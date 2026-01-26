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
        # Variable number of lines between D# and coords
        d_blocks = re.split(r'^D(\d+)', block, flags=re.MULTILINE)[1:]
        for j in range(0, len(d_blocks), 2):
            d_idx = int(d_blocks[j])
            d_content = d_blocks[j+1]
            # Find the first line that looks like coords: 0 -1 64022 or 0 0 1234
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

def get_opposites():
    return {0:2, 1:3, 2:0, 3:1, 4:5, 5:4, 6:9, 7:8, 8:7, 9:6}

def get_direction_names():
    return {0: "North", 1: "East", 2: "South", 3: "West", 4: "Up", 5: "Down", 6: "Northeast", 7: "Northwest", 8: "Southeast", 9: "Southwest"}

def audit_path(all_rooms, start_vnum, end_vnum, expected_sector, path_name):
    if start_vnum == end_vnum:
        room = all_rooms.get(start_vnum)
        if room: return [room], []
        else: return [], [f"PATH ERROR: Start/End room {start_vnum} not found"]

    queue = [(start_vnum, [start_vnum])]
    visited = {start_vnum}
    
    while queue:
        (current_vnum, path_so_far) = queue.pop(0)
        if current_vnum == end_vnum:
            final_path = [all_rooms[v] for v in path_so_far]
            return final_path, []
            
        room = all_rooms.get(current_vnum)
        if not room: continue
            
        for d_idx, dest_vnum in room['exits'].items():
            if dest_vnum not in visited:
                dest_room = all_rooms.get(dest_vnum)
                # Allow sector 2 for 50899 per user instruction
                if dest_room and (dest_room['sector'] == expected_sector or dest_vnum == 50899):
                    visited.add(dest_vnum)
                    queue.append((dest_vnum, path_so_far + [dest_vnum]))
                    
    issues = [f"PATH BROKEN: No continuous path found for {path_name}"]
    return [], issues

def check_room_quality(room, all_rooms, expected_sector, name_standard=None):
    issues = []
    dir_names = get_direction_names()
    opposites = get_opposites()
    
    if room['sector'] != expected_sector and room['vnum'] != 50899:
        issues.append(f"SECTOR MISMATCH: Expected {expected_sector}, found {room['sector']}")
        
    for d_idx, dest_vnum in room['exits'].items():
        # Skip reciprocity check for teleporter 63861 -> 16522
        if room['vnum'] == 63861 and d_idx == 1: continue
        
        dest_room = all_rooms.get(dest_vnum)
        if dest_room:
            opp_idx = opposites.get(d_idx)
            if opp_idx is not None:
                if dest_room['exits'].get(opp_idx) != room['vnum']:
                    issues.append(f"RECIPROCITY: Exit {dir_names[d_idx]} to {dest_vnum} is one-way (Counterpart exits: {dest_room['exits']})")
        else:
            issues.append(f"EXIT ERROR: Exit {dir_names[d_idx]} to {dest_vnum} leads to missing/unloaded room")

    name_clean = room['name'].lower()
    road_dirs_in_name = []
    for d_idx, d_name in dir_names.items():
        if re.search(r'\b' + re.escape(d_name.lower()) + r'\b', name_clean):
            road_dirs_in_name.append(d_idx)
            dest_vnum = room['exits'].get(d_idx)
            dest_room = all_rooms.get(dest_vnum)
            if not dest_room or (dest_room['sector'] != expected_sector and dest_vnum != 50899):
                if not (expected_sector == 11 and dest_room and dest_room['sector'] in [1, 10]):
                    issues.append(f"NAME ERROR: Claims to run {d_name} but no relevant exit")
    
    for d_idx, dest_vnum in room['exits'].items():
        dest_room = all_rooms.get(dest_vnum)
        if dest_room and (dest_room['sector'] == expected_sector or dest_vnum == 50899):
            if d_idx not in road_dirs_in_name:
                issues.append(f"NAME ERROR: Missing direction {dir_names[d_idx]} in room name")

    if name_standard:
        if name_standard.lower() not in room['name'].lower():
            issues.append(f"NAMING CONVENTION: Name should include '{name_standard}'")

    placeholders = ["builder", "maelyn", "change me", "proper description", "vast world stretches out", "far off road", "smudge of road"]
    for p in placeholders:
        if p in room['desc'].lower():
            issues.append(f"DESCRIPTION: Placeholder text found: '{p}'")
            
    return issues

def main():
    wld_dir = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld"
    zones = [468, 469, 508, 509, 537, 538, 539, 540, 567, 568, 569, 570, 607, 608, 609, 610, 638, 639, 640, 13, 130, 16, 160, 52, 526, 62, 626]
    
    all_rooms = {}
    for z in zones:
        wld_file = os.path.join(wld_dir, f"{z}.wld")
        if os.path.exists(wld_file):
            all_rooms.update(parse_wld_file(wld_file))

    roads = [
        (64022, 50919, 11, "Caemlyn - Tar Valon Road"),
        (64062, 64093, 11, "Caemlyn - Far Madding Road"),
        (64044, 63861, 11, "Caemlyn - Aringill Road"),
        (63864, 53786, 11, "Aringill - Cairhien Road"),
        (53746, 53739, 11, "Jangai Road"),
        (53768, 53748, 11, "Jangai Road"),
        (53763, 46883, 11, "Cairhien - Tar Valon Road"),
        (46949, 46800, 11, "Luagde - Shol Arbela Road"),
        (46949, 46907, 11, "Luagde - Chachin Road"),
        (46976, 46960, 11, "Jualdhe - Maradon Road"),
        (46997, 50915, 11, "Darein - Dragonmount Road"),
        (64040, 64040, 11, "Caemlyn West Connector"),
        (61051, 61051, 11, "Tinker Camp to Caemlyn Road Connector")
    ]
    
    rivers = [
        (46905, 63893, 6, "The Erinin"),
        (50960, 53946, 6, "The Luan"),
        (53704, 63843, 6, "The Alguenya"),
        (53719, 53735, 6, "The Gaelin")
    ]

    report = []
    for start, end, sector, name in roads + rivers:
        path, path_issues = audit_path(all_rooms, start, end, sector, name)
        report.append(f"\n### {name}")
        report.append(f"Route: {start} -> {end} | Status: {'CONNECTED' if not path_issues else 'BROKEN'}")
        for pi in path_issues: report.append(f"- !! {pi}")
        for room in path:
            room_issues = check_room_quality(room, all_rooms, sector, name if sector == 11 else None)
            if room_issues:
                report.append(f"- VNUM: {room['vnum']} ({room['name']})")
                for ri in room_issues: report.append(f"  - {ri}")

    with open("/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/docs/ubermap/phase1_audit_report_raw.txt", "w") as f:
        f.write("\n".join(report))
    print("Audit report generated at docs/ubermap/phase1_audit_report_raw.txt")

if __name__ == "__main__":
    main()
