from __future__ import annotations

from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


CommandType = Literal["PC", "CC", "Note", "PB", "Start", "Stop"]
BUTTON_IDS = ("1", "2", "3", "4", "A", "B", "C", "D")


class MidiCommand(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    type: CommandType = "CC"
    channel: int = 1
    number: int = 0
    onValue: int = 127
    offValue: int = 0
    suppressOff: bool = False
    bankSelect: int = 0
    bankSelectHighByte: bool = False
    toggle: bool = False
    velocity: int = 100
    durationMs: int = 0


class PedalButton(BaseModel):
    id: str
    label: str
    commands: list[MidiCommand] = Field(default_factory=list)


class Bank(BaseModel):
    number: int
    largeName: str
    smallName: str
    buttons: list[PedalButton]


class GlobalSettings(BaseModel):
    configName: str = "Lead Rig"
    realtimePassthrough: bool = False
    midiChannel: int = 1


class StudioProject(BaseModel):
    schemaVersion: int = 1
    name: str = "Lead Rig"
    globalSettings: GlobalSettings = Field(default_factory=GlobalSettings)
    banks: list[Bank]


class UploadRequest(BaseModel):
    inputName: str
    outputName: str
    project: StudioProject


class TestCommandRequest(BaseModel):
    outputName: str
    command: MidiCommand


class FirmwareInstallRequest(BaseModel):
    recoveryConfirmed: bool


def starter_project() -> StudioProject:
    labels = {
        "1": "Clean",
        "2": "Drive",
        "3": "Lead",
        "4": "Delay",
        "A": "FX 1",
        "B": "FX 2",
        "C": "Tap",
        "D": "Mute",
    }
    banks: list[Bank] = []
    for bank_number in range(8):
        buttons = [
            PedalButton(
                id=button_id,
                label=labels[button_id] if bank_number == 0 else f"Switch {button_id}",
            )
            for button_id in BUTTON_IDS
        ]
        banks.append(
            Bank(
                number=bank_number,
                largeName="LEAD" if bank_number == 0 else f"BN {bank_number + 1}",
                smallName="Lead rig" if bank_number == 0 else f"Bank {bank_number + 1}",
                buttons=buttons,
            )
        )

    banks[0].buttons[1].commands = [
        MidiCommand(type="CC", channel=1, number=17, onValue=127, offValue=0, toggle=True),
        MidiCommand(type="PC", channel=1, number=12, bankSelect=0),
    ]
    return StudioProject(banks=banks)
