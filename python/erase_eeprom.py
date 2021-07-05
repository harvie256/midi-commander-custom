import mido

MIDI_MANUF_ID = 0x7D

ERASE_EEPROM = 52

midi_inputs = [x for x in mido.get_input_names() if 'STM' in x]
midi_outputs = [x for x in mido.get_output_names() if 'STM' in x]

if len(midi_inputs) == 0:
    print('no input found')
    exit()

if len(midi_outputs) == 0:
    print('no outputs found')
    exit()


inport = mido.open_input(midi_inputs[0])
outport = mido.open_output(midi_outputs[0])

outmsg = mido.Message('sysex', data=[MIDI_MANUF_ID, ERASE_EEPROM, 0x42, 0x24])
outport.send(outmsg)
inmsg = inport.receive()

print(inmsg.hex())

inport.close()
outport.close()


