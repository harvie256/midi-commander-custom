# midi-commander-custom
Custom Firmware for the MeloAudio Midi Commander

There's no intention of this replacing the default firmware functions. I'm creating this purely for custom requirements that the original firmware will never fulfill.

This project provides the following components that work together:

1. A custom firmware to be loaded onto the Midi Commander (e.g. using DFU tool)

2. A publicly available configuration template spreadsheet on Google Sheets that you can customize to your needs

3. The `python/CSV_to_Flash.py` tool that can load a configuration spreadsheet to the Midi Commander through a simple USB connection

# Build status

There is the current build under `DFU\DFU_OUT\generated_xxx.dfu`

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
   pip install -r python/requirements.txt
   python python/CSV_to_Flash.py -h
   ```

   If your setup is successful, the last command should display the help message of the tool.

Once your Python environment is operational, you can load your configuration onto the Midi Commander as follows:

1. Turn on the Midi Commander in normal mode (not DFU)
2. Connect it to the USB port of your computer
3. Run the following in a Terminal or in the Windows Command Prompt:

   ```
   cd /path/to/midi-commander-custom
   python python/CSV_to_Flash.py /path/to/you/configuration-file.csv
   ```

The tool will convert the CSV file to a binary format and transmit it to the Midi Commander. At the end of the operation the Midi Commander should restart to load the new configuration.

# Basic instructions for setting up development environment
Other than the simple python scripts, it's all just STM32CubIDE. Install that, import the project into your workspace (it's just shrink wrapped Eclipse) and your done.

There's two Build settings, one for the DFU (with offset linker script and vector table) and the other for using with a ST-Link debugger. To build a DFU file for upload you'll need to build the binary in the IDE, then use the DFU packing tool that comes with the DFU uploader (can't remember their exact names off the top of my head.) Using the Intel HEX format file instead of the .bin saves you having to input the flash offset.

## Python development
Python files under `python/` can be edited directly, however it is recommended to use the VS Code workspace at the root of this repository with the recommended extensions. It is configured to use auto-formatting with Black and type checking with MyPy.

The main entry point is `python/CSV_to_Flash.py` and some functionality is offloaded to modules under `python/lib`.

# Acknowledgements

- @harvie256: project founder
- @eliericha: expansion to 10 commands per button