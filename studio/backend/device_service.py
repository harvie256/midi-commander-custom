from __future__ import annotations

import hashlib
import platform
import shutil
import subprocess
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

import mido

from .config_service import pack_project
from .jobs import Job
from .models import MidiCommand, StudioProject


MIDI_MANUFACTURER_ID = 0x7D
ERASE_FLASH = 52
ERASE_RESPONSE = 53
WRITE_FLASH = 54
WRITE_RESPONSE = 55
RESET = 60
REPO_ROOT = Path(__file__).resolve().parents[2]
FIRMWARE_PATH = REPO_ROOT / "DFU" / "DFU_OUT" / "generated-20220424-163714.dfu"
STUDIO_TOOLS = REPO_ROOT / ".studio-tools"
WINDOWS_DFU_DIR = STUDIO_TOOLS / "dfu-util"
WINDOWS_DFU_PATH = WINDOWS_DFU_DIR / "dfu-util-static.exe"
WINDOWS_DFU_URL = (
    "https://dfu-util.sourceforge.net/snapshots/dfu-util_SNAPSHOT_20240416-win64.zip"
)
WINDOWS_DFU_SHA256 = "683e78f661ff524186a64ab17d99fc6c3e9637811643ceecae37b791de89a901"
WINDOWS_DRIVER_HELP_URL = "https://zadig.akeo.ie/"


def scan_midi_devices() -> dict[str, Any]:
    inputs = list(mido.get_input_names())
    outputs = list(mido.get_output_names())
    compatible_inputs = [name for name in inputs if "STM" in name.upper()]
    compatible_outputs = [name for name in outputs if "STM" in name.upper()]
    return {
        "inputs": inputs,
        "outputs": outputs,
        "compatibleInputs": compatible_inputs,
        "compatibleOutputs": compatible_outputs,
        "connected": bool(compatible_inputs and compatible_outputs),
    }


def _receive_sysex(port: Any, expected_command: int, timeout: float = 3.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        message = port.receive(block=False)
        if message is None:
            time.sleep(0.01)
            continue
        if message.type == "sysex" and len(message.data) >= 2:
            if message.data[0] == MIDI_MANUFACTURER_ID and message.data[1] == expected_command:
                return
    raise TimeoutError(
        "The pedal did not acknowledge the request. Confirm that the custom firmware is running in normal mode."
    )


def upload_configuration(
    project: StudioProject,
    input_name: str,
    output_name: str,
    job: Job,
) -> dict[str, Any]:
    flash_contents = pack_project(project)
    if len(flash_contents) != 2688:
        raise ValueError(f"Unexpected configuration size: {len(flash_contents)} bytes.")

    job.log(f"Opening MIDI input: {input_name}")
    input_port = mido.open_input(input_name)
    output_port = mido.open_output(output_name)
    try:
        job.log("Erasing configuration flash…")
        output_port.send(
            mido.Message("sysex", data=[MIDI_MANUFACTURER_ID, ERASE_FLASH, 0x42, 0x24])
        )
        _receive_sysex(input_port, ERASE_RESPONSE, timeout=5.0)
        job.log("Erase complete.")

        chunks = [flash_contents[index : index + 16] for index in range(0, len(flash_contents), 16)]
        for index, chunk in enumerate(chunks):
            chunk_low = index & 0x7F
            chunk_high = (index >> 7) & 0x7F
            data = [MIDI_MANUFACTURER_ID, WRITE_FLASH, chunk_high, chunk_low]
            for value in chunk:
                data.extend((value >> 4, value & 0x0F))
            output_port.send(mido.Message("sysex", data=data))
            _receive_sysex(input_port, WRITE_RESPONSE)
            job.progress = round(((index + 1) / len(chunks)) * 96, 1)
            if index == 0 or (index + 1) % 16 == 0 or index + 1 == len(chunks):
                job.log(f"Written {index + 1} of {len(chunks)} chunks.")

        job.log("Resetting the pedal…")
        output_port.send(mido.Message("sysex", data=[MIDI_MANUFACTURER_ID, RESET]))
        job.log("Configuration uploaded successfully.")
        return {"bytesWritten": len(flash_contents), "chunksWritten": len(chunks)}
    finally:
        input_port.close()
        output_port.close()


def test_command(output_name: str, command: MidiCommand) -> None:
    channel = max(0, min(15, command.channel - 1))
    messages: list[mido.Message] = []
    if command.type == "CC":
        messages.append(
            mido.Message("control_change", channel=channel, control=command.number, value=command.onValue)
        )
    elif command.type == "PC":
        if command.bankSelectHighByte:
            messages.append(
                mido.Message(
                    "control_change", channel=channel, control=0, value=(command.bankSelect >> 7) & 0x7F
                )
            )
        messages.append(
            mido.Message(
                "control_change", channel=channel, control=32, value=command.bankSelect & 0x7F
            )
        )
        messages.append(mido.Message("program_change", channel=channel, program=command.number))
    elif command.type == "Note":
        messages.append(
            mido.Message("note_on", channel=channel, note=command.number, velocity=command.velocity)
        )
    elif command.type == "PB":
        messages.append(mido.Message("pitchwheel", channel=channel, pitch=command.onValue))
    elif command.type == "Start":
        messages.append(mido.Message("start"))
    elif command.type == "Stop":
        messages.append(mido.Message("stop"))

    with mido.open_output(output_name) as output_port:
        for message in messages:
            output_port.send(message)
        if command.type == "Note":
            time.sleep(max(command.durationMs, 150) / 1000)
            output_port.send(mido.Message("note_off", channel=channel, note=command.number, velocity=0))
        elif command.type == "PB":
            time.sleep(max(command.durationMs, 150) / 1000)
            output_port.send(mido.Message("pitchwheel", channel=channel, pitch=0))


def _dfu_util_path() -> str | None:
    discovered = shutil.which("dfu-util") or shutil.which("dfu-util.exe")
    if discovered:
        return discovered
    current = platform.system()
    if current == "Windows" and WINDOWS_DFU_PATH.exists():
        return str(WINDOWS_DFU_PATH)
    homebrew_path = Path("/opt/homebrew/bin/dfu-util")
    return str(homebrew_path) if current == "Darwin" and homebrew_path.exists() else None


def _platform_name() -> str:
    return {"Darwin": "macOS", "Windows": "Windows", "Linux": "Linux"}.get(
        platform.system(), platform.system() or "Unknown"
    )


def _dependency_action() -> tuple[bool, str]:
    current = platform.system()
    if current == "Windows":
        return True, "Download dfu-util"
    if current == "Darwin":
        return True, "Install dfu-util"
    return False, "Install dfu-util manually"


def _subprocess_options() -> dict[str, int]:
    if platform.system() == "Windows":
        return {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)}
    return {}


def firmware_status() -> dict[str, Any]:
    executable = _dfu_util_path()
    install_supported, action_label = _dependency_action()
    current_platform = _platform_name()
    common = {
        "platform": current_platform,
        "dependencyInstallSupported": install_supported,
        "dependencyActionLabel": action_label,
        "driverHelpUrl": WINDOWS_DRIVER_HELP_URL if current_platform == "Windows" else None,
        "driverHint": (
            "If the pedal is not detected in DFU mode, install the WinUSB driver for "
            "STM32 BOOTLOADER (0483:df11) with Zadig, then check again."
            if current_platform == "Windows"
            else None
        ),
    }
    if executable is None:
        return {
            **common,
            "installed": False,
            "deviceDetected": False,
            "internalFlashDetected": False,
            "firmwareFile": FIRMWARE_PATH.name,
            "firmwareExists": FIRMWARE_PATH.exists(),
            "detail": "dfu-util is not installed.",
        }
    tool_error: str | None = None
    try:
        result = subprocess.run(
            [executable, "--list"],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
            **_subprocess_options(),
        )
        output = f"{result.stdout}\n{result.stderr}"
    except subprocess.TimeoutExpired:
        output = "dfu-util timed out while scanning."
        tool_error = output
    except OSError as exc:
        output = ""
        tool_error = f"dfu-util could not run: {exc}"
    detected = "0483:df11" in output.lower()
    internal = detected and "alt=0" in output.lower() and "internal flash" in output.lower()
    detail = tool_error or (
        "Internal flash target detected." if internal else "No compatible DFU target detected."
    )
    return {
        **common,
        "installed": True,
        "deviceDetected": detected,
        "internalFlashDetected": internal,
        "firmwareFile": FIRMWARE_PATH.name,
        "firmwareExists": FIRMWARE_PATH.exists(),
        "detail": detail,
    }


def _install_windows_dfu(job: Job) -> dict[str, Any]:
    WINDOWS_DFU_DIR.mkdir(parents=True, exist_ok=True)
    job.log("Downloading the pinned dfu-util Windows build from SourceForge…")
    request = urllib.request.Request(
        WINDOWS_DFU_URL,
        headers={"User-Agent": "MIDI-Commander-Studio/1.0"},
    )
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temporary:
            temporary_path = Path(temporary.name)
            with urllib.request.urlopen(request, timeout=45) as response:
                shutil.copyfileobj(response, temporary)
        assert temporary_path is not None
        digest = hashlib.sha256(temporary_path.read_bytes()).hexdigest()
        if digest != WINDOWS_DFU_SHA256:
            raise RuntimeError(
                "The dfu-util download did not match the pinned SHA-256 checksum; nothing was installed."
            )
        job.log("Download verified. Extracting dfu-util-static.exe…")
        with zipfile.ZipFile(temporary_path) as archive:
            try:
                executable = archive.open("dfu-util-static.exe")
            except KeyError as exc:
                raise RuntimeError("The official archive did not contain dfu-util-static.exe.") from exc
            with executable, WINDOWS_DFU_PATH.open("wb") as destination:
                shutil.copyfileobj(executable, destination)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    job.log("dfu-util is ready. Windows may still require the WinUSB device driver.")
    return {"installed": True, "path": str(WINDOWS_DFU_PATH)}


def install_dfu_util(job: Job) -> dict[str, Any]:
    if _dfu_util_path():
        job.log("dfu-util is already installed.")
        return {"installed": True}
    if platform.system() == "Windows":
        return _install_windows_dfu(job)
    if platform.system() != "Darwin":
        raise RuntimeError("Automatic dfu-util installation is available on macOS and Windows only.")
    brew = shutil.which("brew") or (
        "/opt/homebrew/bin/brew" if Path("/opt/homebrew/bin/brew").exists() else None
    )
    if brew is None:
        raise RuntimeError("Homebrew was not found. Install Homebrew, then try again.")
    job.log("Installing dfu-util with Homebrew…")
    process = subprocess.Popen(
        [brew, "install", "dfu-util"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        **_subprocess_options(),
    )
    assert process.stdout is not None
    for line in process.stdout:
        text = line.strip()
        if text:
            job.log(text)
    return_code = process.wait()
    if return_code:
        raise RuntimeError(f"Homebrew exited with status {return_code}.")
    job.log("dfu-util installed successfully.")
    return {"installed": True}


def _firmware_install_command(executable: str) -> list[str]:
    # The bundled DfuSe file records 0483:0000 in its suffix while the STM32
    # bootloader enumerates as 0483:df11. dfu-util accepts separate runtime
    # and DFU-mode identities, preserving an exact match for the live target
    # without bypassing suffix validation with a force option.
    return [
        executable,
        "--device",
        "0483:0000,0483:df11",
        "--alt",
        "0",
        "--download",
        str(FIRMWARE_PATH),
    ]


def install_firmware(job: Job) -> dict[str, Any]:
    status = firmware_status()
    if not status["installed"]:
        raise RuntimeError("Install dfu-util first.")
    if not status["internalFlashDetected"]:
        raise RuntimeError("The expected alt 0 Internal Flash DFU target is not connected.")
    if not FIRMWARE_PATH.exists():
        raise RuntimeError("The bundled firmware file is missing.")
    executable = _dfu_util_path()
    assert executable is not None
    job.log(f"Installing {FIRMWARE_PATH.name} to alt 0 Internal Flash…")
    process = subprocess.Popen(
        _firmware_install_command(executable),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        **_subprocess_options(),
    )
    assert process.stdout is not None
    for line in process.stdout:
        text = line.strip()
        if text:
            job.log(text)
    return_code = process.wait()
    if return_code:
        raise RuntimeError(f"dfu-util exited with status {return_code}.")
    job.log("Firmware installed. Power-cycle the pedal normally, then upload a configuration.")
    return {"firmware": FIRMWARE_PATH.name}
