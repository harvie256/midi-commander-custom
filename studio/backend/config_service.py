from __future__ import annotations

from dataclasses import dataclass

from .flash_packer import MIDI_NUM_COMMANDS_PER_SWITCH, NUM_BANKS, pack
from .models import BUTTON_IDS, StudioProject


BANK_LARGE_NAME_LIMIT = 4
BANK_SMALL_NAME_LIMIT = 8
CONFIG_NAME_LIMIT = 16
MAX_BANK_SELECT = 16383
MAX_DURATION_MS = 1270
PITCH_BEND_MIN = -8192
PITCH_BEND_MAX = 8191


@dataclass(frozen=True)
class ValidationIssue:
    level: str
    path: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"level": self.level, "path": self.path, "message": self.message}


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

    def ascii_limit(path: str, value: str, limit: int, label: str) -> None:
        length = _ascii_length(value)
        if length is None:
            error(path, f"{label} must use ASCII characters.")
        elif length > limit:
            error(path, f"{label} is limited to {limit} characters.")

    ascii_limit(
        "globalSettings.configName",
        project.globalSettings.configName,
        CONFIG_NAME_LIMIT,
        "Configuration name",
    )

    if len(project.banks) != NUM_BANKS:
        error("banks", f"The firmware requires exactly {NUM_BANKS} banks.")

    for bank_index, bank in enumerate(project.banks):
        base = f"banks.{bank_index}"
        if bank.number != bank_index:
            error(base, f"Expected bank number {bank_index}.")
        ascii_limit(f"{base}.largeName", bank.largeName, BANK_LARGE_NAME_LIMIT, "Large name")
        ascii_limit(f"{base}.smallName", bank.smallName, BANK_SMALL_NAME_LIMIT, "Small line")
        if len(bank.buttons) != len(BUTTON_IDS):
            error(f"{base}.buttons", f"Each bank requires exactly {len(BUTTON_IDS)} buttons.")
            continue

        for button_index, button in enumerate(bank.buttons):
            button_path = f"{base}.buttons.{button_index}"
            if button.id != BUTTON_IDS[button_index]:
                error(button_path, f"Expected button {BUTTON_IDS[button_index]} in this position.")
            if len(button.commands) > MIDI_NUM_COMMANDS_PER_SWITCH:
                error(
                    f"{button_path}.commands",
                    f"A button can contain at most {MIDI_NUM_COMMANDS_PER_SWITCH} commands.",
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
                if command.type == "PC" and not 0 <= command.bankSelect <= MAX_BANK_SELECT:
                    error(f"{command_path}.bankSelect", "Bank select must be between 0 and 16,383.")
                if command.type == "Note" and not 0 <= command.velocity <= 127:
                    error(f"{command_path}.velocity", "Note velocity must be between 0 and 127.")
                if command.type == "PB" and not PITCH_BEND_MIN <= command.onValue <= PITCH_BEND_MAX:
                    error(f"{command_path}.onValue", "Pitch bend must be between -8,192 and 8,191.")
                if command.type in {"Note", "PB"}:
                    if not 0 <= command.durationMs <= MAX_DURATION_MS:
                        error(f"{command_path}.durationMs", "Duration must be between 0 and 1,270 ms.")
                    elif command.durationMs % 10:
                        error(f"{command_path}.durationMs", "Duration must be a multiple of 10 ms.")
                if command.type == "PC" and command.number == 0:
                    warning(f"{command_path}.number", "Program 0 may be displayed as Program 1 by your target device.")

    return [issue.as_dict() for issue in issues]


def pack_project(project: StudioProject) -> bytes:
    errors = [issue for issue in validate_project(project) if issue["level"] == "error"]
    if errors:
        raise ValueError(errors[0]["message"])
    return pack(project)


def project_stats(project: StudioProject) -> dict[str, int]:
    return {
        "contentSize": len(pack_project(project)),
        "commandCount": sum(
            len(button.commands) for bank in project.banks for button in bank.buttons
        ),
    }


__all__ = ["pack_project", "project_stats", "validate_project"]
