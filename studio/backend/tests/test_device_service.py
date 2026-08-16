from __future__ import annotations

import hashlib
import io
import struct
import zipfile
from pathlib import Path

import pytest

from studio.backend import device_service
from studio.backend.jobs import Job


def test_firmware_command_matches_file_and_live_dfu_identities() -> None:
    firmware = device_service.BUNDLED_FIRMWARE_PATH
    command = device_service._firmware_install_command("dfu-util", firmware)

    assert command[:3] == ["dfu-util", "--device", "0483:0000,0483:df11"]
    assert command[3:5] == ["--alt", "0"]
    assert command[-2:] == ["--download", str(firmware)]


def _write_dfu(path: Path, vendor: int, product: int) -> Path:
    body = b"payload"
    suffix = struct.pack("<HHHH", 0, product, vendor, 0x011A) + b"UFD" + bytes([16]) + b"\x00" * 4
    path.write_bytes(body + suffix)
    return path


def test_device_ids_are_read_from_each_files_own_suffix(tmp_path) -> None:
    """A packed build records 0483:df11 where the bundled DfuSe file records
    0483:0000, so the runtime half of --device cannot be a constant."""
    built = _write_dfu(tmp_path / "MIDI_Commander_Custom.dfu", 0x0483, 0xDF11)

    command = device_service._firmware_install_command("dfu-util", built)

    assert command[2] == "0483:df11,0483:df11"


def test_install_command_rejects_a_file_without_a_dfu_suffix(tmp_path) -> None:
    plain = tmp_path / "MIDI_Commander_Custom.bin"
    plain.write_bytes(b"\x00" * 64)

    with pytest.raises(RuntimeError, match="does not carry a DFU suffix"):
        device_service._firmware_install_command("dfu-util", plain)


def test_repository_firmware_files_carry_the_expected_identities() -> None:
    assert device_service._dfu_suffix_ids(device_service.BUNDLED_FIRMWARE_PATH) == (0x0483, 0x0000)


def test_a_local_build_takes_priority_over_the_bundled_firmware(tmp_path, monkeypatch) -> None:
    built = _write_dfu(tmp_path / "MIDI_Commander_Custom.dfu", 0x0483, 0xDF11)
    monkeypatch.setattr(device_service, "BUILT_FIRMWARE_PATH", built)

    assert device_service.resolve_firmware() == (built, "built")
    assert device_service.resolve_firmware("bundled") == (
        device_service.BUNDLED_FIRMWARE_PATH,
        "bundled",
    )


def test_bundled_firmware_is_used_when_nothing_has_been_built(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(device_service, "BUILT_FIRMWARE_PATH", tmp_path / "absent.dfu")

    assert device_service.resolve_firmware() == (
        device_service.BUNDLED_FIRMWARE_PATH,
        "bundled",
    )


def test_unknown_firmware_source_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unknown firmware source"):
        device_service.resolve_firmware("stock")


def test_windows_firmware_status_exposes_driver_guidance(monkeypatch) -> None:
    monkeypatch.setattr(device_service.platform, "system", lambda: "Windows")
    monkeypatch.setattr(device_service, "_dfu_util_path", lambda: None)

    status = device_service.firmware_status()

    assert status["platform"] == "Windows"
    assert status["dependencyInstallSupported"] is True
    assert status["dependencyActionLabel"] == "Download dfu-util"
    assert "WinUSB" in status["driverHint"]
    assert status["driverHelpUrl"] == "https://zadig.akeo.ie/"


def test_windows_dfu_download_is_verified_and_extracted(tmp_path, monkeypatch) -> None:
    archive_buffer = io.BytesIO()
    with zipfile.ZipFile(archive_buffer, "w") as archive:
        archive.writestr("dfu-util-static.exe", b"test executable")
    archive_bytes = archive_buffer.getvalue()

    class Download(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            self.close()

    target_dir = tmp_path / "dfu-util"
    target_path = target_dir / "dfu-util-static.exe"
    monkeypatch.setattr(device_service, "WINDOWS_DFU_DIR", target_dir)
    monkeypatch.setattr(device_service, "WINDOWS_DFU_PATH", target_path)
    monkeypatch.setattr(
        device_service,
        "WINDOWS_DFU_SHA256",
        hashlib.sha256(archive_bytes).hexdigest(),
    )
    monkeypatch.setattr(
        device_service.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: Download(archive_bytes),
    )

    result = device_service._install_windows_dfu(Job(id="test", kind="dependency-install"))

    assert result["installed"] is True
    assert target_path.read_bytes() == b"test executable"


def test_windows_dfu_download_rejects_wrong_checksum(tmp_path, monkeypatch) -> None:
    target_dir = tmp_path / "dfu-util"
    target_path = target_dir / "dfu-util-static.exe"
    monkeypatch.setattr(device_service, "WINDOWS_DFU_DIR", target_dir)
    monkeypatch.setattr(device_service, "WINDOWS_DFU_PATH", target_path)
    monkeypatch.setattr(device_service, "WINDOWS_DFU_SHA256", "0" * 64)
    monkeypatch.setattr(
        device_service.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: io.BytesIO(b"not the pinned archive"),
    )

    with pytest.raises(RuntimeError, match="SHA-256"):
        device_service._install_windows_dfu(Job(id="test", kind="dependency-install"))

    assert not target_path.exists()
