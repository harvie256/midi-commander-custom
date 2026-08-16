from __future__ import annotations

import csv
import io
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from .models import (
    BUTTON_IDS,
    Bank,
    GlobalSettings,
    MidiCommand,
    PedalButton,
    StudioProject,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PYTHON_ROOT = REPO_ROOT / "python"
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from lib import cmdBinaryPacker as command_packer  # noqa: E402
from lib import settingsBinaryPacker as settings_packer  # noqa: E402


# Mirrors the flash layout fixed by MIDI_Commander_Custom/Core/Src/flash_midi_settings.c:
#   pGlobalSettings  +0                            GLOBAL_SETTINGS_SIZE
#   pBankStrings     +32    NUM_BANKS            * BANK_STRING_SIZE
#   pSwitchCmds      +128   NUM_BANKS * buttons  * commands * MIDI_ROM_CMD_SIZE
# The command count comes from the shared packer rather than being restated here,
# and test_flash_layout_matches_firmware_header checks the rest against the C header.
GLOBAL_SETTINGS_SIZE = 32
BANK_STRING_SIZE = 12
NUM_BANKS = 8
MIDI_ROM_CMD_SIZE = 4
FLASH_CONTENT_SIZE = (
    GLOBAL_SETTINGS_SIZE
    + NUM_BANKS * BANK_STRING_SIZE
    + NUM_BANKS
    * len(BUTTON_IDS)
    * command_packer.MIDI_NUM_COMMANDS_PER_SWITCH
    * MIDI_ROM_CMD_SIZE
)

COMMAND_LETTERS = tuple("ABCDEFGHIJ")
COMMAND_FIELDS = (
    "CommandType",
    "Channel_(PC/CC/Note/PB)",
    "Number_(PC/CC/Note)",
    "OnValue_(CC/PB)",
    "OffValue_(CC)",
    "BankSelect_(PC)",
    "BankSelectHighByte_(PC)",
    "Toggle_(CC/PB/Note)",
    "Velocity_(Note)",
    "Duration_(Note/PB)",
)


@dataclass(frozen=True)
class ValidationIssue:
    level: str
    path: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"level": self.level, "path": self.path, "message": self.message}


def _integer(value: Any, default: int = 0) -> int:
    if value is None or value == "":
        return default
    if isinstance(value, float) and math.isnan(value):
        return default
    return int(float(value))


def _yes(value: Any) -> bool:
    return str(value).strip().upper().startswith("Y")


def _ascii_length(value: str) -> int | None:
    try:
        return len(value.encode("ascii"))
    except UnicodeEncodeError:
        return None


def validate_project(project: StudioProject) -> list[dict[str, str]]:
    issues: list[ValidationIssue] = []

    def error(path: str, message: str) -> None:
        issues.append(ValidationIssue("error", path, message))

    def warning(path: str, message: str) -> None:
        issues.append(ValidationIssue("warning", path, message))

    config_name_length = _ascii_length(project.globalSettings.configName)
    if config_name_length is None:
        error("globalSettings.configName", "Configuration name must use ASCII characters.")
    elif config_name_length > 16:
        error("globalSettings.configName", "Configuration name is limited to 16 characters.")

    if len(project.banks) != NUM_BANKS:
        error("banks", f"The firmware requires exactly {NUM_BANKS} banks.")

    for bank_index, bank in enumerate(project.banks):
        base = f"banks.{bank_index}"
        if bank.number != bank_index:
            error(base, f"Expected bank number {bank_index}.")
        large_length = _ascii_length(bank.largeName)
        small_length = _ascii_length(bank.smallName)
        if large_length is None:
            error(f"{base}.largeName", "Large name must use ASCII characters.")
        elif large_length > 4:
            error(f"{base}.largeName", "Large name is limited to 4 characters.")
        if small_length is None:
            error(f"{base}.smallName", "Small line must use ASCII characters.")
        elif small_length > 8:
            error(f"{base}.smallName", "Small line is limited to 8 characters.")
        if len(bank.buttons) != len(BUTTON_IDS):
            error(f"{base}.buttons", f"Each bank requires exactly {len(BUTTON_IDS)} buttons.")
            continue

        for button_index, button in enumerate(bank.buttons):
            button_path = f"{base}.buttons.{button_index}"
            if button.id != BUTTON_IDS[button_index]:
                error(button_path, f"Expected button {BUTTON_IDS[button_index]} in this position.")
            if len(button.commands) > command_packer.MIDI_NUM_COMMANDS_PER_SWITCH:
                error(
                    f"{button_path}.commands",
                    f"A button can contain at most {command_packer.MIDI_NUM_COMMANDS_PER_SWITCH} commands.",
                )
            for command_index, command in enumerate(button.commands):
                command_path = f"{button_path}.commands.{command_index}"
                if command.type not in {"Start", "Stop"} and not 1 <= command.channel <= 16:
                    error(f"{command_path}.channel", "MIDI channel must be between 1 and 16.")
                if command.type in {"PC", "CC", "Note"} and not 0 <= command.number <= 127:
                    error(f"{command_path}.number", "MIDI number must be between 0 and 127.")
                if command.type == "CC":
                    if not 0 <= command.onValue <= 127:
                        error(f"{command_path}.onValue", "CC on value must be between 0 and 127.")
                    if not command.suppressOff and not 0 <= command.offValue <= 127:
                        error(f"{command_path}.offValue", "CC off value must be between 0 and 127.")
                if command.type == "PC" and not 0 <= command.bankSelect <= 16383:
                    error(f"{command_path}.bankSelect", "Bank select must be between 0 and 16,383.")
                if command.type == "Note" and not 0 <= command.velocity <= 127:
                    error(f"{command_path}.velocity", "Note velocity must be between 0 and 127.")
                if command.type == "PB" and not -8192 <= command.onValue <= 8191:
                    error(f"{command_path}.onValue", "Pitch bend must be between -8,192 and 8,191.")
                if command.type in {"Note", "PB"}:
                    if not 0 <= command.durationMs <= 1270:
                        error(f"{command_path}.durationMs", "Duration must be between 0 and 1,270 ms.")
                    elif command.durationMs % 10:
                        error(f"{command_path}.durationMs", "Duration must be a multiple of 10 ms.")
                if command.type == "PC" and command.number == 0:
                    warning(f"{command_path}.number", "Program 0 may be displayed as Program 1 by your target device.")

    return [issue.as_dict() for issue in issues]


def project_stats(project: StudioProject) -> dict[str, int]:
    return {
        "contentSize": len(pack_project(project)),
        "commandCount": sum(
            len(button.commands) for bank in project.banks for button in bank.buttons
        ),
    }


def _command_row(command: MidiCommand) -> dict[str, Any]:
    return {
        "CommandType": command.type,
        "Channel_(PC/CC/Note/PB)": command.channel,
        "Number_(PC/CC/Note)": command.number,
        "OnValue_(CC/PB)": command.onValue,
        "OffValue_(CC)": 255 if command.suppressOff else command.offValue,
        "BankSelect_(PC)": command.bankSelect,
        "BankSelectHighByte_(PC)": "Y" if command.bankSelectHighByte else "N",
        "Toggle_(CC/PB/Note)": "Y" if command.toggle else "N",
        "Velocity_(Note)": command.velocity,
        "Duration_(Note/PB)": command.durationMs // 10,
    }


def project_to_frames(project: StudioProject) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    global_frame = pd.DataFrame(
        {
            "Value": {
                "MIDI_Channel": project.globalSettings.midiChannel,
                "RealTime_Passthrough": "Y" if project.globalSettings.realtimePassthrough else "N",
                "ConfigName": project.globalSettings.configName,
            }
        }
    )
    bank_frame = pd.DataFrame(
        [
            {
                "Bank_Number": bank.number,
                "Bank_Name_Large": bank.largeName,
                "Bank_Info_Small": bank.smallName,
            }
            for bank in project.banks
        ]
    ).set_index("Bank_Number")

    button_rows: list[dict[str, Any]] = []
    for bank in project.banks:
        for button in bank.buttons:
            row: dict[str, Any] = {
                "Bank_Number": bank.number,
                "Button_Identifier": button.id,
            }
            for command_index, letter in enumerate(COMMAND_LETTERS):
                values = (
                    _command_row(button.commands[command_index])
                    if command_index < len(button.commands)
                    else {field: "" for field in COMMAND_FIELDS}
                )
                row.update({f"{letter}_{key}": value for key, value in values.items()})
            button_rows.append(row)
    button_frame = pd.DataFrame(button_rows).set_index(["Bank_Number", "Button_Identifier"])
    return global_frame, bank_frame, button_frame


def pack_project(project: StudioProject) -> bytes:
    errors = [issue for issue in validate_project(project) if issue["level"] == "error"]
    if errors:
        raise ValueError(errors[0]["message"])
    global_frame, bank_frame, button_frame = project_to_frames(project)
    packed: list[int] = []
    packed.extend(settings_packer.pack_global_settings(global_frame))
    packed.extend(settings_packer.pack_bank_strings(bank_frame))
    for _, row in button_frame.iterrows():
        packed.extend(command_packer.pack_row(row.copy()))
    if len(packed) != FLASH_CONTENT_SIZE:
        raise ValueError(
            f"Packed {len(packed)} bytes but the firmware flash layout expects "
            f"{FLASH_CONTENT_SIZE}."
        )
    return bytes(packed)


def project_to_csv(project: StudioProject) -> str:
    global_frame, bank_frame, button_frame = project_to_frames(project)
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["# Generated by MIDI Commander Studio"])
    writer.writerow(["* Global_Settings"])
    writer.writerow(["Label", "Value"])
    for label in ("MIDI_Channel", "RealTime_Passthrough", "ConfigName"):
        writer.writerow([label, global_frame.loc[label, "Value"]])
    writer.writerow([])
    writer.writerow(["* Bank_Naming"])
    writer.writerow(["Bank_Number", "Bank_Name_Large", "Bank_Info_Small"])
    for index, row in bank_frame.iterrows():
        writer.writerow([index, row["Bank_Name_Large"], row["Bank_Info_Small"]])
    writer.writerow([])
    writer.writerow(["* Button_Settings"])
    headers = ["Bank_Number", "Button_Identifier"] + [
        f"{letter}_{field}" for letter in COMMAND_LETTERS for field in COMMAND_FIELDS
    ]
    writer.writerow(headers)
    for (bank_number, button_id), row in button_frame.iterrows():
        writer.writerow([bank_number, button_id] + [row.get(header, "") for header in headers[2:]])
    return output.getvalue()


def _read_sections(csv_text: str) -> dict[str, list[list[str]]]:
    rows = list(csv.reader(io.StringIO(csv_text)))
    sections: dict[str, list[list[str]]] = {}
    current: str | None = None
    for row in rows:
        first = row[0].strip() if row else ""
        if first.startswith("#"):
            continue
        if first.startswith("*"):
            current = first.lstrip("* ").strip()
            sections[current] = []
            continue
        if current is not None and any(cell.strip() for cell in row):
            sections[current].append(row)
    return sections


def _table(rows: list[list[str]]) -> list[dict[str, str]]:
    if not rows:
        return []
    headers = [header.strip() for header in rows[0]]
    result: list[dict[str, str]] = []
    for row in rows[1:]:
        padded = row + [""] * max(0, len(headers) - len(row))
        result.append({header: padded[index].strip() for index, header in enumerate(headers) if header})
    return result


def _command_label(command: MidiCommand) -> str:
    return {
        "PC": f"Program {command.number}",
        "CC": f"CC {command.number}",
        "Note": f"Note {command.number}",
        "PB": "Pitch bend",
        "Start": "Start",
        "Stop": "Stop",
    }[command.type]


def project_from_csv(csv_text: str, source_name: str = "Imported configuration") -> StudioProject:
    sections = _read_sections(csv_text)
    required = {"Global_Settings", "Bank_Naming", "Button_Settings"}
    missing = required.difference(sections)
    if missing:
        raise ValueError(f"CSV is missing section(s): {', '.join(sorted(missing))}")

    global_values = {row.get("Label", ""): row.get("Value", "") for row in _table(sections["Global_Settings"])}
    global_settings = GlobalSettings(
        configName=global_values.get("ConfigName", "Imported") or "Imported",
        realtimePassthrough=_yes(global_values.get("RealTime_Passthrough", "N")),
        midiChannel=_integer(global_values.get("MIDI_Channel"), 1),
    )

    banks: list[Bank] = [
        Bank(
            number=index,
            largeName=f"BN {index + 1}",
            smallName=f"Bank {index + 1}",
            buttons=[PedalButton(id=button_id, label=f"Switch {button_id}") for button_id in BUTTON_IDS],
        )
        for index in range(8)
    ]
    for row in _table(sections["Bank_Naming"]):
        bank_number = _integer(row.get("Bank_Number"), -1)
        if 0 <= bank_number < 8:
            banks[bank_number].largeName = row.get("Bank_Name_Large", "")
            banks[bank_number].smallName = row.get("Bank_Info_Small", "")

    for row in _table(sections["Button_Settings"]):
        bank_number = _integer(row.get("Bank_Number"), -1)
        button_id = row.get("Button_Identifier", "")
        if not 0 <= bank_number < 8 or button_id not in BUTTON_IDS:
            continue
        button = banks[bank_number].buttons[BUTTON_IDS.index(button_id)]
        commands: list[MidiCommand] = []
        for letter in COMMAND_LETTERS:
            command_type = row.get(f"{letter}_CommandType", "")
            if command_type not in {"PC", "CC", "Note", "PB", "Start", "Stop"}:
                continue
            commands.append(
                MidiCommand(
                    type=command_type,
                    channel=_integer(row.get(f"{letter}_Channel_(PC/CC/Note/PB)"), 1),
                    number=_integer(row.get(f"{letter}_Number_(PC/CC/Note)"), 0),
                    onValue=_integer(row.get(f"{letter}_OnValue_(CC/PB)"), 127),
                    offValue=min(_integer(row.get(f"{letter}_OffValue_(CC)"), 0), 127),
                    suppressOff=_integer(row.get(f"{letter}_OffValue_(CC)"), 0) > 127,
                    bankSelect=_integer(row.get(f"{letter}_BankSelect_(PC)"), 0),
                    bankSelectHighByte=_yes(row.get(f"{letter}_BankSelectHighByte_(PC)", "N")),
                    toggle=_yes(row.get(f"{letter}_Toggle_(CC/PB/Note)", "N")),
                    velocity=_integer(row.get(f"{letter}_Velocity_(Note)"), 100),
                    durationMs=_integer(row.get(f"{letter}_Duration_(Note/PB)"), 0) * 10,
                )
            )
        button.commands = commands
        if commands:
            button.label = _command_label(commands[0])

    project_name = Path(source_name).stem.replace("_", " ").strip() or "Imported configuration"
    project = StudioProject(name=project_name, globalSettings=global_settings, banks=banks)
    errors = [issue for issue in validate_project(project) if issue["level"] == "error"]
    if errors:
        raise ValueError(errors[0]["message"])
    return project
