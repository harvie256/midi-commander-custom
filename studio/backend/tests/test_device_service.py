from __future__ import annotations

import hashlib
import io
import zipfile

import pytest

from studio.backend import device_service
from studio.backend.jobs import Job


def test_firmware_command_matches_file_and_live_dfu_identities() -> None:
    command = device_service._firmware_install_command("dfu-util")

    assert command[:3] == ["dfu-util", "--device", "0483:0000,0483:df11"]
    assert command[3:5] == ["--alt", "0"]
    assert command[-2:] == ["--download", str(device_service.FIRMWARE_PATH)]


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
