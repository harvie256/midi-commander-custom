/*
 * eeprom_midi_settings.h
 *
 *  Created on: 5 Jul 2021
 *      Author: derry
 */

#ifndef INC_EEPROM_MIDI_SETTINGS_H_
#define INC_EEPROM_MIDI_SETTINGS_H_

void eeprom_load_settings(void);

extern uint8_t *pSwitchCmds;
extern uint8_t *pGlobalSettings;
extern uint8_t *pBankStrings;


#define MIDI_ROM_CMD_SIZE	(4)
#define MIDI_ROM_KEY_STRIDE	(3*MIDI_ROM_CMD_SIZE)

#endif /* INC_EEPROM_MIDI_SETTINGS_H_ */
