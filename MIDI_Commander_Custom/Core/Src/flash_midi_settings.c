/*
 * flash_midi_settings.c
 *
 *  Created on: 12 Jul 2021
 *      Author: D Harvie
 */

#include "main.h"
#include "flash_midi_settings.h"


#define FLASH_SETTINGS_OFFSET	(1024*128)
#define FLASH_SETTINGS_START	(FLASH_BASE + FLASH_SETTINGS_OFFSET)

#define FLASH_SETTINGS_NO_PAGES	(3)

uint8_t *pGlobalSettings = (uint8_t*)FLASH_SETTINGS_START;
uint8_t *pBankStrings = (uint8_t*)FLASH_SETTINGS_START+32;
uint8_t *pSwitchCmds = (uint8_t*)FLASH_SETTINGS_START+32+96;


void flash_settings_erase(void){
	// Erase flash sectors containing the settings
	// This must be done before re-writing them.

	uint32_t pageError;

	FLASH_EraseInitTypeDef eraseInit ={
			.TypeErase = FLASH_TYPEERASE_PAGES,
			.Banks = FLASH_BANK_1,
			.PageAddress = FLASH_SETTINGS_START,
			.NbPages = FLASH_SETTINGS_NO_PAGES
	};

	HAL_FLASH_Unlock();

	HAL_StatusTypeDef status = HAL_FLASHEx_Erase(&eraseInit, &pageError);

	HAL_FLASH_Lock();

	if(status != HAL_OK){
		// TODO: Display a message of the page that's in error
		Error("Flash erase error");
	}

}


void flash_settings_write(uint8_t* data, uint32_t offset){
	uint32_t flash_address = offset + FLASH_SETTINGS_START;

	HAL_FLASH_Unlock();

	// Programming 16bytes, so 8 iterations of 16bit
	for(int i=0; i<8; i++){
		uint16_t write_data = data[2*i] + (data[2*i+1] << 8);
		HAL_StatusTypeDef status = HAL_FLASH_Program(FLASH_TYPEPROGRAM_HALFWORD, flash_address + 2*i, write_data);
		if(status != HAL_OK){
			Error("Flash write error");
		}
	}

	HAL_FLASH_Lock();

}
