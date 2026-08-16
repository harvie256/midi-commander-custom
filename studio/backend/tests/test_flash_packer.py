from __future__ import annotations

import json
import re
from pathlib import Path

from studio.backend import flash_packer
from studio.backend.models import MidiCommand, StudioProject, starter_project


REPO_ROOT = Path(__file__).resolve().parents[3]
FIRMWARE_HEADER = REPO_ROOT / "MIDI_Commander_Custom" / "Core" / "Inc" / "flash_midi_settings.h"
FIRMWARE_SOURCE = REPO_ROOT / "MIDI_Commander_Custom" / "Core" / "Src" / "flash_midi_settings.c"
MIDI_DEFINES = REPO_ROOT / "MIDI_Commander_Custom" / "Core" / "Inc" / "midi_defines.h"
REFERENCE = Path(__file__).parent / "fixtures" / "rc600_reference.json"


def _define(text: str, name: str) -> int:
    match = re.search(rf"^#define\s+{name}\s+\(?(0[xX][0-9a-fA-F]+|\d+)\)?", text, re.MULTILINE)
    assert match, f"{name} not found in the firmware source"
    return int(match.group(1), 0)


def test_layout_matches_firmware_header() -> None:
    """The wire contract is mirrored by hand, so pin it against the C it mirrors."""
    header = FIRMWARE_HEADER.read_text()
    assert flash_packer.MIDI_ROM_CMD_SIZE == _define(header, "MIDI_ROM_CMD_SIZE")
    assert flash_packer.MIDI_NUM_COMMANDS_PER_SWITCH == _define(
        header, "MIDI_NUM_COMMANDS_PER_SWITCH"
    )

    # pSwitchCmds sits at FLASH_SETTINGS_START+32+96, directly after the global
    # settings block and the bank strings.
    source = FIRMWARE_SOURCE.read_text().replace(" ", "")
    assert "FLASH_SETTINGS_START+32+96" in source
    assert flash_packer.GLOBAL_SETTINGS_SIZE == 32
    assert flash_packer.NUM_BANKS * flash_packer.BANK_STRING_SIZE == 96

    # The packed image must fit the region the firmware erases.
    pages = _define(FIRMWARE_SOURCE.read_text(), "FLASH_SETTINGS_NO_PAGES")
    assert flash_packer.FLASH_CONTENT_SIZE <= pages * 1024


def test_command_nibbles_match_firmware_defines() -> None:
    defines = MIDI_DEFINES.read_text()
    for name in (
        "CMD_NO_CMD_NIBBLE",
        "CMD_PC_NIBBLE",
        "CMD_CC_NIBBLE",
        "CMD_PB_NIBBLE",
        "CMD_NOTE_NIBBLE",
        "CMD_START_NIBBLE",
        "CMD_STOP_NIBBLE",
        "GLOBAL_SETTINGS_CHANNEL",
        "GLOBAL_SETTINGS_REALTIME_PASS",
    ):
        assert getattr(flash_packer, name) == _define(defines, name), name


def test_flash_content_size_is_the_expected_layout() -> None:
    assert flash_packer.FLASH_CONTENT_SIZE == 2688


def test_reference_configuration_packs_to_known_bytes() -> None:
    """Golden image captured from the pandas/CSV implementation this replaced."""
    reference = json.loads(REFERENCE.read_text())
    project = StudioProject.model_validate(reference["project"])
    assert flash_packer.pack(project).hex() == reference["packed"]


def test_starter_project_packs_to_firmware_size() -> None:
    assert len(flash_packer.pack(starter_project())) == flash_packer.FLASH_CONTENT_SIZE


def _first_command_bytes(project: StudioProject) -> bytes:
    offset = flash_packer.GLOBAL_SETTINGS_SIZE + flash_packer.NUM_BANKS * flash_packer.BANK_STRING_SIZE
    return flash_packer.pack(project)[offset : offset + flash_packer.MIDI_ROM_CMD_SIZE]


def _with_command(command: MidiCommand) -> StudioProject:
    project = starter_project()
    project.banks[0].buttons[0].commands = [command]
    return project


def test_suppressed_cc_off_value_is_above_the_firmware_threshold() -> None:
    """midi_cmds.c sends no off value when pRom[3] > 0x7F."""
    packed = _first_command_bytes(
        _with_command(MidiCommand(type="CC", channel=1, number=20, onValue=127, suppressOff=True))
    )
    assert packed[3] > 0x7F

    kept = _first_command_bytes(
        _with_command(
            MidiCommand(type="CC", channel=1, number=20, onValue=127, offValue=64, suppressOff=False)
        )
    )
    assert kept[3] == 64


def test_toggle_is_the_top_bit_of_byte_one() -> None:
    on = _first_command_bytes(
        _with_command(MidiCommand(type="CC", channel=1, number=20, toggle=True))
    )
    off = _first_command_bytes(
        _with_command(MidiCommand(type="CC", channel=1, number=20, toggle=False))
    )
    assert on[1] & 0x80 and not off[1] & 0x80
    assert on[1] & 0x7F == off[1] & 0x7F == 20


def test_channel_is_zero_based_in_the_low_nibble() -> None:
    packed = _first_command_bytes(_with_command(MidiCommand(type="CC", channel=16, number=1)))
    assert packed[0] == flash_packer.CMD_CC_NIBBLE | 0x0F


def test_program_change_suppresses_only_the_high_bank_byte_by_default() -> None:
    low_only = _first_command_bytes(
        _with_command(MidiCommand(type="PC", channel=1, number=5, bankSelect=200))
    )
    assert low_only[2] > 0x7F
    assert low_only[3] == 200 & 0x7F

    both = _first_command_bytes(
        _with_command(
            MidiCommand(type="PC", channel=1, number=5, bankSelect=200, bankSelectHighByte=True)
        )
    )
    assert both[2] == 200 >> 7
    assert both[3] == 200 & 0x7F


def test_pitch_bend_is_centred_on_0x2000() -> None:
    centre = _first_command_bytes(_with_command(MidiCommand(type="PB", channel=1, onValue=0)))
    assert centre[1] & 0x7F == 0x00
    assert centre[2] == 0x40  # 0x2000 >> 7


def test_duration_is_stored_in_ten_millisecond_units() -> None:
    packed = _first_command_bytes(
        _with_command(MidiCommand(type="Note", channel=1, number=60, durationMs=1270))
    )
    assert packed[3] == 127


def test_absent_commands_pad_the_switch_block_with_zeros() -> None:
    project = _with_command(MidiCommand(type="CC", channel=1, number=20))
    packed = flash_packer.pack(project)
    offset = flash_packer.GLOBAL_SETTINGS_SIZE + flash_packer.NUM_BANKS * flash_packer.BANK_STRING_SIZE
    stride = flash_packer.MIDI_NUM_COMMANDS_PER_SWITCH * flash_packer.MIDI_ROM_CMD_SIZE
    assert packed[offset + 4 : offset + stride] == bytes(stride - 4)


def test_text_fields_are_space_padded_to_fixed_width() -> None:
    project = starter_project()
    project.globalSettings.configName = "Lead"
    project.banks[0].largeName = "AB"
    project.banks[0].smallName = "Rig"
    packed = flash_packer.pack(project)
    assert packed[16:32] == b"Lead            "
    assert packed[32:36] == b"AB  "
    assert packed[36:44] == b"Rig     "
