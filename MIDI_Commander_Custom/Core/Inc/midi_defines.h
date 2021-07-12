/*
 * midi_defines.h
 *
 *  Created on: 4 Jul 2021
 *      Author: D Harvie
 */

#ifndef INC_MIDI_DEFINES_H_
#define INC_MIDI_DEFINES_H_

/* Code Index Number Classifications */
// See page 16 of "USB Device Class Definition for MIDI Devices"
#define CIN_MISCELLANEOUS				(0x0)
#define CIN_CABLE_EVENTS				(0x1)
#define CIN_TWO_BYTE_SYSTEM_COMMON		(0x2)
#define CIN_THREE_BYTE_SYSTEM_COMMON	(0x3)
#define CIN_SYSEX_STARTS_OR_CONTINUES	(0x4)
#define CIN_SINGLE_BYTE_SYSTEM_COMMON	(0x5)
#define CIN_SYSEX_ENDS_WITH_FOLLOWING_SINGLE_BYTE	(0x5)
#define CIN_SYSEX_ENDS_WITH_FOLLOWING_TWO_BYTES		(0x6)
#define CIN_SYSEX_ENDS_WITH_FOLLOWING_THREE_BYTES	(0x7)
#define CIN_NOTE_OFF					(0x8)
#define CIN_NOTE_ON						(0x9)
#define CIN_POLY_KEYPRESS				(0xA)
#define CIN_CONTROL_CHANGE				(0xB)
#define CIN_PROGRAM_CHANGE				(0xC)
#define CIN_CHANNEL_PRESSURE			(0xD)
#define CIN_PITCHBEND_CHANGE			(0xE)
#define CIN_SINGLE_BYTE					(0xF)

#define MIDI_PC_BANK_SELECT_MSB	(0x00)
#define MIDI_PC_BANK_SELECT_LSB (0X20)

#define MIDI_CONTROL_ON		(1)
#define MIDI_CONTROL_OFF	(0)

// using the private use manufacturer ID
#define MIDI_MANUF_ID	(0x7D)

// SysEx commands for this device
#define SYSEX_CMD_ERASE_FLASH	(52) // must contain two bytes of 0x42 and 0x24 as check words.
#define SYSEX_RSP_ERASE_FLASH	(53) // zero length response to confirm success
#define SYSEX_CMD_WRITE_FLASH	(54) // first byte is the page address (16 byte pages), valid range 0-63.  Following 16 bytes are the data to write
#define SYSEX_RSP_WRITE_FLASH	(55) // zero length response to confirm write
#define SYSEX_CMD_RESET			(60) // Reset the device

#define SYSEX_START (0xF0)
#define SYSEX_END	(0xF7)

#define CMD_NO_CMD_NIBBLE	(0x00)
#define CMD_PC_NIBBLE		(0xC0)
#define CMD_CC_NIBBLE		(0xB0)
#define CMD_PB_NIBBLE		(0xE0)
#define CMD_NOTE_NIBBLE		(0x90)
#define CMD_START_NIBBLE	(0x10)
#define CMD_STOP_NIBBLE		(0x20)

#define GLOBAL_SETTINGS_CHANNEL (0)
#define GLOBAL_SETTINGS_REALTIME_PASS (1)

#endif /* INC_MIDI_DEFINES_H_ */
