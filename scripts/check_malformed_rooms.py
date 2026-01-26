import os
import re

wld_dir = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld"
zones = [468, 469, 508, 509, 537, 538, 539, 540, 567, 568, 569, 570, 607, 608, 609, 610, 638, 639, 640]

for z in zones:
    wld_file = os.path.join(wld_dir, f"{z}.wld")
    if not os.path.exists(wld_file): continue
    
    with open(wld_file, 'r', encoding='latin-1') as f:
        content = f.read()
    
    # Each room block starts with #VNUM and should end with S on a new line before the next #VNUM or end of file
    blocks = re.split(r'^#(\d+)', content, flags=re.MULTILINE)[1:]
    for i in range(0, len(blocks), 2):
        vnum = int(blocks[i])
        block = blocks[i+1].strip()
        
        if not block.endswith('\nS') and not block.endswith('\r\nS') and not block == 'S':
            # Check if the block ends with S but has extra space
            if not block.rstrip().endswith('\nS'):
                print(f"Malformed block found at VNUM {vnum} in {z}.wld")
