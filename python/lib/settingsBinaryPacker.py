GLOBAL_SETTINGS_CHANNEL = 0
GLOBAL_SETTINGS_REALTIME_PASS = 1


def pack_global_settings(df):
    # global settings will be 32 bytes long (bit of pluck as to how much is
    # needed out of the 128 bytes)
    bin_list = [0] * 16
    bin_list[GLOBAL_SETTINGS_CHANNEL] = \
        int(df.loc['MIDI_Channel', 'Value']) & 0xF
    if 'Y' in df.loc['RealTime_Passthrough', 'Value']:
        bin_list[GLOBAL_SETTINGS_REALTIME_PASS] = 0x1
    # print('{:8.8}'.format(df.loc['ConfigName'].Value))
    bin_list += ('{:16.16}'.format(df.loc['ConfigName'].Value)).encode('ASCII')

    return bin_list


def pack_bank_strings(df):
    bin_list = []
    for index, row in df.iterrows():
        # Pack the bank info. The large name is 4 bytes and the small string is
        # 8 bytes. In case of an empty string, the value read from the CSV is
        # nan.
        large_name = str(row['Bank_Name_Large'])
        small_name = str(row['Bank_Info_Small'])
        if large_name == 'nan':
            large_name = ''
        if small_name == 'nan':
            small_name = ''
        bin_list += ('{:4.4}'.format(large_name)).encode('ASCII')
        bin_list += ('{:8.8}'.format(small_name)).encode('ASCII')

    return bin_list
