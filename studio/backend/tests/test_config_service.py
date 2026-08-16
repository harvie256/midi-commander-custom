from __future__ import annotations

from studio.backend.config_service import pack_project, project_stats, validate_project
from studio.backend.flash_packer import FLASH_CONTENT_SIZE
from studio.backend.models import Bank, MidiCommand, PedalButton, StudioProject, starter_project


def _errors(project: StudioProject) -> list[dict[str, str]]:
    return [issue for issue in validate_project(project) if issue["level"] == "error"]


def test_starter_project_is_valid_and_packs() -> None:
    project = starter_project()
    assert not _errors(project)
    assert len(pack_project(project)) == FLASH_CONTENT_SIZE


def test_project_stats_reports_size_and_command_count() -> None:
    stats = project_stats(starter_project())
    assert stats["contentSize"] == FLASH_CONTENT_SIZE
    assert stats["commandCount"] == 2


def test_packing_refuses_an_invalid_project() -> None:
    project = starter_project()
    project.globalSettings.configName = "A configuration name far past the limit"
    try:
        pack_project(project)
    except ValueError as exc:
        assert "16 characters" in str(exc)
    else:  # pragma: no cover - the assertion above is the point
        raise AssertionError("pack_project accepted an invalid project")


def test_bank_count_is_enforced() -> None:
    project = starter_project()
    project.banks = project.banks[:4]
    assert any("exactly 8 banks" in issue["message"] for issue in _errors(project))


def test_button_ids_must_keep_their_firmware_order() -> None:
    project = starter_project()
    project.banks[0].buttons[0] = PedalButton(id="D", label="Wrong slot")
    assert any(issue["path"] == "banks.0.buttons.0" for issue in _errors(project))


def test_command_limit_per_button() -> None:
    project = starter_project()
    project.banks[0].buttons[0].commands = [
        MidiCommand(type="CC", channel=1, number=index) for index in range(11)
    ]
    assert any("at most 10 commands" in issue["message"] for issue in _errors(project))


def test_non_ascii_names_are_rejected() -> None:
    project = starter_project()
    project.banks[0].largeName = "Ünï"
    assert any("ASCII" in issue["message"] for issue in _errors(project))


def test_duration_must_be_a_multiple_of_ten_milliseconds() -> None:
    project = starter_project()
    project.banks[0].buttons[0].commands = [
        MidiCommand(type="Note", channel=1, number=60, durationMs=15)
    ]
    assert any("multiple of 10" in issue["message"] for issue in _errors(project))


def test_program_zero_is_a_warning_not_an_error() -> None:
    project = starter_project()
    project.banks[0].buttons[0].commands = [MidiCommand(type="PC", channel=1, number=0)]
    issues = validate_project(project)
    assert not [issue for issue in issues if issue["level"] == "error"]
    assert any(issue["level"] == "warning" for issue in issues)


def test_start_and_stop_ignore_the_channel_range() -> None:
    project = starter_project()
    project.banks[0].buttons[0].commands = [MidiCommand(type="Start", channel=0)]
    assert not _errors(project)


def test_bank_numbers_must_match_their_position() -> None:
    project = starter_project()
    project.banks[3] = Bank(
        number=7,
        largeName="BN 4",
        smallName="Bank 4",
        buttons=project.banks[3].buttons,
    )
    assert any(issue["path"] == "banks.3" for issue in _errors(project))
