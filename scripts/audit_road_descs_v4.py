import os
import re

def strip_ansi(text):
    text = text.rstrip('~')
    text = re.sub(r'`.', '', text)
    text = re.sub(r'\^.', '', text)
    text = re.sub(r'&[0-9]+;?', '', text)
    return text.strip()

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
        flags_line_raw = block[desc_end_pos+1:].strip().split('\n')
        if not flags_line_raw: continue
        flags_line = flags_line_raw[0].split()
        if len(flags_line) < 3: continue
        sector = int(flags_line[2])
        
        if sector == 11:
            desc_match = re.search(r'~.*?\n(.*?)~', block, re.MULTILINE | re.DOTALL)
            if not desc_match: continue
            raw_desc = desc_match.group(1)
            # Normalize whitespace for multi-line matches
            desc = " ".join(strip_ansi(raw_desc).lower().split())
            
            # Check for bad patterns in road descriptions
            distance_patterns = [
                'roads can be seen', 'road can be seen', 'see the road', 
                'see a road', 'road lies', 'distant road', 
                'smudge of road', 'see roads'
            ]
            found_dist = [p for p in distance_patterns if p in desc]
            
            # 2. Absence of being ON the road
            mentions_road = any(kw in desc for kw in ['road', 'way', 'path', 'highway', 'paving', 'stones', 'traveler'])
            
            if found_dist:
                bad_descriptions.append(f"VNUM: {vnum} Zone: {z} - Observer text: {found_dist}")
            elif not mentions_road:
                bad_descriptions.append(f"VNUM: {vnum} Zone: {z} - No road mention")

print(f"Found {len(bad_descriptions)} bad road descriptions.")
for issue in bad_descriptions:
    print(issue)
