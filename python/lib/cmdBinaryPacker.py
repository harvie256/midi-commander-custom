
CMD_NO_CMD_NIBBLE = 0x00
CMD_PC_NIBBLE = 0xC0
CMD_CC_NIBBLE = 0xB0
CMD_PB_NIBBLE = 0xE0
CMD_NOTE_NIBBLE = 0x90
CMD_START_NIBBLE = 0x10
CMD_STOP_NIBBLE = 0x20


# Standard command
# byte 1
# Upper 4 bits -> command types
# Lower 4 bits -> channel
# byte 2
# Most significant bit -> toggle control

def get_toggle_bit(toggle_str):
    if 'Y' in toggle_str:
        return 0x80
    else:
        return 0


# Program Change (or patch change) command, including back select
def cmd_pc(cmd):
    bank_select_low = int(cmd['BankSelect_(PC)']) & 0x7F
    if 'Y' in cmd['BankSelectHighByte_(PC)']:
        bank_select_high = (int(cmd['BankSelect_(PC)']) >> 7) & 0x7F
    else:
        bank_select_high = 0x80
    
    cmd_bytes = [
        CMD_PC_NIBBLE | int(cmd['Channel_(PC/CC/Note/PB)'] - 1), # Command and channel
        int(cmd['Number_(PC/CC/Note)']) & 0x7F, # Patch number
        bank_select_high,
        bank_select_low
        ]
    
    return cmd_bytes


def cmd_cc(cmd):
    cmd_bytes = [
        CMD_CC_NIBBLE | int(cmd['Channel_(PC/CC/Note/PB)'] - 1), # Command and channel
        int(cmd['Number_(PC/CC/Note)']) & 0x7F | \
            get_toggle_bit(cmd['Toggle_(CC/PB/Note)']), # command number & toggle
        int(cmd['OnValue_(CC/PB)']) & 0x7F,
        int(cmd['OffValue_(CC)'])
        ]
    return cmd_bytes


def cmd_note(cmd):
    cmd_bytes = [
        CMD_NOTE_NIBBLE | int(cmd['Channel_(PC/CC/Note/PB)'] - 1), # Command and channel
        int(cmd['Number_(PC/CC/Note)']) & 0x7F | \
            get_toggle_bit(cmd['Toggle_(CC/PB/Note)']), # note number & toggle
        int(cmd['Velocity_(Note)']) & 0x7F,
        int(cmd['Duration_(Note/PB)']) & 0x7F
        ]
    return cmd_bytes
    
    
def cmd_pb(cmd):
    # The pitch in the CSV file will be -8192 to 8191, this needs to be centered
    # around 0x2000
    
    if -8192 > cmd['OnValue_(CC/PB)'] > 8191:
        raise ValueError('PB outside of range: ', cmd['OnValue_(CC/PB)'])
    
    pitch = int(cmd['OnValue_(CC/PB)'] + 0x2000)
    
    pitch_LSB = pitch & 0x7F
    pitch_MSB = (pitch >> 7) & 0x7F 
    
    cmd_bytes = [
        CMD_PB_NIBBLE | int(cmd['Channel_(PC/CC/Note/PB)'] - 1), # Command and channel
        pitch_LSB | get_toggle_bit(cmd['Toggle_(CC/PB/Note)']), # high byte of value & toggle
        pitch_MSB,
        int(cmd['Duration_(Note/PB)']) & 0x7F
        ]
    return cmd_bytes


def cmd_start(cmd):
    return [CMD_START_NIBBLE, 0, 0, 0]

def cmd_stop(cmd):
    return [CMD_STOP_NIBBLE, 0, 0, 0]

def cmd_none(cmd):
    return [0,0,0,0]

cmd_route_table = {
    'PC': cmd_pc,
    'CC': cmd_cc,
    'Note': cmd_note,
    'PB': cmd_pb,
    'Start': cmd_start,
    'Stop':cmd_stop
    }

def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text

def pack_row(row):
    
    cmd_A = row.loc[row.index.str.startswith('A_')]
    cmd_A.index = cmd_A.index.str.replace('A_','')
    func_A = cmd_route_table.get(cmd_A['CommandType'], cmd_none)
    
    cmd_B = row.loc[row.index.str.startswith('B_')]
    cmd_B.index = cmd_B.index.str.replace('B_','')
    func_B = cmd_route_table.get(cmd_B['CommandType'], cmd_none)
    
    cmd_C = row.loc[row.index.str.startswith('C_')]
    cmd_C.index = cmd_C.index.str.replace('C_','')
    func_C = cmd_route_table.get(cmd_C['CommandType'], cmd_none)
    
    row_byte_list = func_A(cmd_A)
    row_byte_list += func_B(cmd_B)
    row_byte_list += func_C(cmd_C)

    return row_byte_list


    