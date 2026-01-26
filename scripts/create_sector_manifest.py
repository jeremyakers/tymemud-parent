#!/usr/bin/env python3
"""
Create a baseline sector manifest for all overland zones.
This file is used to detect unintended sector changes during the audit process.
"""
import os
import re

wld_dir = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld"
zones = [468, 469, 508, 509, 537, 538, 539, 540, 567, 568, 569, 570, 607, 608, 609, 610, 638, 639, 640]

def strip_ansi(text):
    text = text.rstrip('~')
    text = re.sub(r'`.', '', text)
    text = re.sub(r'\^.', '', text)
    text = re.sub(r'&[0-9]+;?', '', text)
    return text.strip()

print("VNUM\tZONE\tSECTOR\tNAME")

for z in zones:
    wld_file = os.path.join(wld_dir, f"{z}.wld")
    if not os.path.exists(wld_file):
        continue
    
    with open(wld_file, 'r', encoding='latin-1') as f:
        content = f.read()
    
    blocks = re.split(r'^#(\d+)', content, flags=re.MULTILINE)[1:]
    for i in range(0, len(blocks), 2):
        vnum = int(blocks[i])
        block = blocks[i+1]
        
        # Name
        name_match = re.search(r"^(.*?)~", block, re.MULTILINE | re.DOTALL)
        name = strip_ansi(name_match.group(1)) if name_match else "UNKNOWN"
        
        # Sector
        desc_end_pos = block.find('~', block.find('~') + 1)
        flags_line = block[desc_end_pos+1:].strip().split('\n')[0].split()
        sector = int(flags_line[2]) if len(flags_line) > 2 else -1
        
        print(f"{vnum}\t{z}\t{sector}\t{name}")
