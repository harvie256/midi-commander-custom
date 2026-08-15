# midi-commander-custom
Custom Firmware for the MeloAudio Midi Commander

There's no intention of this replacing the default firmware functions. I'm creating this purely for custom requirements that the original firmware will never fulfill.

This project provides the following components that work together:

1. A custom firmware to be loaded onto the Midi Commander (e.g. using DFU tool)

2. A publicly available configuration template spreadsheet on Google Sheets that you can customize to your needs

3. The `python/CSV_to_Flash.py` tool that can load a configuration spreadsheet to the Midi Commander through a simple USB connection

# MIDI Commander Studio (macOS and Windows GUI)

This repository now includes **MIDI Commander Studio**, a local visual editor for macOS and Windows. It provides a pedal-style bank and button editor, project autosave, CSV import/export, direct configuration upload, MIDI device diagnostics, and a guarded firmware installation workflow.

## Purpose

MIDI Commander Studio replaces the manual CSV-editing and command-line upload workflow with one local browser interface. It is intended for users of this repository's custom firmware who want to:

- visually configure all eight banks and eight switches;
- assign up to ten ordered MIDI commands to each switch;
- validate MIDI channels, controller numbers, values, names, and firmware limits before uploading;
- import or export repository-compatible CSV files;
- install the bundled custom firmware with explicit DFU target checks; and
- upload a validated 2,688-byte configuration directly over USB MIDI.

The application runs locally at `http://127.0.0.1:8765`. Project data stays in the browser unless the user explicitly saves or exports it.

## Platform status

| Platform | Status |
| --- | --- |
| macOS | **Tested end-to-end with a physical MIDI Commander:** Studio launch, custom firmware installation, MIDI detection, validation, and configuration upload are working. |
| Windows 10/11 (64-bit) | Launcher, dependency setup, UI, automated tests, and CI are included. **Physical Windows firmware and MIDI upload testing is still pending**, so Windows support should be treated as beta. |

## Typical workflow

1. Keep a matching stock firmware recovery file before replacing firmware.
2. Start MIDI Commander Studio using the launcher for your operating system.
3. If the pedal still has stock firmware, use **Firmware** once to install the bundled custom firmware, then power-cycle normally.
4. Use **Editor** to configure banks, switches, and MIDI commands. Fix any validation messages shown by Studio.
5. Use **Device** to select the pedal's MIDI input/output ports and upload the configuration.
6. Save a `.mcs.json` project for future editing and optionally export CSV for the original tooling.

## Start the Studio on macOS

1. In Finder, open this repository folder.
2. Double-click `Launch MIDI Commander Studio.command`.
3. On the first launch, allow a minute for the private Python environment to be prepared. Later launches are immediate.
4. The Studio opens in your default browser at `http://127.0.0.1:8765`.

If macOS refuses to open the launcher, Control-click it, choose **Open**, and confirm once. The app runs only on your Mac and binds to the local loopback address.

## Start the Studio on Windows

> **Testing status:** Windows hardware testing is pending. Keep a recovery file and use the Windows firmware workflow as beta software until it has been verified with a physical pedal.

1. Install [Python 3](https://www.python.org/downloads/windows/) and enable **Add Python to PATH** in its installer.
2. Extract the repository ZIP to a normal writable folder; do not run it from inside the ZIP viewer.
3. Double-click `Launch MIDI Commander Studio.cmd`.
4. On the first launch, allow a minute for the private Python environment to be prepared. Later launches are immediate.
5. The Studio opens in your default browser at `http://127.0.0.1:8765`.

Windows SmartScreen may show a warning because the open-source launcher is not code-signed. Choose **More info → Run anyway** after confirming that you downloaded the repository from its expected GitHub page. See [`docs/WINDOWS.md`](docs/WINDOWS.md) for firmware-driver setup, troubleshooting, and verification details.

Use the **Editor** to design banks and commands, **Device** to upload a configuration while the pedal is in normal mode, and **Firmware** only when installing the bundled custom firmware in DFU mode. The Studio automatically creates repository-compatible CSV files, so the command-line workflow remains available.

See [`studio/README.md`](studio/README.md) for implementation and development details.

# Build status

There is the current build under `DFU\DFU_OUT\generated_xxx.dfu`. See the instructions in the [development environment section](#basic-instructions-for-setting-up-development-environment) for building the firmware locally and/or loading it to the device.

Anything I leave in there has had a bit of testing on my device, and everything appears to be working ok.  These are still Dev builds, so it's likely they'll have bugs.  But it's something you can play with, and you should be able to go back to an meloaudio build.

Uploading the DFU binary is the same as for the meloaudio firmware.  So download the firmware update tools from the meloaudio website (or directly from ST - package STSW-STM32080) and follow the upgrade manual.

I have had a lot of issues under Windows 10, and there are reports from others on the net to this effect. So I'm using a Windows 7 Virtual Machine to test the DFU aspects, which works fine.

# Improvements in this commit
24 Apr 22 - The display driver has been modified to use DMA for all transfers, and interrupts to kick off the transfer of each line.  The result is the processor isn't stalled waiting for the display to update. This will allow the display to be utilised more on individual key presses without resulting in delays.  From an end user perspective, there should be no visable change.

# Current features list
- Completely open source, so feel free to contribute (even just bug reports! or better still user guides)
- "Spreadsheet" based configuration, no scrolling through menus on that tiny screen with huge buttons. Easy Copy/Paste, Fill, etc. Easy sharing.
- Supports Program Change (aka Patch Change), Controller Change, Note, Pitch Bend and Start/Stop messages for any of the buttons.
- The Channel for each message is configured on each individual command.  So it can address seperate pieces of hardware in a midi chain.
- 8 banks of 8 buttons.  Each bank can display message strings for identification.
- 0 to 10 independant chained commands on each switch/bank position.  Enables configuring different devices, or a series of actions of each button push.
- CC, Note and Pitch Bend support momentary, toggle, or an on-duration of up to 2.5 sec in 10ms increments. CC can also send just the start message.
- Program Change messages can include the Bank Select messages prior to the PC message, either just the Lease Signficant Byte or both the LSB & MSB.
- Pass through of Sync/Start/Stop messages from USB to the Serial MIDI connector.

- Firmware can be loaded through the normal DFU update process.
- Configuration has been moved to the FLASH memory, so this will not affect the standard Melo firmware configuration that is stored in an external EEPROM.

# Still to come
- Expression Pedal inputs
- The battery management has not been considered yet.  Not sure if it even works on batteries with this.
- Plenty of code tidying to be done
- Plenty of testing needed
- Needs documentation.


# Configuration
The configuration is done via a spreadsheet. Here is a publicly available template on Google Sheets that you can copy and customize to your needs:

https://docs.google.com/spreadsheets/d/1KwKj3sYrNEkEl8ONipW-ZGSLD7r_W1NfWwyGgjnbk08/edit?usp=sharing

(a copy of this spreasheet is also availble in the repository at `python/MeloConfig_10_Cmds - RC-600.csv`)

Roughly, the spreadsheet allows you to specify for each button press up to 10 independant MIDI commands. For each command the following characteristics can be chosen independently:

- Type: PC/CC/Note/PB (Pitch Bend)/Start/Stop
- Midi Channel
- PC/CC/Note number
- CC/PB button on value
- CC/PB button off value
- PC bank select value
- PC bank select value high byte
- CC/PB/Note toggle mode
  - If disabled, the button on value is sent when the button is held down, and the button off value is sent when the button is released. So each button press results in 2 commands sent.
  - If enabled, the button on value is sent at the first button press, and the button off value is sent at the next button press and so on. So each button press results in 1 command sent. The LED of the button is toggled on and off at each button press.
- Note velocity
- Note/PB duration (up to 2.5 seconds in 10ms increments)

Lines starting with `#` or `*` are simply ignored which allows you to include comments in the configuration file to keep track of your work.

Once you are happy with your configuration, download it from Google Sheets as a CSV file (or use "Save As" if you chose to edit it locally with Excel or similar spreadsheet software).

Then prepare a Python environment as follows:

1. Download and install [Python](https://www.python.org/).
2. Check out this repository with Git or download it as a Zip and extract it somewhere.
3. Open a Terminal (or Windows Command Prompt) and run the following:

   ```
   cd /path/to/midi-commander-custom
   python3 -m pip install -r python/requirements.txt
   python3 python/CSV_to_Flash.py -h
   ```

   If your setup is successful, the last command should display the help message of the tool.

Once your Python environment is operational, you can load your configuration onto the Midi Commander as follows:

1. Turn on the Midi Commander in normal mode (not DFU)
2. Connect it to the USB port of your computer
3. Run the following in a Terminal or in the Windows Command Prompt:

   ```
   cd /path/to/midi-commander-custom
   python3 python/CSV_to_Flash.py /path/to/you/configuration-file.csv
   ```

The tool will convert the CSV file to a binary format and transmit it to the Midi Commander. At the end of the operation the Midi Commander should restart to load the new configuration.

# Basic instructions for setting up development environment
Other than the simple python scripts, it's all just [STM32CubeIDE](https://www.st.com/en/development-tools/stm32cubeide.html). Install that, import the project from the `MIDI_Commander_Custom` directory into your workspace (it's just shrink wrapped Eclipse) and you're done.

There are two Build target, one called `DFU Release` for the DFU (with offset linker script and vector table) and the other called `Debug` for use with a ST-Link debugger. To build a DFU file for upload you'll need to build the binary in the IDE, then use the DFU packing tool that comes with the DFU uploader (can't remember their exact names off the top of my head.) Using the Intel HEX format file instead of the .bin saves you having to input the flash offset.

## Loading the firmware

### macOS

On macOS the firmware can be loaded with [dfu-util](https://dfu-util.sourceforge.net/) which can be installed using [Homebrew](https://brew.sh/) with a simple `brew install dfu-util`.

Then you connect the Midi Commander to the USB port of the computer and start it in DFU mode by holding down the `bank down` and `D` buttons (the two buttons on the bottom-right corner) while pressing the power button. The device should start with nothing on the display, and the LED 3 turned on.

`dfu-util` should now be able to detect the device:

```
$ dfu-util --list
...
Found DFU: [0483:df11] ver=0200, devnum=12, cfg=1, intf=0, path="4-1", alt=2, name="@NOR Flash : M29W128F/0x64000000/0256*64Kg", serial="5CE867623433"
Found DFU: [0483:df11] ver=0200, devnum=12, cfg=1, intf=0, path="4-1", alt=1, name="@SPI Flash : M25P64/0x00000000/128*64Kg", serial="5CE867623433"
Found DFU: [0483:df11] ver=0200, devnum=12, cfg=1, intf=0, path="4-1", alt=0, name="@Internal Flash  /0x08000000/06*002Ka,250*002Kg", serial="5CE867623433"
```

If you have a DFU file (e.g. from `DFU/DFU_OUT/generated-*.dfu`), you can load it as follows. `--alt 0` should be used because it corresponds to the address range of the internal flash `0x80000000` in the list above.

```
dfu-util --alt 0 --download ./DFU/DFU_OUT/generated-*.dfu
```

If you are building the firmware yourself on macOS, it is unclear how you can create a DFU file. Instead you should use a binary file and specify the load address explicitly. To do that, use the `DFU Release` build target in STM32CubeIDE to produce a `.bin` binary file that you can load as follows:

```
dfu-util --alt 0 -s 0x8003000 --download "./MIDI_Commander_Custom/DFU Release/MIDI_Commander_Custom.bin"
```

Once the firmware is loaded, turn off the device and turn it back on in normal mode. You should see the name and version of the custom firmware on the display briefly, and then the name of the first configured bank. You can now load your own configuration following the instructions in the section [Configuration](#configuration).

## Python development
Python files under `python/` can be edited directly, however it is recommended to use the VS Code workspace at the root of this repository with the recommended extensions. It is configured to use auto-formatting with Black and type checking with MyPy.

The main entry point is `python/CSV_to_Flash.py` and some functionality is offloaded to modules under `python/lib`.

# Acknowledgements

- @harvie256: project founder
- @eliericha: expansion to 10 commands per button
