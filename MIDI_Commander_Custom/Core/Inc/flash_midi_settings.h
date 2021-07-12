/*
 * flash_midi_settings.h
 *
 *  Created on: 12 Jul 2021
 *      Author: derry
 */

#ifndef INC_FLASH_MIDI_SETTINGS_H_
#define INC_FLASH_MIDI_SETTINGS_H_

#include "main.h"

extern uint8_t *pSwitchCmds;
extern uint8_t *pGlobalSettings;
extern uint8_t *pBankStrings;


#define MIDI_ROM_CMD_SIZE	(4)
#define MIDI_ROM_KEY_STRIDE	(3*MIDI_ROM_CMD_SIZE)

void flash_settings_erase(void);
void flash_settings_write(uint8_t* data, uint32_t offset);

#endif /* INC_FLASH_MIDI_SETTINGS_H_ */
