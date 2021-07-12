import mido
import time

MIDI_MANUF_ID = 0x7D

ERASE_FLASH = 52
WRITE_FLASH = 54
SYSEX_CMD_RESET	= 60


File_To_Write = r"D:\midi-commander-custom\python\config_image.bin"

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

# Erase Flash settings pages
print('Erasing Flash Settings')
outmsg = mido.Message('sysex', data=[MIDI_MANUF_ID, ERASE_FLASH, 0x42, 0x24])
outport.send(outmsg)

# Wait for response
time.sleep(0.05)
inmsg = inport.receive()
print('Erase Complete')


with open(File_To_Write, 'rb') as f:
    flash_contents = bytes(f.read())

no_chunks = int(len(flash_contents)/16)
for x in range(0, no_chunks):
    print('Writing Flash Chunk: ', x+1, '/', no_chunks)
    
    flash_chunk_low_byte = x & 0x7F
    flash_chunk_high_byte = (x >> 7) & 0x7F
    
    outmsg = mido.Message('sysex', data=[MIDI_MANUF_ID, WRITE_FLASH, flash_chunk_high_byte, flash_chunk_low_byte])
    
    
    for i in range(0, 16):
        outmsg.data += [flash_contents[x*16 + i] >> 4]
        outmsg.data += [flash_contents[x*16 + i] & 0xF]

    outport.send(outmsg)
    inmsg = inport.receive()
    time.sleep(0.01)


print('Finshed, reseting device...')

outmsg = mido.Message('sysex', data=[MIDI_MANUF_ID, SYSEX_CMD_RESET])
outport.send(outmsg)


inport.close()
outport.close()
