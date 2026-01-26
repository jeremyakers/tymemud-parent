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
        flags_line = block[desc_end_pos+1:].strip().split('\n')[0].split()
        sector = int(flags_line[2]) if len(flags_line) > 2 else -1
        
        exits = {}
        d_blocks = re.split(r'^D(\d+)', block, flags=re.MULTILINE)[1:]
        for j in range(0, len(d_blocks), 2):
            d_idx = int(d_blocks[j])
            d_content = d_blocks[j+1]
            coord_match = re.search(r'^(-?\d+) (-?\d+) (\d+)', d_content, re.MULTILINE)
            if coord_match:
                exits[d_idx] = int(coord_match.group(3))
            
        rooms[vnum] = {
            'vnum': vnum,
            'name': name,
            'desc': desc,
            'sector': sector,
            'exits': exits,
            'zone': vnum // 100
        }
    return rooms

def run_audit(wld_dir, zones):
    all_rooms = {}
    for z in zones:
        wld_file = os.path.join(wld_dir, f"{z}.wld")
        if os.path.exists(wld_file):
            all_rooms.update(parse_wld_file(wld_file))
            
    placeholder_keywords = ["builder~", "builder\\n", "maelyn", "online map", "change me", "proper description", "vast world stretches out"]
    direction_map = {0: "North", 1: "East", 2: "South", 3: "West", 6: "Northeast", 7: "Northwest", 8: "Southeast", 9: "Southwest"}
    
    hallucination_rules = [
        # Landmarks that should NOT be in certain zones
        ("Aringill", [468, 469, 508, 509, 537, 538, 539, 540], "Too far north for Aringill"),
        ("White Tower", [537, 538, 567, 568, 607, 608, 609, 610, 638, 639, 640], "Too far south/east for White Tower"),
        ("Topless Towers", [468, 469, 508, 509, 640, 610, 611, 570, 540], "Too far north/west for Topless Towers"),
        ("Caemlyn", [468, 469, 508, 509, 537, 538, 567, 568, 607, 638, 608, 609, 569], "Too far north/east for Caemlyn")
    ]

    issues = []
    
    for vnum, room in all_rooms.items():
        # Only audit overland scope rooms
        if room['zone'] not in [468, 469, 508, 509, 537, 538, 539, 540, 567, 568, 569, 570, 607, 608, 609, 610, 638, 639, 640]:
            continue

        # 1. Placeholder Detection
        for kw in placeholder_keywords:
            if kw in room['name'].lower() or kw in room['desc'].lower():
                issues.append(f"VNUM: {vnum} [S:{room['sector']}] Placeholder text found: '{kw}'")
                break
        
        # 2. Road Naming Truth (Sector 11)
        if room['sector'] == 11:
            name_clean = room['name'].lower()
            for d_idx, d_name in direction_map.items():
                if re.search(r'\b' + re.escape(d_name.lower()) + r'\b', name_clean):
                    dest = room['exits'].get(d_idx)
                    if not dest:
                        issues.append(f"VNUM: {vnum} [S:11] Name claims road runs {d_name}, but no exit in that direction")
                    else:
                        dest_room = all_rooms.get(dest)
                        if not dest_room or (dest_room['sector'] != 11 and dest != 50899):
                            # Allow "into the city" for gate rooms
                            if not ("into the city" in name_clean and dest_room and dest_room['sector'] in [1, 10]):
                                issues.append(f"VNUM: {vnum} [S:11] Name claims road runs {d_name}, but exit leads to non-road (S:{dest_room['sector'] if dest_room else '?'})")
            
            # Check for missing directions in name
            road_exits = []
            for d_idx, dest in room['exits'].items():
                dest_room = all_rooms.get(dest)
                if dest_room and (dest_room['sector'] == 11 or dest == 50899):
                    d_name = direction_map.get(d_idx)
                    if d_name and not re.search(r'\b' + re.escape(d_name.lower()) + r'\b', name_clean):
                        road_exits.append(d_name)
            if road_exits:
                issues.append(f"VNUM: {vnum} [S:11] Name missing road directions: {', '.join(road_exits)}")

        # 3. Hallucination Detection
        for kw, bad_zones, msg in hallucination_rules:
            if room['zone'] in bad_zones:
                if kw.lower() in room['desc'].lower() or kw.lower() in room['name'].lower():
                    # Check if it's a valid road name mentioning the endpoint
                    if not ("Road" in room['name'] and kw in room['name']):
                        issues.append(f"VNUM: {vnum} [Z:{room['zone']}] Hallucination: '{kw}' mentioned. {msg}")

        # 4. Sector 6 (River) naming truth
        if room['sector'] == 6:
            name_clean = room['name'].lower()
            if "road" in name_clean:
                issues.append(f"VNUM: {vnum} [S:6] Contradictory name: contains 'Road'")
            if "luan" in name_clean and vnum > 53946: # South of junction
                issues.append(f"VNUM: {vnum} [S:6] Incorrect name: 'Luan' mentioned south of junction")

    return issues

if __name__ == "__main__":
    wld_dir = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld"
    zones = [468, 469, 508, 509, 537, 538, 539, 540, 567, 568, 569, 570, 607, 608, 609, 610, 638, 639, 640, 13, 130, 16, 160, 52, 526, 62, 626]
    
    issues = run_audit(wld_dir, zones)
    for issue in sorted(issues):
        print(issue)
    print(f"\nTotal Issues Found: {len(issues)}")
