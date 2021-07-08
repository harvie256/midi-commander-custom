/*
 * eeprom_midi_settings.c
 *
 *  Created on: 5 Jul 2021
 *      Author: D Harvie
 */

#include "main.h"

uint8_t eeprom_mirror[0x400];
uint8_t *pSwitchCmds;
uint8_t *pGlobalSettings;
uint8_t *pBankStrings;

extern I2C_HandleTypeDef hi2c1;

void eeprom_error(void){
	// TODO: display an error state.
	__NOP();
}

void eeprom_load_settings(void){
	uint16_t ee_byte_address = 0;
	// Load the complete EEPROM into RAM
	HAL_StatusTypeDef status = HAL_I2C_Mem_Read(&hi2c1, 0xA0 | ((ee_byte_address & 0x0300) >> 7), (ee_byte_address & 0xff), I2C_MEMADD_SIZE_8BIT, eeprom_mirror, 0x400, 100);
	if(status != HAL_OK){
		eeprom_error();
	}

	pGlobalSettings = eeprom_mirror + 128;
	pBankStrings = pGlobalSettings + 32;
	pSwitchCmds = pBankStrings + 96;
}
