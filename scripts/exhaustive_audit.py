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

issues = []

for z in zones:
    wld_file = os.path.join(wld_dir, f"{z}.wld")
    if not os.path.exists(wld_file): continue
    
    with open(wld_file, 'r', encoding='latin-1') as f:
        content = f.read()
    
    rooms = re.split(r'^#(\d+)', content, flags=re.MULTILINE)[1:]
    for i in range(0, len(rooms), 2):
        vnum = int(rooms[i])
        block = rooms[i+1]
        
        # Get name and desc
        parts = re.split(r'~', block)
        if len(parts) < 2: continue
        name_raw = parts[0].strip()
        name = strip_ansi(name_raw)
        desc_raw = parts[1].strip()
        desc = " ".join(strip_ansi(desc_raw).lower().split())
        
        # Get sector
        # The line after the second ~
        m = re.search(r'~.*?\n(.*)', block, re.DOTALL)
        if not m: continue
        flags_line = m.group(1).strip().split('\n')[0].split()
        if len(flags_line) < 3: continue
        sector = -1
        if flags_line[2].isdigit():
            sector = int(flags_line[2])
        elif len(flags_line) > 3 and flags_line[3].isdigit():
            sector = int(flags_line[3])
            
        if sector == -1: continue

        # 1. Road Sector (11) Audit
        if sector == 11:
            dist_terms = ['smudge', 'far off', 'can be seen', 'view of the road', 'sightline', 'imagine', 'faint']
            found_dist = [p for p in dist_terms if p in desc]
            
            mentions_road = any(kw in desc for kw in ['road', 'way', 'path', 'highway', 'paving', 'stones', 'traveler'])
            
            if found_dist and 'road' in desc: # "road can be seen"
                issues.append(f"VNUM: {vnum} [Road] - Observer text: {desc[:100]}")
            elif not mentions_road:
                issues.append(f"VNUM: {vnum} [Road] - No road mention: {desc[:100]}")
        
        # 2. River Sector (6) Audit
        if sector == 6:
            road_terms = ['road', 'wagon', 'rut', 'paving', 'dust', 'hooves', 'boots']
            found_road = [p for p in road_terms if p in desc]
            if found_road:
                issues.append(f"VNUM: {vnum} [River] - Contradictory road text {found_road}: {desc[:100]}")
            
            water_terms = ['water', 'river', 'current', 'flow', 'hiss', 'lapping', 'wet', 'depth', 'bank', 'spans', 'erinin', 'luan', 'alguenya', 'gaelin']
            mentions_water = any(kw in desc for kw in water_terms)
            if not mentions_water:
                issues.append(f"VNUM: {vnum} [River] - No water mention: {desc[:100]}")

        # 3. Hallucinations
        if 'caemlyn' in desc or 'capital' in desc:
            if vnum >= 46960 and vnum <= 46976: # Maradon road
                issues.append(f"VNUM: {vnum} [Maradon Road] - Incorrect Andor/Caemlyn mention")
            if vnum >= 46997 and vnum <= 50915: # Dragonmount road
                issues.append(f"VNUM: {vnum} [Dragonmount Road] - Incorrect Andor/Caemlyn mention")

        if 'aringill' in desc:
            if z in [468, 469, 508, 509, 539, 540]:
                if not any(kw in name.lower() for kw in ['aringill', 'road']):
                    issues.append(f"VNUM: {vnum} [Zone {z}] - Hallucination: Aringill mentioned in North")

with open("/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/docs/ubermap/exhaustive_desc_audit.txt", "w") as f:
    for issue in issues:
        f.write(issue + "\n")

print(f"Exhaustive audit complete. Found {len(issues)} description issues.")
