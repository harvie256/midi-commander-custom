import mido
import time

MIDI_MANUF_ID = 0x7D

WRITE_EEPROM = 54

File_To_Write = r"D:\midi-commander-custom\python\eeprom_05-07-2021_14-58-31"

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
    eeprom_contents = bytes(f.read(1024))

no_chunks = int(1024/16)
for x in range(0, no_chunks):
    print('Writing EEPROM Page: ', x+1, '/', no_chunks)
    outmsg = mido.Message('sysex', data=[MIDI_MANUF_ID, WRITE_EEPROM, x])
    
    
    for i in range(0, 16):
        outmsg.data += [eeprom_contents[x*16 + i] >> 4]
        outmsg.data += [eeprom_contents[x*16 + i] & 0xF]

    # print(outmsg.hex())
    outport.send(outmsg)
    inmsg = inport.receive()
    time.sleep(0.01)


print('Finshed')

inport.close()
outport.close()