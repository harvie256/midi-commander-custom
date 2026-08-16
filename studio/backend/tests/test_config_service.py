import re
from pathlib import Path

from studio.backend.config_service import (
    FLASH_CONTENT_SIZE,
    GLOBAL_SETTINGS_SIZE,
    MIDI_ROM_CMD_SIZE,
    pack_project,
    project_from_csv,
    project_to_csv,
    validate_project,
)
from studio.backend.models import starter_project


REPO_ROOT = Path(__file__).resolve().parents[3]
FIRMWARE_HEADER = (
    REPO_ROOT / "MIDI_Commander_Custom" / "Core" / "Inc" / "flash_midi_settings.h"
)
FIRMWARE_SOURCE = (
    REPO_ROOT / "MIDI_Commander_Custom" / "Core" / "Src" / "flash_midi_settings.c"
)


def _define(text: str, name: str) -> int:
    match = re.search(rf"^#define\s+{name}\s+\(?(\d+)\)?", text, re.MULTILINE)
    assert match, f"{name} not found in the firmware source"
    return int(match.group(1))


def test_flash_layout_matches_firmware_header() -> None:
    """The wire contract has no enforcement in the firmware direction, so pin the
    Python side against the C headers it mirrors."""
    header = FIRMWARE_HEADER.read_text()
    assert MIDI_ROM_CMD_SIZE == _define(header, "MIDI_ROM_CMD_SIZE")

    from lib import cmdBinaryPacker

    assert cmdBinaryPacker.MIDI_NUM_COMMANDS_PER_SWITCH == _define(
        header, "MIDI_NUM_COMMANDS_PER_SWITCH"
    )

    # pSwitchCmds sits at FLASH_SETTINGS_START+32+96, i.e. directly after the
    # global settings block and the bank strings.
    source = FIRMWARE_SOURCE.read_text()
    assert "FLASH_SETTINGS_START+32+96" in source.replace(" ", "")
    assert GLOBAL_SETTINGS_SIZE == 32

    # The packed image must still fit the region the firmware erases.
    pages = _define(source, "FLASH_SETTINGS_NO_PAGES")
    assert FLASH_CONTENT_SIZE <= pages * 1024


def test_flash_content_size_is_the_expected_layout() -> None:
    assert FLASH_CONTENT_SIZE == 2688


def test_starter_project_packs_to_firmware_size() -> None:
    project = starter_project()
    assert not [issue for issue in validate_project(project) if issue["level"] == "error"]
    assert len(pack_project(project)) == FLASH_CONTENT_SIZE


def test_round_trip_generated_csv() -> None:
    source = starter_project()
    imported = project_from_csv(project_to_csv(source), "round-trip.csv")
    assert imported.globalSettings.configName == source.globalSettings.configName
    assert imported.banks[0].buttons[1].commands[0].type == "CC"
    assert len(pack_project(imported)) == FLASH_CONTENT_SIZE


def test_repository_sample_imports() -> None:
    sample = REPO_ROOT / "python" / "MeloConfig_10_Cmds - RC-600.csv"
    project = project_from_csv(sample.read_text(), sample.name)
    assert len(pack_project(project)) == FLASH_CONTENT_SIZE
    assert project.banks[0].buttons[4].commands[0].type == "CC"
