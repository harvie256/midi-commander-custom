

def pack_global_settings(df):
    bin_list = [0] * 32 # global settings will be 32 bytes long (bit of pluck as to how much is needed out of the 128 bytes)
    bin_list[0] = int(df.loc['MIDI_Channel','Value']) & 0xF
    if 'Y' in df.loc['RealTime_Passthrough','Value']:
        bin_list[1] = 0x1
    
    return bin_list

def pack_bank_strings(df):
    bin_list = []
    for index, row in df.iterrows():
        # Pack the 4 byte name
        bin_list += ('{:4.4}'.format(row['Bank_Name_Large'])).encode('ASCII')
        bin_list += ('{:8.8}'.format(row['Bank_Info_Small'])).encode('ASCII')
        
    return bin_list
