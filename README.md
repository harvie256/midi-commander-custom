# midi-commander-custom
Custom Firmware for the MeloAudio Midi Commander

There's no intention of this replacing the default firmware functions. I'm creating this purely for custom requirements that the original firmware will never fulfill.

# Current features list
- Completely open source, so feel free to contribute (even just bug reports! or better still user guides)
- "Spreadsheet" based configuration, no scrolling through menus on that tiny screen with huge buttons. Easy Copy/Paste, Fill, etc. Easy sharing.
- Supports Program Change (aka Patch Change), Controller Change, Note, Pitch Bend and Start/Stop messages for any of the buttons.
- The Channel for each message is configured on each individual command.  So it can address seperate pieces of hardware in a midi chain.
- 8 banks of 8 buttons.  Each bank can display message strings for identification.
- 0 to 3 independant chained commands on each switch/bank position.  Enables configuring different devices, or a series of actions of each button push.
- CC, Note and Pitch Bend support momenary, toggle, or an on-duration of up to 2.5 sec in 10ms increments. CC can also send just the start message.
- Program Change messages can include the Bank Select messages prior to the PC message, either just the Lease Signficant Byte or both the LSB & MSB.
- Pass through of Sync/Start/Stop messages from USB to the Serial MIDI connector.

- Firmware can be loaded through the normal DFU update process.
- Uses a section of the EEPROM that the standard MeloAudio firmware doesn't (at least as I write this.)  So it's possible to reload firmwares without effecting settings.
- Provides SYSEX tools for downloading and uploading both the configuration section for this firmware, and to completely backup and restore the eeprom.

# Still to come
- Expression Pedal inputs
- The battery management has not been considered yet.  Not sure if it even works on batteries with this.
- Plenty of code tidying to be done
- Plenty of testing needed
- Needs documentation.


# Configuration
The basic configuration idea, is you use a spreadsheet template to create a configuration CSV file.  Here's a Public visable copy of a test google doc sheet I'm using.
This has some conditional formating and layout that makes choosing commands quite straight forward.
https://docs.google.com/spreadsheets/d/10smgMXW7wyQpB8cjfMVDMhDkW0gWgf0O7VTku3-jU90/edit#gid=0

The downloaded (or "Save As" in excel et al) CSV file is then passed to Convert_CSV_To_Config_Binary.py, which converts the CSV file into a binary called config_image.bin.
A second tool, Write_Settings_To_Eeprom.py, will load this binary file, write the eeprom, then reset the MIDI Commander to load the new settings.
