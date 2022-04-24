/*
 * switch_router.c
 *
 *  Created on: 8 Jul 2021
 *      Author: D Harvie
 */
#include "main.h"
#include "midi_defines.h"
#include "midi_cmds.h"
#include "flash_midi_settings.h"
#include "display.h"

/*
 * Creating some constant arrays for the switches that can be scanned and handled
 * in a loop to simplify code and reduce duplication;
 */
typedef struct {
	GPIO_TypeDef *sw_gpio_port;
	uint16_t sw_gpio_pin;
	volatile uint16_t *pSwChangeState;
	GPIO_TypeDef *led_gpio_port;
	uint16_t led_gpio_pin;
	uint8_t switch_toggle_state; // Each bit will be a flag for pages 0-7
	uint8_t led_cmd_toggle;
} sw_t;

typedef struct {
	uint32_t systick_timout;
	uint8_t *pRomCmd;
} delayed_cmd_t;

#define SW_PORTA_MASK (SW_1_Pin | SW_2_Pin | SW_E_Pin | SW_D_Pin | SW_C_Pin)
#define SW_PORTB_MASK (SW_A_Pin | SW_3_Pin | SW_4_Pin | SW_5_Pin)
#define SW_PORTC_MASK (SW_B_Pin)

uint16_t port_A_previous_state = SW_PORTA_MASK; // All pins will be high un-pressed
volatile uint16_t port_A_switches_changed = 0;
uint16_t port_B_previous_state = SW_PORTB_MASK; // All pins will be high un-pressed
volatile uint16_t port_B_switches_changed = 0;
uint16_t port_C_previous_state = SW_PORTC_MASK; // All pins will be high un-pressed
volatile uint16_t port_C_switches_changed = 0;

volatile uint8_t debounce_counter = 0;

extern uint8_t f_sys_config_complete;

uint8_t switch_current_page = 0;

sw_t a_sw_obj[] = {
		{ .sw_gpio_port = SW_1_GPIO_Port, .sw_gpio_pin = SW_1_Pin, .pSwChangeState = &port_A_switches_changed, .led_gpio_port = LED_1_GPIO_Port, .led_gpio_pin = LED_1_Pin, .switch_toggle_state = 0},
		{ .sw_gpio_port = SW_2_GPIO_Port, .sw_gpio_pin = SW_2_Pin, .pSwChangeState = &port_A_switches_changed, .led_gpio_port = LED_2_GPIO_Port, .led_gpio_pin = LED_2_Pin, .switch_toggle_state = 0},
		{ .sw_gpio_port = SW_3_GPIO_Port, .sw_gpio_pin = SW_3_Pin, .pSwChangeState = &port_B_switches_changed, .led_gpio_port = LED_3_GPIO_Port, .led_gpio_pin = LED_3_Pin, .switch_toggle_state = 0},
		{ .sw_gpio_port = SW_4_GPIO_Port, .sw_gpio_pin = SW_4_Pin, .pSwChangeState = &port_B_switches_changed, .led_gpio_port = LED_4_GPIO_Port, .led_gpio_pin = LED_4_Pin, .switch_toggle_state = 0},

		{ .sw_gpio_port = SW_A_GPIO_Port, .sw_gpio_pin = SW_A_Pin, .pSwChangeState = &port_B_switches_changed, .led_gpio_port = LED_A_GPIO_Port, .led_gpio_pin = LED_A_Pin, .switch_toggle_state = 0},
		{ .sw_gpio_port = SW_B_GPIO_Port, .sw_gpio_pin = SW_B_Pin, .pSwChangeState = &port_C_switches_changed, .led_gpio_port = LED_B_GPIO_Port, .led_gpio_pin = LED_B_Pin, .switch_toggle_state = 0},
		{ .sw_gpio_port = SW_C_GPIO_Port, .sw_gpio_pin = SW_C_Pin, .pSwChangeState = &port_A_switches_changed, .led_gpio_port = LED_C_GPIO_Port, .led_gpio_pin = LED_C_Pin, .switch_toggle_state = 0},
		{ .sw_gpio_port = SW_D_GPIO_Port, .sw_gpio_pin = SW_D_Pin, .pSwChangeState = &port_A_switches_changed, .led_gpio_port = LED_D_GPIO_Port, .led_gpio_pin = LED_D_Pin, .switch_toggle_state = 0}
};

#define MAX_DELAYED_CMDS (32)

delayed_cmd_t delayed_cmds[MAX_DELAYED_CMDS];


/*
 * This scans the switch ports each ms for changes in the systick interrupt context.
 * We can't use port interrupts, as some of the pins are on non-interrupt pins.
 *
 * Switch changes are then handled in the main loop.
 */
void sw_scan(void){

	if(!f_sys_config_complete){
		return;
	}

	if(debounce_counter){
		debounce_counter--;
		return;
	}

	/* PORTA input pins */
	uint16_t current_port_A = GPIOA->IDR & SW_PORTA_MASK;
	port_A_switches_changed |= current_port_A  ^ port_A_previous_state;
	port_A_previous_state = current_port_A;

	/* PORTB input pins */
	uint16_t current_port_B = GPIOB->IDR & SW_PORTB_MASK;
	port_B_switches_changed |= current_port_B  ^ port_B_previous_state;
	port_B_previous_state = current_port_B;

	/* PORTC input pins */
	uint16_t current_port_C = GPIOC->IDR & SW_PORTC_MASK;
	port_C_switches_changed |= current_port_C  ^ port_C_previous_state;
	port_C_previous_state = current_port_C;

	if(port_A_switches_changed | port_B_switches_changed | port_C_switches_changed){
		debounce_counter = 10; // 10ms debounce delay
		return;
	}

}

static inline uint8_t get_sw_toggle_state(sw_t *sw){
	return sw->switch_toggle_state & (1 << switch_current_page);
}

static inline void toggle_sw_state(sw_t *sw){
	sw->switch_toggle_state ^= (1 << switch_current_page);
}

uint8_t* get_rom_pointer(uint8_t page, uint8_t sw, uint8_t cmd){
	return pSwitchCmds + (MIDI_ROM_KEY_STRIDE * sw) + (MIDI_ROM_CMD_SIZE * cmd) + (MIDI_ROM_KEY_STRIDE * 8 * page);
}


void sw_led_init(void){
	// Scan all commands in EEPROM, and build the table of whether the LED should toggle with the switch, or be momentary
	for(int page=0; page<8; page++){
		for(int sw=0; sw<8; sw++){
			// Clear the toggle bit
			a_sw_obj[sw].led_cmd_toggle &= ~(1<<page);

			for(int cmd=0; cmd<MIDI_NUM_COMMANDS_PER_SWITCH; cmd++){
				uint8_t *pCmd = get_rom_pointer(page, sw, cmd);
				if(midiCmd_get_cmd_toggle(pCmd)){
					a_sw_obj[sw].led_cmd_toggle |= (1<<page);
				}
			}
		}
	}

	// Init all delayed cmds to off
	for(int i=0; i<MAX_DELAYED_CMDS; i++){
		delayed_cmds[i].systick_timout = UINT32_MAX;
	}

	// Init all the LEDs to the off state
	for(int i = 0; i<8; i++){
		HAL_GPIO_WritePin(a_sw_obj[i].led_gpio_port, a_sw_obj[i].led_gpio_pin, GPIO_PIN_SET);
	}
	HAL_GPIO_WritePin(LED_5_GPIO_Port, LED_5_Pin, GPIO_PIN_SET);
	HAL_GPIO_WritePin(LED_E_GPIO_Port, LED_E_Pin, GPIO_PIN_SET);


}


/*
 * Functions for the command duration, i.e. delay until switching a cmd/note/pb off.
 */
int get_available_delayed_cmd_slot(void){
	for(int i=0; i<MAX_DELAYED_CMDS; i++){
		if(delayed_cmds[i].systick_timout == UINT32_MAX){
			return i;
		}
	}

	return -1;
}

void handle_delayed_cmds(void){
	for(int i=0; i<MAX_DELAYED_CMDS; i++){
		if(delayed_cmds[i].systick_timout < HAL_GetTick()){
			uint8_t* pRom = delayed_cmds[i].pRomCmd;
			switch(*pRom & 0xF0){
			case CMD_PB_NIBBLE:
				midiCmd_send_pb_command_from_rom(pRom, MIDI_CONTROL_OFF);
			case CMD_NOTE_NIBBLE:
				midiCmd_send_note_command_from_rom(pRom, MIDI_CONTROL_OFF);
				break;
			default:
				break;
			}
			delayed_cmds[i].systick_timout = UINT32_MAX;
		}
	}
}

// Sets the cmd point to switch off and the delay timeout into the delayed cmds table
void set_cmd_duration_delay(uint8_t *pRom){
	int slot = get_available_delayed_cmd_slot();
	if(slot >= 0){
		delayed_cmds[slot].pRomCmd = pRom;
		delayed_cmds[slot].systick_timout = HAL_GetTick() + midiCmd_get_delay(pRom);
	}
}

void handle_cmd_sw_down(uint8_t *pRom, uint8_t toggleState){
	/*
	 * Assume success by default since this was the behavior before adding this status.
	 */
	int8_t status = 0;

	switch(*pRom & 0xF0){
	case CMD_PC_NIBBLE:
		status = midiCmd_send_pc_command_from_rom(pRom);
		break;
	case CMD_CC_NIBBLE:
		if(midiCmd_get_cmd_toggle(pRom)){
			status = midiCmd_send_cc_command_from_rom(pRom, toggleState);
		} else {
			// Not toggling, so set command and either set a duration or not
			status = midiCmd_send_cc_command_from_rom(pRom, MIDI_CONTROL_ON);
		}
		break;
	case CMD_PB_NIBBLE:
		if(midiCmd_get_cmd_toggle(pRom)){
			status = midiCmd_send_pb_command_from_rom(pRom, toggleState);
		} else {
			// Not toggling, so set command and either set a duration or not
			status = midiCmd_send_pb_command_from_rom(pRom, MIDI_CONTROL_ON);
			if(midiCmd_get_delay(pRom) != 0){
				set_cmd_duration_delay(pRom);
			}
		}
		break;
	case CMD_NOTE_NIBBLE:
		if(midiCmd_get_cmd_toggle(pRom)){
			status = midiCmd_send_note_command_from_rom(pRom, toggleState);
		} else {
			// Not toggling, so set command and either set a duration or not
			status = midiCmd_send_note_command_from_rom(pRom, MIDI_CONTROL_ON);
			if(midiCmd_get_delay(pRom) != 0){
				set_cmd_duration_delay(pRom);
			}
		}
		break;
	case CMD_START_NIBBLE:
		status = midiCmd_send_start_command();
		break;
	case CMD_STOP_NIBBLE:
		status = midiCmd_send_stop_command();
		break;
	default:
		break;
	}

	if (status == ERROR_BUFFERS_FULL) {
		Error("Buffers full");
 	}
}

void handle_cmd_sw_up(uint8_t *pRom, uint8_t toggleState){
	/*
	 * Assume success by default since this was the behavior before adding this status.
	 */
	int8_t status = 0;

	switch(*pRom & 0xF0){
	case CMD_PC_NIBBLE:
		break;
	case CMD_CC_NIBBLE:
		if(!midiCmd_get_cmd_toggle(pRom)){
			status = midiCmd_send_cc_command_from_rom(pRom, MIDI_CONTROL_OFF);
		}
		break;
	case CMD_PB_NIBBLE:
		if(!midiCmd_get_cmd_toggle(pRom)) {
			if(midiCmd_get_delay(pRom) == 0) {
				// No cmd duration delay, so immediately release
				status = midiCmd_send_pb_command_from_rom(pRom, MIDI_CONTROL_OFF);
			}
		}
		break;
	case CMD_NOTE_NIBBLE:
		if(!midiCmd_get_cmd_toggle(pRom)) {
			if(midiCmd_get_delay(pRom) == 0) {
				// No cmd duration delay, so immediately release
				status = midiCmd_send_note_command_from_rom(pRom, MIDI_CONTROL_OFF);
			}
		}
		break;
	case CMD_START_NIBBLE:
		break;
	case CMD_STOP_NIBBLE:
		break;
	default:
		break;
	}

	if (status == ERROR_BUFFERS_FULL) {
		Error("Buffers full");
 	}
}

void set_led(uint8_t sw_no, uint8_t state){
	GPIO_PinState pinState = (state) ? GPIO_PIN_RESET : GPIO_PIN_SET;
	HAL_GPIO_WritePin(a_sw_obj[sw_no].led_gpio_port, a_sw_obj[sw_no].led_gpio_pin, pinState);

}

void update_leds_on_bank_change(void){
	for(int i=0; i<8; i++){
		if(a_sw_obj[i].led_cmd_toggle & (1<<switch_current_page)){
			set_led(i,get_sw_toggle_state(&a_sw_obj[i]));
		} else {
			set_led(i,RESET);
		}
	}
}

void handle_switches(void){

	// The Command switches
	for(int i=0; i<8; i++){
		if(*a_sw_obj[i].pSwChangeState & a_sw_obj[i].sw_gpio_pin){
				*a_sw_obj[i].pSwChangeState &= ~a_sw_obj[i].sw_gpio_pin;

				if(!HAL_GPIO_ReadPin(a_sw_obj[i].sw_gpio_port, a_sw_obj[i].sw_gpio_pin)){
					// Switch Down
					toggle_sw_state(&a_sw_obj[i]);

					// Either toggle the LED, or set it if not toggling
					if(a_sw_obj[i].led_cmd_toggle & (1<<switch_current_page)){
						set_led(i,get_sw_toggle_state(&a_sw_obj[i]));
					} else {
						set_led(i,SET);
					}

					for(int j=0; j<MIDI_NUM_COMMANDS_PER_SWITCH; j++){
						handle_cmd_sw_down(pSwitchCmds + (MIDI_ROM_KEY_STRIDE * (i + switch_current_page*8)) + (MIDI_ROM_CMD_SIZE * j),
								get_sw_toggle_state(&a_sw_obj[i]));
					}
				}else {
					// Switch up
					// Clear the LED if it's not toggling.
					if(!(a_sw_obj[i].led_cmd_toggle & (1<<switch_current_page))){
						set_led(i, RESET);
					}

					for(int j=0; j<MIDI_NUM_COMMANDS_PER_SWITCH; j++){
						handle_cmd_sw_up(pSwitchCmds + (MIDI_ROM_KEY_STRIDE * (i + switch_current_page*8)) + (MIDI_ROM_CMD_SIZE * j),
								get_sw_toggle_state(&a_sw_obj[i]));
					}

				}
			}

	}

	handle_delayed_cmds();

	// The bank change switches
	if(port_A_switches_changed & SW_E_Pin){
		port_A_switches_changed &= ~SW_E_Pin;

		if(!HAL_GPIO_ReadPin(SW_E_GPIO_Port, SW_E_Pin)){
			// Bank Down
			HAL_GPIO_WritePin(LED_E_GPIO_Port, LED_E_Pin, RESET);

			if(switch_current_page > 0){
				switch_current_page--;
				update_leds_on_bank_change();
				display_setBankName(switch_current_page);
			}
		} else {
			HAL_GPIO_WritePin(LED_E_GPIO_Port, LED_E_Pin, SET);
		}
	}

	if(port_B_switches_changed & SW_5_Pin){
		port_B_switches_changed &= ~SW_5_Pin;

		if(!HAL_GPIO_ReadPin(SW_5_GPIO_Port, SW_5_Pin)){
			// Bank Down
			HAL_GPIO_WritePin(LED_5_GPIO_Port, LED_5_Pin, RESET);

			if(switch_current_page < 7){
				switch_current_page++;
				update_leds_on_bank_change();
				display_setBankName(switch_current_page);
			}
		} else {
			HAL_GPIO_WritePin(LED_5_GPIO_Port, LED_5_Pin, SET);
		}
	}
}

