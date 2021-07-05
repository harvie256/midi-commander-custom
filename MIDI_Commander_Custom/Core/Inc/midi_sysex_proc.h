/*
 * midi_sysex_proc.h
 *
 *  Created on: 3 Jul 2021
 *      Author: derry
 */

#ifndef INC_MIDI_SYSEX_PROC_H_
#define INC_MIDI_SYSEX_PROC_H_

void midi_process_sysex_msg(uint8_t* pBuf, uint16_t length);
void dump_eeprom_to_sysex(void);

#endif /* INC_MIDI_SYSEX_PROC_H_ */
