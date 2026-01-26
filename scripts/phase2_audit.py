import os
import re

def strip_ansi(text):
    text = text.rstrip('~')
    text = re.sub(r'`.', '', text)
    text = re.sub(r'\^.', '', text)
    text = re.sub(r'&[0-9]+;?', '', text)
    return text.strip()

def parse_wld_file(wld_file):
    with open(wld_file, 'r', encoding='latin-1') as f:
        content = f.read()
    
    rooms = {}
    blocks = re.split(r'^#(\d+)', content, flags=re.MULTILINE)[1:]
    for i in range(0, len(blocks), 2):
        vnum = int(blocks[i])
        block = blocks[i+1]
        
        name_match = re.search(r"^(.*?)~", block, re.MULTILINE | re.DOTALL)
        name = strip_ansi(name_match.group(1)) if name_match else ""
        
        desc_match = re.search(r"~.*?\n(.*?)~", block, re.MULTILINE | re.DOTALL)
        desc = strip_ansi(desc_match.group(1)) if desc_match else ""
        
        desc_end_pos = block.find('~', block.find('~') + 1)
        if desc_end_pos == -1: continue
        
        lines_after_desc = block[desc_end_pos+1:].strip().split('\n')
        if not lines_after_desc: continue
        
        flags_line = lines_after_desc[0].split()
        sector = int(flags_line[2]) if len(flags_line) > 2 else -1
        
        exits = {}
        d_matches = re.finditer(r"^D(\d+)\n.*?\n.*?\n(\d+) (\d+) (\d+)", block, re.MULTILINE)
        for dm in d_matches:
            exits[int(dm.group(1))] = int(dm.group(4))
            
        rooms[vnum] = {
            'vnum': vnum,
            'name': name,
            'desc': desc,
            'sector': sector,
            'exits': exits,
            'zone': vnum // 100
        }
    return rooms

def audit_overland_rooms(all_rooms):
    issues = []
    
    hallucination_map = {
        539: ["Aringill"],
        509: ["Aringill"],
        540: ["Camelyn"] # Spelling error common in history
    }

    for vnum, room in all_rooms.items():
        # Skip Road (11) and River (6) as they were handled in Phase 1
        if room['sector'] in [6, 11]:
            continue
            
        name_lower = room['name'].lower()
        desc_lower = room['desc'].lower()
        
        # 1. Rule NP1: "Road" in non-road room
        if "road" in name_lower:
            is_adj_road = any(all_rooms.get(dest, {}).get('sector') == 11 for dest in room['exits'].values())
            if not is_adj_road:
                issues.append(f"VNUM: {vnum} [S:{room['sector']}] [NP1] Name '{room['name']}' contains 'Road' but not adjacent to any Road (11)")
            elif not ("near" in name_lower or "along" in name_lower or "by the" in name_lower or "towards" in name_lower):
                issues.append(f"VNUM: {vnum} [S:{room['sector']}] [NP1] Name '{room['name']}' needs qualifier (e.g. 'Near the Road')")

        # 2. Rule NP2: "River" or river name in non-river room
        river_names = ["erinin", "luan", "alguenya", "gaelin"]
        has_river_ref = "river" in name_lower or any(rn in name_lower for rn in river_names)
        if has_river_ref:
            is_adj_river = any(all_rooms.get(dest, {}).get('sector') == 6 for dest in room['exits'].values())
            if not is_adj_river:
                issues.append(f"VNUM: {vnum} [S:{room['sector']}] [NP2] Name '{room['name']}' refers to river but not adjacent to any River (6)")

        # 3. Rule DP1: Generic descriptions
        generic_patterns = ["vast world stretches out", "proper description", "change me", "far off road", "smudge of road"]
        for p in generic_patterns:
            if p in desc_lower:
                issues.append(f"VNUM: {vnum} [S:{room['sector']}] [DP1] Generic description: contains '{p}'")
                break

        # 4. Rule DP2: Geographical Hallucinations
        zone_hallucinations = hallucination_map.get(room['zone'], [])
        for h in zone_hallucinations:
            if h.lower() in desc_lower or h.lower() in name_lower:
                issues.append(f"VNUM: {vnum} [S:{room['sector']}] [DP2] Hallucination: refers to '{h}' in Zone {room['zone']}")

    return issues

def main():
    wld_dir = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld"
    zones = [468, 469, 508, 509, 537, 538, 539, 540, 567, 568, 569, 570, 607, 608, 609, 610, 638, 639, 640]
    
    all_rooms = {}
    for z in zones:
        wld_file = os.path.join(wld_dir, f"{z}.wld")
        if os.path.exists(wld_file):
            all_rooms.update(parse_wld_file(wld_file))

    issues = audit_overland_rooms(all_rooms)
    
    with open("/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/docs/ubermap/phase2_audit_report_raw.txt", "w") as f:
        for issue in sorted(issues):
            f.write(issue + "\n")
            
    print(f"Phase 2 audit report generated with {len(issues)} issues.")

if __name__ == "__main__":
    main()
