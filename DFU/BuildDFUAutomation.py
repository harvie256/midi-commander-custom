# This script automates the generation of the DFU file from the release build.
# File paths are generated relative to the repo, so should work where ever the repo is put.
#
# Requires pywinauto.
#   pip install pywinauto


from pywinauto.application import Application
from pywinauto.timings import Timings
import time
from pathlib import Path
import os


# Create file paths relative to the repo
BASE_PATH = Path(os.path.realpath(__file__)).parent.parent.absolute()
DFU_FILE_MGR_PATH = BASE_PATH.joinpath(r"DFU\MidiCommander_DFU_APP\DfuFileMgr.exe").__str__()
HEX_FILE_PATH = BASE_PATH.joinpath(r"MIDI_Commander_Custom\DFU Release\MIDI_Commander_Custom.hex").__str__()
DFU_OUTPUT_PATH = BASE_PATH.joinpath(r'DFU\DFU_OUT\generated-{}.dfu'.format(time.strftime("%Y%m%d-%H%M%S"))).__str__()

# Create the output folder if it doesn't exist
BASE_PATH.joinpath(r'DFU\DFU_OUT').mkdir(parents=True, exist_ok=True)

# Increase key stroke speed, which seems to work fine for this app.
Timings.fast()

app = Application().start(DFU_FILE_MGR_PATH, timeout=10)

start_dlg = app.window(title='DFU File Manager - Want to do (v3.0.6)')
start_dlg.OK.click()

fileMgr_dlg = app.window(title='DFU File Manager (v3.0.6) - Generation')
fileMgr_dlg.child_window(title="&S19 or Hex...", class_name="Button").click()

app.Open.child_window(title="*.hex", class_name="Edit").type_keys(HEX_FILE_PATH, with_spaces=True)
app.Open.Open.click()

fileMgr_dlg.child_window(title="&Generate...", class_name="Button").click()

saveAs_dlg = app.window(title='Save As')
saveAs_dlg.child_window(title="*.dfu", class_name="Edit").type_keys(DFU_OUTPUT_PATH, with_spaces=True)
saveAs_dlg.Save.click()

confirm_dlg = app.window(title="DfuFileMgr")
confirm_dlg.OK.click()

fileMgr_dlg.child_window(title="&Cancel", class_name="Button").click()

print('Output Filename: ', DFU_OUTPUT_PATH)
