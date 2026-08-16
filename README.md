# midi-commander-custom
Custom Firmware for the MeloAudio Midi Commander

There's no intention of this replacing the default firmware functions. I'm creating this purely for custom requirements that the original firmware will never fulfill.

This project provides the following components that work together:

1. A custom firmware to be loaded onto the Midi Commander (e.g. using DFU tool)

2. **MIDI Commander Studio**, a visual editor that configures the pedal and installs firmware over USB

# MIDI Commander Studio (macOS, Windows, and Linux GUI)

**MIDI Commander Studio** is a local visual editor for macOS, Windows, and Linux, and the only supported way to configure the pedal. It provides a pedal-style bank and button editor, project autosave, direct configuration upload, MIDI device diagnostics, and a guarded firmware installation workflow.

> **Note for existing users:** the previous CSV spreadsheet workflow and the `python/CSV_to_Flash.py` command-line tool have been removed, along with Studio's CSV import and export. Planned features change the configuration model in ways the CSV layout cannot follow. If you still have a CSV configuration, check out a revision of this repository from before the removal, import the CSV in that older Studio, and save it as a `.mcs.json` project file.

## Purpose

MIDI Commander Studio is one local browser interface for everything. It is intended for users of this repository's custom firmware who want to:

- visually configure all eight banks and eight switches;
- assign up to ten ordered MIDI commands to each switch;
- validate MIDI channels, controller numbers, values, names, and firmware limits before uploading;
- install the bundled custom firmware with explicit DFU target checks; and
- upload a validated 2,688-byte configuration directly over USB MIDI.

The application runs locally at `http://127.0.0.1:8765`. Project data stays in the browser unless the user explicitly saves or exports it.

## Platform status

| Platform | Status |
| --- | --- |
| macOS | **Tested end-to-end with a physical MIDI Commander:** Studio launch, custom firmware installation, MIDI detection, validation, and configuration upload are working. |
| Windows 10/11 (64-bit) | Launcher, dependency setup, UI, automated tests, and CI are included. **Physical Windows firmware and MIDI upload testing is still pending**, so Windows support should be treated as beta. |
| Linux | Launcher, dependency setup, UI, and CI are included. ALSA MIDI ports are enumerated through `python-rtmidi`. **Physical Linux firmware and MIDI upload testing is still pending**, so Linux support should be treated as beta. |

## Typical workflow

1. Keep a matching stock firmware recovery file before replacing firmware.
2. Start MIDI Commander Studio using the launcher for your operating system.
3. If the pedal still has stock firmware, use **Firmware** once to install the bundled custom firmware, then power-cycle normally.
4. Use **Editor** to configure banks, switches, and MIDI commands. Fix any validation messages shown by Studio.
5. Use **Device** to select the pedal's MIDI input/output ports and upload the configuration.
6. Save a `.mcs.json` project file — this is the only way to keep a configuration outside the browser.

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

## Start the Studio on Linux

> **Testing status:** Linux hardware testing is pending. Keep a recovery file and use the Linux firmware workflow as beta software until it has been verified with a physical pedal.

1. Install Python 3 with virtual-environment support (`sudo apt install python3 python3-venv` on Debian/Ubuntu).
2. Install the MIDI build dependencies (`sudo apt install libasound2-dev libjack-jackd2-dev`). These are only needed when `python-rtmidi` has no prebuilt wheel for your Python version and must be compiled.
3. For the firmware workflow, install `dfu-util` (`sudo apt install dfu-util`); the Studio does not download it automatically on Linux.
4. Run `./"Launch MIDI Commander Studio.sh"` from a terminal, or double-click it in your file manager and choose **Run**.
5. On the first launch, allow a minute for the private Python environment to be prepared. Later launches are immediate.
6. The Studio opens in your default browser at `http://127.0.0.1:8765`.

Stop the local service with the power button in the top-right corner, or run `./"Stop MIDI Commander Studio.sh"`.

Installing firmware over DFU needs write access to the USB device. Either run the DFU step as root or add a udev rule for the pedal's bootloader (`0483:df11`) so it is writable by your user.

Use the **Editor** to design banks and commands, **Device** to upload a configuration while the pedal is in normal mode, and **Firmware** only when installing the bundled custom firmware in DFU mode.

See [`studio/README.md`](studio/README.md) for implementation and development details.

# Build status

There is the current build under `DFU\DFU_OUT\generated_xxx.dfu`. See the instructions in the [development environment section](#basic-instructions-for-setting-up-development-environment) for building the firmware locally and/or loading it to the device.

Anything I leave in there has had a bit of testing on my device, and everything appears to be working ok.  These are still Dev builds, so it's likely they'll have bugs.  But it's something you can play with, and you should be able to go back to an meloaudio build.

The DFU binary is uploaded with `dfu-util`, on any operating system — see [Loading the firmware](#loading-the-firmware). Note that earlier versions of these instructions used MeloAudio's updater and ST's DfuSe tools, which gave a lot of trouble under Windows 10; `dfu-util` is now the supported route and those tools are only needed for [going back to the MeloAudio firmware](#going-back-to-the-meloaudio-firmware).

# Improvements in this commit
24 Apr 22 - The display driver has been modified to use DMA for all transfers, and interrupts to kick off the transfer of each line.  The result is the processor isn't stalled waiting for the display to update. This will allow the display to be utilised more on individual key presses without resulting in delays.  From an end user perspective, there should be no visable change.

# Current features list
- Completely open source, so feel free to contribute (even just bug reports! or better still user guides)
- Visual configuration from a computer, no scrolling through menus on that tiny screen with huge buttons. Projects save to a single file, so they are easy to keep and share.
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

Configuration is done in **MIDI Commander Studio** — see [the Studio section above](#midi-commander-studio-macos-windows-and-linux-gui) for how to start it. The **Editor** page lays out all eight banks and eight switches; **Device** uploads the result to the pedal over USB.

Studio allows you to specify for each button press up to 10 independant MIDI commands. For each command the following characteristics can be chosen independently:

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

Studio validates these against the firmware's limits as you edit, and refuses to upload a configuration that would not fit.

Save your work with **Save project** in the header, which writes a `.mcs.json` file, and reload it later with **Open project**. Studio also keeps the current project in the browser's local storage automatically, but the project file is the only copy that survives clearing site data or moving to another computer.

To load a configuration onto the Midi Commander:

1. Turn on the Midi Commander in normal mode (not DFU)
2. Connect it to the USB port of your computer
3. Open the **Device** page, select the pedal's MIDI input and output ports, and upload

Studio converts the project to the firmware's binary format and transmits it over USB MIDI. At the end of the operation the Midi Commander restarts to load the new configuration.

## The old spreadsheet workflow

Configuration used to be a Google Sheets template exported as CSV and uploaded with `python/CSV_to_Flash.py`. That tool and all CSV support have been removed, because planned features change the configuration model in ways the CSV layout cannot follow.

If you have an existing CSV configuration, check out a revision of this repository from before the removal, import the CSV there, and save it as a `.mcs.json` project file that current Studio can open.

# Basic instructions for setting up development environment
Other than the simple python scripts, the firmware is a CMake project. You need CMake (3.22 or later), a build tool such as Ninja, and the `arm-none-eabi` GCC toolchain. On Debian/Ubuntu:

```
sudo apt install cmake ninja-build gcc-arm-none-eabi binutils-arm-none-eabi
```

In VS Code, install the [STM32 VS Code Extension](https://marketplace.visualstudio.com/items?itemName=STMicroelectronics.stm32-vscode-extension) and open the `MIDI_Commander_Custom` folder. The build configurations are picked up from `CMakePresets.json`. Alternatively, build from the command line:

```
cd MIDI_Commander_Custom
cmake --preset "DFU Release"
cmake --build --preset "DFU Release"
```

There are two build presets. `DFU Release` is the one to flash through the DFU bootloader: it is optimised, linked at `0x8003000` with the offset linker script, and relocates the vector table to match. `Debug` is unoptimised and linked at the start of flash for use with an ST-Link debugger.

Each build writes `MIDI_Commander_Custom.elf`, `.hex`, and `.bin` into `build/<preset name>/`. The `DFU Release` preset additionally packs `MIDI_Commander_Custom.dfu`, ready to upload — building it is a single step, and no ST tooling is involved.

The `Debug` preset deliberately does not produce a `.dfu`. It is linked at the start of flash, so uploading one through the bootloader would overwrite the bootloader itself.

Packing needs Python 3 on the `PATH`. If CMake cannot find it you still get the `.elf`, `.hex`, and `.bin`, and the build prints a warning rather than failing.

### Packing a DFU file by hand

`DFU/bin_to_dfu.py` is a standalone tool, so an existing build can be packed without rebuilding it:

```
python3 DFU/bin_to_dfu.py "MIDI_Commander_Custom/build/DFU Release/MIDI_Commander_Custom.hex" \
    -o DFU/DFU_OUT/generated.dfu
```

Giving it the Intel HEX file saves you having to state the flash offset, since the address is already recorded in the file. To pack a raw binary instead, name the load address explicitly:

```
python3 DFU/bin_to_dfu.py "MIDI_Commander_Custom/build/DFU Release/MIDI_Commander_Custom.bin" \
    -a 0x8003000 -o DFU/DFU_OUT/generated.dfu
```

Both routes produce the same file.

If your `arm-none-eabi-gcc` is not on the `PATH` — for instance if you want to use the copy bundled with STM32CubeIDE — point CMake at it when configuring:

```
cmake --preset "DFU Release" -DTOOLCHAIN_PREFIX=/path/to/toolchain/bin/
```

## Loading the firmware

The firmware is loaded with [dfu-util](https://dfu-util.sourceforge.net/), which works the same way on Linux, macOS and Windows:

| | |
|---|---|
| Linux | `sudo apt install dfu-util` (or your distribution's equivalent) |
| macOS | `brew install dfu-util` using [Homebrew](https://brew.sh/) |
| Windows | Download the binaries from the [dfu-util site](https://dfu-util.sourceforge.net/), then use [Zadig](https://zadig.akeo.ie/) to assign the WinUSB driver to the device while it is in DFU mode |

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

If you are building the firmware yourself, you can skip the `.dfu` packaging altogether and load the binary directly, naming the load address explicitly:

```
dfu-util --alt 0 -s 0x8003000 --download "./MIDI_Commander_Custom/build/DFU Release/MIDI_Commander_Custom.bin"
```

If you would rather produce a `.dfu` — to share a build with someone else, for instance — see [Packing a DFU file by hand](#packing-a-dfu-file-by-hand) above.

Once the firmware is loaded, turn off the device and turn it back on in normal mode. You should see the name and version of the custom firmware on the display briefly, and then the name of the first configured bank. You can now load your own configuration following the instructions in the section [Configuration](#configuration).

### Going back to the MeloAudio firmware

The stock firmware is loaded with MeloAudio's own updater, which is built on ST's DfuSe tools rather than dfu-util. On Windows those two want different USB drivers, so if you used Zadig to switch the device to WinUSB you will need to point the driver back at ST's before the MeloAudio updater will see it. A copy of the ST tools and their drivers is kept in this repository under `DFU/MidiCommander_DFU_APP/`, and they are also available from ST as package STSW-STM32080. Nothing in this project uses them otherwise.

Your MeloAudio configuration is not affected by any of this: the custom firmware keeps its settings in the microcontroller's own flash memory, and never touches the external EEPROM that the stock firmware stores its configuration in.

## Python development

The Python code lives under `studio/backend/`. It is recommended to use the VS Code workspace at the root of this repository with the recommended extensions; it is configured to use auto-formatting with Black and type checking with MyPy.

The entry point is `studio/backend/app.py` (a FastAPI application). Configuration validation lives in `config_service.py`, the flash encoder in `flash_packer.py`, and MIDI and DFU handling in `device_service.py`. Tests are under `studio/backend/tests/` — run them with `python -m pytest studio/backend/tests` from the repository root. See [`studio/README.md`](studio/README.md) for more.

# Acknowledgements

- @harvie256: project founder
- @eliericha: expansion to 10 commands per button
