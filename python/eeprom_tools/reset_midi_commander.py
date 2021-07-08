#
#   This scrip just loads the alt firmware configuration section
#   of the EEPROM.  This shouldn't effect the meloaudio firmware
#   settings, at least when this was written.  No garrentees!!!!
#
#   Make sure you've got a backup of your complete EEPROM 
#   before loading anything new!
#

import mido

MIDI_MANUF_ID = 0x7D

SYSEX_CMD_RESET	= (60)


midi_outputs = [x for x in mido.get_output_names() if 'STM' in x]

if len(midi_outputs) == 0:
    print('no outputs found')
    exit()


outport = mido.open_output(midi_outputs[0])

print('Reseting device...')

outmsg = mido.Message('sysex', data=[MIDI_MANUF_ID, SYSEX_CMD_RESET])
outport.send(outmsg)

outport.close()
