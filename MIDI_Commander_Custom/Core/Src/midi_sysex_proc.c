/*
 * midi_sysex_proc.c
 *
 *  Created on: 3 Jul 2021
 *      Author: Derryn Harvie
 */

#include "main.h"
#include "usbd_midi_if.h"

extern I2C_HandleTypeDef hi2c1;

#define DUMP_EEPROM 		0x10
#define DUMP_EEPROM_RESP	0x11

void dump_eeprom_to_sysex(void);

uint8_t message_buffer[64];

/* This device will only receive sysex messages over the USB port.
 * From a data integrity sense, this means it's already been unpacked
 * from a transport system with error correction coding.
 *
 * So while it might seem remiss to not bother with CRCs, it's already done
 * at a lower level in the protocol stack.
 *
 * Sysex message format will be.
 * Start byte - 0xF0
 * End byte - 0x7F
 *
 * [1] - message type ID
 * [2] - message length (in bytes, count starting at the next byte (3) and not including the end byte
 *
 *
 *
 *
 */
void midi_process_sysex_msg(uint8_t* pBuf, uint16_t length){
	__NOP();
	switch(pBuf[1]){
	case DUMP_EEPROM:
		dump_eeprom_to_sysex();
		break;
	default:
		break;
	}

}

/*
 * Loop through the EEPROM sending the contents as Sysex messages
 * 32 bytes at a time.
 *
 */

void dump_eeprom_to_sysex(void){
	uint8_t eeprom_address;

	message_buffer[0] = 0x8;
	message_buffer[1] = 0xF0; //SysEx message
	message_buffer[2] = DUMP_EEPROM_RESP; // message ID
	message_buffer[3] = 32; // length
	message_buffer[36] = 0x7F; // SysEx message terminator

	eeprom_address = 0xA0 + (0 << 1);
	//HAL_I2C_Mem_Read(&hi2c1, eeprom_address, 0, 8, message_buffer+4, 32, 10);
	MIDI_DataTx(message_buffer, 37);

//	for(int block = 0; block < 4; block ++){
//		eeprom_address = 0xA0 + (block << 1);
//		for(int i=0; i<8; i++){
//			HAL_I2C_Mem_Read(&hi2c1, eeprom_address, (32*i), 8, message_buffer+3, 32, 10);
//			MIDI_DataTx(message_buffer, 32+4);
//		}
//	}

}
