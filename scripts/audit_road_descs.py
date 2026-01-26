import os
import re

wld_dir = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld"
zones = [468, 469, 508, 509, 537, 538, 539, 540, 567, 568, 569, 570, 607, 608, 609, 610, 638, 639, 640]

bad_descriptions = []

for z in zones:
    wld_file = os.path.join(wld_dir, f"{z}.wld")
    if not os.path.exists(wld_file): continue
    
    with open(wld_file, 'r', encoding='latin-1') as f:
        content = f.read()
    
    rooms = re.split(r'^#(\d+)', content, flags=re.MULTILINE)[1:]
    for i in range(0, len(rooms), 2):
        vnum = int(rooms[i])
        block = rooms[i+1]
        
        # Get sector
        desc_end_pos = block.find('~', block.find('~') + 1)
        if desc_end_pos == -1: continue
        flags_line = block[desc_end_pos+1:].strip().split('\n')[0].split()
        if len(flags_line) < 3: continue
        sector = int(flags_line[2])
        
        if sector == 11:
            desc_match = re.search(r'~.*?\n(.*?)~', block, re.MULTILINE | re.DOTALL)
            if not desc_match: continue
            desc = desc_match.group(1).lower()
            
            # Check for bad patterns in road descriptions
            placeholders = ['smudge', 'far off', 'faint', 'imagine', 'sightline']
            found = [p for p in placeholders if p in desc]
            
            if found:
                bad_descriptions.append(f"VNUM: {vnum} Zone: {z} - Found bad terms: {found}")
            elif 'road' not in desc and 'way' not in desc and 'path' not in desc:
                bad_descriptions.append(f"VNUM: {vnum} Zone: {z} - Description does not mention road")

with open("/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/docs/ubermap/bad_road_descriptions.txt", "w") as f:
    for issue in bad_descriptions:
        f.write(issue + "\n")
    f.write(f"\nTotal Bad Road Descriptions Found: {len(bad_descriptions)}\n")

print(f"Audit complete. Found {len(bad_descriptions)} bad road descriptions.")
