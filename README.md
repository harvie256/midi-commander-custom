# midi-commander-custom
Custom Firmware for the MeloAudio Midi Commander

There's no intention of this replacing the default firmware functions. I'm creating this purely for custom requirements that the original firmware will never fulfill.

# Build status

There is the current build under DFU\DFU_OUT\generated_xxx.dfu

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
- CC, Note and Pitch Bend support momenary, toggle, or an on-duration of up to 2.5 sec in 10ms increments. CC can also send just the start message.
- Program Change messages can include the Bank Select messages prior to the PC message, either just the Lease Signficant Byte or both the LSB & MSB.
- Pass through of Sync/Start/Stop messages from USB to the Serial MIDI connector.

- Firmware can be loaded through the normal DFU update process.
- Configuration has been moved to the FLASH memory, so this will not affect the standard Melo firmware configuration that is stored in an external EEPROM.
- Provides SYSEX tools for downloading and uploading both the configuration section for this firmware.

# Still to come
- Expression Pedal inputs
- The battery management has not been considered yet.  Not sure if it even works on batteries with this.
- Plenty of code tidying to be done
- Plenty of testing needed
- Needs documentation.


# Configuration
The basic configuration idea, is you use a spreadsheet template to create a configuration CSV file.  Here's a Public visable copy of a test google doc sheet I'm using.
This has some conditional formating and layout that makes choosing commands quite straight forward.
Updated: New spreadsheet from eliericha with the 10 command per button improvement:
https://docs.google.com/spreadsheets/d/1KwKj3sYrNEkEl8ONipW-ZGSLD7r_W1NfWwyGgjnbk08/edit?usp=sharing

The downloaded (or "Save As" in excel et al) CSV file is then passed to CSV_to_Flash.py, which will convert the CSV file to a binary format and download to the USB connect midi-commander.


# Basic instructions for setting up development environment
Other than the simple python scripts, it's all just STM32CubIDE. Install that, import the project into your workspace (it's just shrink wrapped eclipse) and your done.

There's two Build settings, one for the DFU (with offset linker script and vector table) and the other for using with a ST-Link debugger. To build a DFU file for upload you'll need to build the binary in the IDE, then use the DFU packing tool that comes with the DFU uploader (can't remember their exact names off the top of my head.) Using the Intel HEX format file instead of the .bin saves you having to input the flash offset.
