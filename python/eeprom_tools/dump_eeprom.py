import mido
import time
from datetime import datetime

MIDI_MANUF_ID = 0x7D

DUMP_EEPROM = 50

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
combinedPacket = []

for eeprom_page in range(0, 64):
    print('Page: ', eeprom_page, '/63')

    outmsg = mido.Message('sysex', data=[MIDI_MANUF_ID, DUMP_EEPROM, eeprom_page])
    outport.send(outmsg)
    inmsg = inport.receive()
    time.sleep(0.01)
    
    for x in range(0, 16):
        offset = (2*x)+3
    
        byte = inmsg.data[offset] << 4
        byte += inmsg.data[offset+1]
        combinedPacket.append(byte)

inport.close()
outport.close()

    
dt_string = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")

eeprom_content = bytes(combinedPacket)
with open('eeprom_' + dt_string, 'wb') as f:
    f.write(eeprom_content)

