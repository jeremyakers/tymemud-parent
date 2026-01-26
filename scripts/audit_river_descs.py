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

bad_river_descriptions = []

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
        
        if sector == 6: # River
            desc_match = re.search(r'~.*?\n(.*?)~', block, re.MULTILINE | re.DOTALL)
            if not desc_match: continue
            raw_desc = desc_match.group(1)
            desc = " ".join(strip_ansi(raw_desc).lower().split())
            
            # Contradictory keywords for a river
            road_terms = ['road', 'wagon', 'rut', 'paving', 'dust', 'hooves', 'boots', 'well-traveled way', 'way cuts through the land']
            found_road = [p for p in road_terms if p in desc]
            
            # Distance/Placeholder keywords
            distance_patterns = ['river can be seen', 'see the river', 'faint smudge', 'distant river']
            found_dist = [p for p in distance_patterns if p in desc]
            
            # Lack of water context
            water_terms = ['water', 'river', 'current', 'flow', 'hiss', 'lapping', 'wet', 'depth', 'bank', 'spans', 'erinin', 'luan', 'alguenya', 'gaelin']
            mentions_water = any(kw in desc for kw in water_terms)
            
            if found_road:
                bad_river_descriptions.append(f"VNUM: {vnum} Zone: {z} - Contradictory road text: {found_road}")
            elif found_dist:
                bad_river_descriptions.append(f"VNUM: {vnum} Zone: {z} - Observer text: {found_dist}")
            elif not mentions_water:
                bad_river_descriptions.append(f"VNUM: {vnum} Zone: {z} - No river/water mention")

print(f"Found {len(bad_river_descriptions)} bad river descriptions.")
for issue in bad_river_descriptions:
    print(issue)
