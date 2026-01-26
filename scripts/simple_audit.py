import os
import re

wld_dir = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld"
zones = [468, 469, 508, 509, 537, 538, 539, 540, 567, 568, 569, 570, 607, 608, 609, 610, 638, 639, 640]

for z in zones:
    wld_file = os.path.join(wld_dir, f"{z}.wld")
    if not os.path.exists(wld_file): continue
    with open(wld_file, 'r', encoding='latin-1') as f:
        content = f.read()
    
    rooms = re.split(r'^#(\d+)', content, flags=re.MULTILINE)[1:]
    for i in range(0, len(rooms), 2):
        vnum = int(rooms[i])
        block = rooms[i+1]
        
        # Check for sector 11
        # Match line like: zone_num a 11 ...
        if re.search(r'\n\d+ \w+ 11 ', block):
            # It's a road. Now check desc.
            # Get text between first and second ~
            m = re.search(r'~(.*?)~', block, re.DOTALL)
            if m:
                desc = m.group(1).lower()
                if 'smudge' in desc or 'faint' in desc:
                    print(f"VNUM: {vnum} [Road] Bad desc: {desc.strip()[:100]}")
        
        # Check for sector 6
        if re.search(r'\n\d+ \w+ 6 ', block):
            m = re.search(r'~(.*?)~', block, re.DOTALL)
            if m:
                desc = m.group(1).lower()
                if 'road' in desc or 'wagon' in desc:
                    print(f"VNUM: {vnum} [River] Bad desc: {desc.strip()[:100]}")
