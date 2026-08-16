"""Encodes a StudioProject into the firmware's configuration flash image.

This is the host side of the wire contract decoded by
`MIDI_Commander_Custom/Core/Src/midi_cmds.c`. Nothing validates the two against
each other at build time, so the constants below are mirrored by hand from the
firmware headers named beside them, and
`tests/test_flash_packer.py::test_layout_matches_firmware_header` greps the C
for the ones that can be checked mechanically.

Encoding conventions, all fixed by the firmware:

* byte 0 is the command-type nibble OR'd with the zero-based MIDI channel
* the toggle flag is the top bit of byte 1 (CC, Note and PB only)
* a byte above 0x7F means "no value" — it suppresses the CC off-value
  (`midi_cmds.c` returns early when `pRom[3] > 0x7F`) and the program-change
  bank-select bytes (`pRom[2]`/`pRom[3] < 0x80`)
* note and pitch-bend durations are byte 3 in 10 ms units (`pRom[3] * 10`)
"""

from __future__ import annotations

from typing import Callable

from .models import BUTTON_IDS, Bank, GlobalSettings, MidiCommand, StudioProject


# Core/Inc/midi_defines.h
CMD_NO_CMD_NIBBLE = 0x00
CMD_PC_NIBBLE = 0xC0
CMD_CC_NIBBLE = 0xB0
CMD_PB_NIBBLE = 0xE0
CMD_NOTE_NIBBLE = 0x90
CMD_START_NIBBLE = 0x10
CMD_STOP_NIBBLE = 0x20
GLOBAL_SETTINGS_CHANNEL = 0
GLOBAL_SETTINGS_REALTIME_PASS = 1

# Core/Inc/flash_midi_settings.h
MIDI_ROM_CMD_SIZE = 4
MIDI_NUM_COMMANDS_PER_SWITCH = 10

# Core/Src/flash_midi_settings.c — pGlobalSettings +0, pBankStrings +32,
# pSwitchCmds +32+96.
GLOBAL_SETTINGS_SIZE = 32
GLOBAL_SETTINGS_FLAGS_SIZE = 16
CONFIG_NAME_SIZE = 16
BANK_LARGE_NAME_SIZE = 4
BANK_SMALL_NAME_SIZE = 8
BANK_STRING_SIZE = BANK_LARGE_NAME_SIZE + BANK_SMALL_NAME_SIZE
NUM_BANKS = 8

NO_VALUE = 0x80
TOGGLE_BIT = 0x80
PITCH_BEND_CENTRE = 0x2000
DURATION_UNIT_MS = 10

FLASH_CONTENT_SIZE = (
    GLOBAL_SETTINGS_SIZE
    + NUM_BANKS * BANK_STRING_SIZE
    + NUM_BANKS * len(BUTTON_IDS) * MIDI_NUM_COMMANDS_PER_SWITCH * MIDI_ROM_CMD_SIZE
)


def _ascii_field(value: str, length: int) -> bytes:
    """Fixed-width ASCII, space padded and truncated — what the OLED expects."""
    return f"{value:{length}.{length}}".encode("ascii")


def _channel(command: MidiCommand) -> int:
    return (command.channel - 1) & 0x0F


def _toggle(command: MidiCommand) -> int:
    return TOGGLE_BIT if command.toggle else 0


def _duration(command: MidiCommand) -> int:
    return (command.durationMs // DURATION_UNIT_MS) & 0x7F


def _pack_pc(command: MidiCommand) -> bytes:
    # The low bank-select byte is always sent; the high byte is suppressed
    # unless the project asks for it.
    high = (command.bankSelect >> 7) & 0x7F if command.bankSelectHighByte else NO_VALUE
    return bytes(
        (
            CMD_PC_NIBBLE | _channel(command),
            command.number & 0x7F,
            high,
            command.bankSelect & 0x7F,
        )
    )


def _pack_cc(command: MidiCommand) -> bytes:
    off = NO_VALUE if command.suppressOff else command.offValue & 0x7F
    return bytes(
        (
            CMD_CC_NIBBLE | _channel(command),
            (command.number & 0x7F) | _toggle(command),
            command.onValue & 0x7F,
            off,
        )
    )


def _pack_note(command: MidiCommand) -> bytes:
    return bytes(
        (
            CMD_NOTE_NIBBLE | _channel(command),
            (command.number & 0x7F) | _toggle(command),
            command.velocity & 0x7F,
            _duration(command),
        )
    )


def _pack_pb(command: MidiCommand) -> bytes:
    # The model carries a signed bend; the wire carries it centred on 0x2000.
    pitch = command.onValue + PITCH_BEND_CENTRE
    return bytes(
        (
            CMD_PB_NIBBLE | _channel(command),
            (pitch & 0x7F) | _toggle(command),
            (pitch >> 7) & 0x7F,
            _duration(command),
        )
    )


def _pack_start(command: MidiCommand) -> bytes:
    return bytes((CMD_START_NIBBLE, 0, 0, 0))


def _pack_stop(command: MidiCommand) -> bytes:
    return bytes((CMD_STOP_NIBBLE, 0, 0, 0))


_COMMAND_PACKERS: dict[str, Callable[[MidiCommand], bytes]] = {
    "PC": _pack_pc,
    "CC": _pack_cc,
    "Note": _pack_note,
    "PB": _pack_pb,
    "Start": _pack_start,
    "Stop": _pack_stop,
}

EMPTY_COMMAND = bytes(MIDI_ROM_CMD_SIZE)


def pack_global_settings(settings: GlobalSettings) -> bytes:
    flags = bytearray(GLOBAL_SETTINGS_FLAGS_SIZE)
    flags[GLOBAL_SETTINGS_CHANNEL] = settings.midiChannel & 0x0F
    flags[GLOBAL_SETTINGS_REALTIME_PASS] = 1 if settings.realtimePassthrough else 0
    return bytes(flags) + _ascii_field(settings.configName, CONFIG_NAME_SIZE)


def pack_bank_strings(banks: list[Bank]) -> bytes:
    packed = bytearray()
    for bank in banks:
        packed += _ascii_field(bank.largeName, BANK_LARGE_NAME_SIZE)
        packed += _ascii_field(bank.smallName, BANK_SMALL_NAME_SIZE)
    return bytes(packed)


def pack_switch_commands(banks: list[Bank]) -> bytes:
    packed = bytearray()
    for bank in banks:
        for button in bank.buttons:
            for index in range(MIDI_NUM_COMMANDS_PER_SWITCH):
                if index >= len(button.commands):
                    packed += EMPTY_COMMAND
                    continue
                command = button.commands[index]
                packer = _COMMAND_PACKERS.get(command.type)
                packed += EMPTY_COMMAND if packer is None else packer(command)
    return bytes(packed)


def pack(project: StudioProject) -> bytes:
    """Encode a project. Assumes it has already passed validate_project()."""
    packed = (
        pack_global_settings(project.globalSettings)
        + pack_bank_strings(project.banks)
        + pack_switch_commands(project.banks)
    )
    if len(packed) != FLASH_CONTENT_SIZE:
        raise ValueError(
            f"Packed {len(packed)} bytes but the firmware flash layout expects "
            f"{FLASH_CONTENT_SIZE}."
        )
    return packed
