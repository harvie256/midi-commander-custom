import io
import pandas as pd
import cmdBinaryPacker as cbp
import settingsBinaryPacker as sbp
import sys

inputFile = sys.argv[1]

with open(inputFile, 'r') as f:
    raw_content = f.readlines()

def remove_comments(content):
    # Discard all comment lines
    no_comments = []
    for l in raw_content:
        if "#" not in l:
            no_comments.append(l)
    return no_comments
        
no_comments = remove_comments(raw_content)

# Split into individual table sections
title_lines = []
for i, l in enumerate(no_comments):
    if '*' in l:
        title_lines.append((l.replace(',',' ').strip(' *'), i))


df_dic = {}
for i,tline in enumerate(title_lines):
    start_line = tline[1] + 1
    if(i == len(title_lines) -1):
        end_line = len(no_comments)
    else:
        end_line = title_lines[i+1][1]
    frame_lines = no_comments[start_line:end_line]
    df = pd.read_csv(io.StringIO('\n'.join(frame_lines)), delimiter=',').dropna(how='all')
    df.drop(df.columns[df.columns.str.contains('unnamed',case = False)],axis = 1, inplace=True)
    df_dic[tline[0].strip()] = df
    
# Setup the columns in the Button_Settings table
df_dic['Button_Settings'].set_index(['Bank_Number','Button_Identifier'], inplace=True)
df_dic['Global_Settings'].set_index(['Label'], inplace=True)
df_dic['Bank_Naming'].set_index(['Bank_Number'], inplace=True)

memory_bytes_list = []
memory_bytes_list += sbp.pack_global_settings(df_dic['Global_Settings'])
memory_bytes_list += sbp.pack_bank_strings(df_dic['Bank_Naming'])

for index, row in df_dic['Button_Settings'].iterrows():
    memory_bytes_list += cbp.pack_row(row)

# dump out to a file
memory_bytes = bytes(memory_bytes_list)
with open('config_image.bin', 'wb') as f:
    f.write(memory_bytes)

# File should be 896 bytes long
    