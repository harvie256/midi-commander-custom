import mido
import time

MIDI_MANUF_ID = 0x7D

WRITE_EEPROM = 54

File_To_Write = r"D:\midi-commander-custom\python\config_image_06-07-2021_17-22-59"

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

with open(File_To_Write, 'rb') as f:
    eeprom_contents = bytes(f.read(0x380))

start_chunk = int(128/16)
no_chunks = int(1024/16)
for x in range(start_chunk, no_chunks):
    print('Writing EEPROM Page: ', x+1, '/', no_chunks)
    outmsg = mido.Message('sysex', data=[MIDI_MANUF_ID, WRITE_EEPROM, x])
    
    
    for i in range(0, 16):
        outmsg.data += [eeprom_contents[(x-start_chunk)*16 + i] >> 4]
        outmsg.data += [eeprom_contents[(x-start_chunk)*16 + i] & 0xF]

    outport.send(outmsg)
    inmsg = inport.receive()
    time.sleep(0.01)


print('Finshed')

inport.close()
outport.close()