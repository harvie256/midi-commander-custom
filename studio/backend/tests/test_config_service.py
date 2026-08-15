from pathlib import Path

from studio.backend.config_service import (
    pack_project,
    project_from_csv,
    project_to_csv,
    validate_project,
)
from studio.backend.models import starter_project


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_starter_project_packs_to_firmware_size() -> None:
    project = starter_project()
    assert not [issue for issue in validate_project(project) if issue["level"] == "error"]
    assert len(pack_project(project)) == 2688


def test_round_trip_generated_csv() -> None:
    source = starter_project()
    imported = project_from_csv(project_to_csv(source), "round-trip.csv")
    assert imported.globalSettings.configName == source.globalSettings.configName
    assert imported.banks[0].buttons[1].commands[0].type == "CC"
    assert len(pack_project(imported)) == 2688


def test_repository_sample_imports() -> None:
    sample = REPO_ROOT / "python" / "MeloConfig_10_Cmds - RC-600.csv"
    project = project_from_csv(sample.read_text(), sample.name)
    assert len(pack_project(project)) == 2688
    assert project.banks[0].buttons[4].commands[0].type == "CC"
