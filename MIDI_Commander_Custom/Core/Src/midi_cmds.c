/*
 * midi_cmds.c
 *
 *  Created on: Jul 6, 2021
 *      Author: D Harvie
 */
#include "midi_cmds.h"
#include "main.h"
#include "flash_midi_settings.h"
#include "midi_defines.h"
#include "usbd_midi_if.h"
#include "ssd1306.h"

extern UART_HandleTypeDef huart2;

// The USB doesn't need a buffering arrangement at this level, as when a call is made to tx, the data is copied
// completely into the USB's own endpoint transmit buffers. Therefore a single array is declared here to use for
// assembling messages into before being passed to the USB stack.
uint8_t midi_usb_assembly_buffer[16];

/*
 * Serial buffer management.
 *
 * Because the midi serial port is relatively slow (compared to USB) and it has no inherent buffering in the stack beyond
 * the DMA transfer that is started, we're defining a series of "mailbox" type buffers that will be sent when something is
 * written to them. Since each push of a switch can potentially send MIDI_NUM_COMMANDS_PER_SWITCH commands as well as another
 * MIDI_NUM_COMMANDS_PER_SWITCH commands if not in toggle mode, then we need 2 * MIDI_NUM_COMMANDS_PER_SWITCH buffers.
 */
#define NO_BUFFERS (2 * MIDI_NUM_COMMANDS_PER_SWITCH)
#define BUFFER_SIZE (16)

// Implementing as a series of buffers
uint8_t midi_uart_out_buffer[NO_BUFFERS][BUFFER_SIZE];
uint8_t midi_uart_out_buffer_bytes_to_tx[NO_BUFFERS] = {0}; // Indicates that a buffer is ready to be sent, and therefore also can't be written to.
uint8_t last_transmitted_buffer = NO_BUFFERS -1; // When a buffer is given to the DMA, this is set with the buffer number.  That allows buffers to be sent in order.

// Note should only be called from critical section, not thread safe
static int8_t get_next_available_tx_buffer(void){
	// Starting at the last sent buffer, loop through and find the next available.
	for(int i=0; i<NO_BUFFERS; i++){
		uint8_t n = (last_transmitted_buffer + i + 1) % NO_BUFFERS;
		if(midi_uart_out_buffer_bytes_to_tx[n] == 0){
			return n;
		}
	}

	return -1;
}

uint8_t midiCmd_get_cmd_toggle(uint8_t *pRom){
// Toggle state is always stored in the most significant bit of the second cmd byte
	return *(pRom+1) & 0x80;
}

/*
 * Returns the delay time to note or pitch bend off in ms
 */
uint32_t midiCmd_get_delay(uint8_t *pRom){
	return (uint32_t)*(pRom+3) * 10;
}

void midi_serial_start_next_dma(void){
	uint8_t buffer_to_transmit = 0xFF;
	// Find the next buffer ready for transmit
	for(int i=0; i<NO_BUFFERS; i++){
		uint8_t n = (last_transmitted_buffer + i + 1) % NO_BUFFERS;
		if(midi_uart_out_buffer_bytes_to_tx[n] != 0){
			buffer_to_transmit = n;
			break;
		}
	}

	if(buffer_to_transmit < NO_BUFFERS){
		// We've found a valid buffer to transmit
		while(HAL_UART_Transmit_DMA(&huart2, midi_uart_out_buffer[buffer_to_transmit],
				midi_uart_out_buffer_bytes_to_tx[buffer_to_transmit]) != HAL_OK);
		last_transmitted_buffer = buffer_to_transmit;
	}

}

static void midi_serial_transmit(void){
	if(huart2.gState == HAL_UART_STATE_READY){
		// This means the UART is idle, so the next buffer needs to be loaded.
		midi_serial_start_next_dma();
	}

	// If the UART isn't ready, then it will currently be in a DMA transfer.
	// The DMA complete callback will then load the next buffer for transfer, so
	// nothing to be done.
}

void HAL_UART_TxCpltCallback(UART_HandleTypeDef *huart)
{
	if(huart->Instance == huart2.Instance){
		// last sent buffer is complete, start another transfer.
		midi_uart_out_buffer_bytes_to_tx[last_transmitted_buffer] = 0;
		midi_serial_start_next_dma();
	}
}

int8_t midiCmd_send_stop_command(void){
	__disable_irq();
	int8_t buffer_no = get_next_available_tx_buffer();
	if(buffer_no < 0){
		__enable_irq();
		return ERROR_BUFFERS_FULL;
	}

	uint8_t *serialBuf = &(midi_uart_out_buffer[buffer_no][0]);
	uint8_t *usbBuf = midi_usb_assembly_buffer;

	*(usbBuf++) = CIN_SINGLE_BYTE;
	*(usbBuf++) = 0xFC; // Start byte
	*(usbBuf++) = 0; // Pad
	*(usbBuf++) = 0; // Pad

	*serialBuf = 0xFC;
	midi_uart_out_buffer_bytes_to_tx[buffer_no] = 1;

	__enable_irq();

	uint8_t usb_bytes_to_tx = usbBuf - midi_usb_assembly_buffer;
	MIDI_DataTx(midi_usb_assembly_buffer, usb_bytes_to_tx);

	midi_serial_transmit();
	return 0;
}

/*
 * Send a single byte message just through to the serial midi port.
 * This is to transfer start/stop/sync messages through from the USB to the midi port
 */
void midiCmd_send_byte_serial(uint8_t byteMessage){
	__disable_irq();
	int8_t buffer_no = get_next_available_tx_buffer();
	if(buffer_no < 0){
		__enable_irq();
		return;
	}

	uint8_t *serialBuf = &(midi_uart_out_buffer[buffer_no][0]);
	*serialBuf = byteMessage;
	midi_uart_out_buffer_bytes_to_tx[buffer_no] = 1;
	__enable_irq();

	midi_serial_transmit();
}

int8_t midiCmd_send_start_command(void){
	__disable_irq();
	int8_t buffer_no = get_next_available_tx_buffer();
	if(buffer_no < 0){
		__enable_irq();
		return ERROR_BUFFERS_FULL;
	}

	uint8_t *serialBuf = &(midi_uart_out_buffer[buffer_no][0]);
	uint8_t *usbBuf = midi_usb_assembly_buffer;

	*(usbBuf++) = CIN_SINGLE_BYTE;
	*(usbBuf++) = 0xFA; // Start byte
	*(usbBuf++) = 0; // Pad
	*(usbBuf++) = 0; // Pad

	*serialBuf = 0xFA;
	midi_uart_out_buffer_bytes_to_tx[buffer_no] = 1;

	__enable_irq();

	uint8_t usb_bytes_to_tx = usbBuf - midi_usb_assembly_buffer;
	MIDI_DataTx(midi_usb_assembly_buffer, usb_bytes_to_tx);

	midi_serial_transmit();
	return 0;
}


int8_t midiCmd_send_pb_command_from_rom(uint8_t *pRom, uint8_t on_off){
	__disable_irq();
	int8_t buffer_no = get_next_available_tx_buffer();
	if(buffer_no < 0){
		__enable_irq();
		return ERROR_BUFFERS_FULL;
	}

	uint8_t *serialBuf = &(midi_uart_out_buffer[buffer_no][0]);
	uint8_t *usbBuf = midi_usb_assembly_buffer;

	*(usbBuf++) = CIN_PITCHBEND_CHANGE;
	*(usbBuf++) = 0xE0| (pRom[0] & 0xF); // Channel
	*(usbBuf++) = on_off ? (pRom[1] & 0x7F) : 0x0; // PB LSB
	*(usbBuf++) = on_off ? (pRom[2] & 0x7F) : (0X2000 >> 7) & 0X7f; // PB MSB

	memcpy(serialBuf, (usbBuf-3), 3);
	serialBuf += 3;

	midi_uart_out_buffer_bytes_to_tx[buffer_no] = serialBuf - &midi_uart_out_buffer[buffer_no][0];

	__enable_irq();

	uint8_t usb_bytes_to_tx = usbBuf - midi_usb_assembly_buffer;
	MIDI_DataTx(midi_usb_assembly_buffer, usb_bytes_to_tx);

	midi_serial_transmit();
	return 0;
}

int8_t midiCmd_send_note_command_from_rom(uint8_t *pRom, uint8_t on_off){
	__disable_irq();
	int8_t buffer_no = get_next_available_tx_buffer();
	if(buffer_no < 0){
		__enable_irq();
		return ERROR_BUFFERS_FULL;
	}

	uint8_t *serialBuf = &(midi_uart_out_buffer[buffer_no][0]);
	uint8_t *usbBuf = midi_usb_assembly_buffer;

	*(usbBuf++) = (on_off) ? CIN_NOTE_ON : CIN_NOTE_OFF;
	*(usbBuf) = (on_off) ? 0x90 : 0x80; // Note on/off
	*(usbBuf++) |= pRom[0] & 0xF; // Channel
	*(usbBuf++) = pRom[1] & 0x7F; // Note Number
	*(usbBuf++) = (on_off) ?  pRom[2] & 0x7F : 0; // Velocity

	memcpy(serialBuf, (usbBuf-3), 3);
	serialBuf += 3;

	midi_uart_out_buffer_bytes_to_tx[buffer_no] = serialBuf - &midi_uart_out_buffer[buffer_no][0];

	__enable_irq();

	uint8_t usb_bytes_to_tx = usbBuf - midi_usb_assembly_buffer;
	MIDI_DataTx(midi_usb_assembly_buffer, usb_bytes_to_tx);

	midi_serial_transmit();
	return 0;
}

int8_t midiCmd_send_cc_command_from_rom(uint8_t *pRom, uint8_t on_off){
	// Check switch off value is valid, else no off value will be sent
	if(!on_off){
		if(pRom[3] > 0x7F)
			return 0;
	}

	__disable_irq();
	int8_t buffer_no = get_next_available_tx_buffer();
	if(buffer_no < 0){
		__enable_irq();
		return ERROR_BUFFERS_FULL;
	}

	uint8_t *serialBuf = &(midi_uart_out_buffer[buffer_no][0]);
	uint8_t *usbBuf = midi_usb_assembly_buffer;

	uint8_t cc_number = pRom[1] & 0x7F; // CC Number
	uint8_t cc_value = (on_off) ?  pRom[2] & 0x7F : pRom[3] & 0x7F; // Value

	*(usbBuf++) = CIN_CONTROL_CHANGE;
	*(usbBuf++) = 0xB0 | (pRom[0] & 0xF); // CC and Channel
	*(usbBuf++) = cc_number;
	*(usbBuf++) = cc_value;

	memcpy(serialBuf, (usbBuf-3), 3);
	serialBuf += 3;

	midi_uart_out_buffer_bytes_to_tx[buffer_no] = serialBuf - &midi_uart_out_buffer[buffer_no][0];

	__enable_irq();

	uint8_t usb_bytes_to_tx = usbBuf - midi_usb_assembly_buffer;
	MIDI_DataTx(midi_usb_assembly_buffer, usb_bytes_to_tx);

	midi_serial_transmit();

	/*
	 * Displaying messages on screen likely involves a delay which can be
	 * detrimental on the timing of MIDI messages. So keep this commented and
	 * only use for debugging. Using the display here also hides issues with
	 * the serial transmission buffers. The delay in the display update allows
	 * serial transmission to finish before the next time we enter this function.
	 * So we never use multiple buffers at the same time and this can hide issues.
	 */
//	ssd1306_SetCursor(2, 10);
//	char msg[25];
//	sprintf(msg, "CC %d = %d", cc_number, cc_value);
//	ssd1306_WriteString(msg, Font_6x8, White);
//	ssd1306_UpdateScreen();

 	return 0;
}


int8_t midiCmd_send_pc_command_from_rom(uint8_t *pRom){
	__disable_irq();
	int8_t buffer_no = get_next_available_tx_buffer();
	if(buffer_no < 0){
		__enable_irq();
		return ERROR_BUFFERS_FULL;
	}

	uint8_t *serialBuf = &(midi_uart_out_buffer[buffer_no][0]);
	uint8_t *usbBuf = midi_usb_assembly_buffer;

	/*
	 * Bank select messages must be transmitted first, as
	 * the actual program change is only executed on the PC
	 * message.
	 */
	if(pRom[2] < 0x80){ // Bank Select MSB
		*(usbBuf++) = CIN_CONTROL_CHANGE;
		*(usbBuf++) = 0xB0 | (pRom[0] & 0xF);
		*(usbBuf++) = MIDI_PC_BANK_SELECT_MSB;
		*(usbBuf++) = pRom[2];

		memcpy(serialBuf, (usbBuf-3), 3);
		serialBuf += 3;
	}

	if(pRom[3] < 0x80){ // Bank Select LSB
		*(usbBuf++) = CIN_CONTROL_CHANGE;
		*(usbBuf++) = 0xB0 | (pRom[0] & 0xF);
		*(usbBuf++) = MIDI_PC_BANK_SELECT_LSB;
		*(usbBuf++) = pRom[3];

		memcpy(serialBuf, (usbBuf-3), 3);
		serialBuf += 3;
	}

	// The program change message
	*(usbBuf++) = CIN_PROGRAM_CHANGE;
	*(usbBuf++) = 0xC0 | (pRom[0] & 0xF);
	*(usbBuf++) = pRom[1] & 0x7F;
	*(usbBuf++) = 0; // must pad USB packets to 32b

	memcpy(serialBuf, (usbBuf-3), 2);
	serialBuf += 2;

	midi_uart_out_buffer_bytes_to_tx[buffer_no] = serialBuf - &midi_uart_out_buffer[buffer_no][0];

	__enable_irq();

	uint8_t usb_bytes_to_tx = usbBuf - midi_usb_assembly_buffer;
	MIDI_DataTx(midi_usb_assembly_buffer, usb_bytes_to_tx);

	midi_serial_transmit();
	return 0;
}
