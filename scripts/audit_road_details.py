import sys
import os
import re

def strip_ansi(text):
    # Remove color codes like `6, `7, `#, `^, etc.
    # The format seems to be ` followed by a char (color) or # then color
    # and also ^ followed by a char.
    # And & followed by numbers and a semicolon.
    # The whole line usually ends with ~ which is a delimiter, not part of the name.
    
    # First remove the trailing ~
    text = text.rstrip('~')
    
    # Remove `X patterns (where X is any character)
    text = re.sub(r'`.', '', text)
    # Remove ^X patterns
    text = re.sub(r'\^.', '', text)
    # Remove &10; patterns
    text = re.sub(r'&[0-9]+;?', '', text)
    # Remove any other ANSI-like escapes if present
    text = re.sub(r'[\x1b\x1d].*?[m~]', '', text)
    
    return text.strip()

def get_room_data(wld_dir, vnum):
    zone = vnum // 100
    wld_file = os.path.join(wld_dir, f"{zone}.wld")
    if not os.path.exists(wld_file):
        return None
    
    try:
        with open(wld_file, 'r', encoding='latin-1') as f:
            content = f.read()
    except Exception:
        return None
    
    # Find the room block starting with #VNUM until the next # or end
    # Room header: #VNUM\nName~\nDescription~\nFlags...
    room_match = re.search(fr"^#{vnum}\s*\n(.*?)\n(.*?)\n~" , content, re.MULTILINE | re.DOTALL)
    if not room_match:
        return None
    
    name_raw = room_match.group(1).strip()
    name = strip_ansi(name_raw)
    
    desc_raw = room_match.group(2).strip()
    desc = strip_ansi(desc_raw)
    
    # Find until the S
    full_room_match = re.search(fr"^#{vnum}\s*\n.*?^S" , content, re.MULTILINE | re.DOTALL)
    if not full_room_match:
        return None
    block = full_room_match.group(0)
    lines = block.split('\n')
    
    desc_end_idx = -1
    for i, line in enumerate(lines):
        if line.strip() == '~' and i > 1:
            desc_end_idx = i
            # We want the SECOND tilde (end of description)
            # The regex above group(2) captures until the FIRST tilde after the name.
            # Actually, standard MUD format is:
            # #VNUM
            # Name~
            # Description
            # ~
            # Flags...
            pass
    
    # Let's find the flags line differently. It's the line after the description's terminating ~
    # We'll find the first ~ after the name line.
    name_tilde_pos = content.find('~', content.find(f"#{vnum}"))
    desc_start_pos = name_tilde_pos + 1
    desc_tilde_pos = content.find('~', desc_start_pos)
    
    flags_start_pos = desc_tilde_pos + 1
    flags_end_pos = content.find('\n', flags_start_pos + 1)
    flags_line = content[flags_start_pos:flags_end_pos].strip().split()
    
    sector = -1
    if len(flags_line) >= 3:
        try:
            sector = int(flags_line[2])
        except ValueError:
            pass
    
    exits = {}
    # Search for D[0-9] in the block
    d_matches = re.finditer(r"^D(\d+)\n.*?\n.*?\n(\d+) (\d+) (\d+)", block, re.MULTILINE)
    for dm in d_matches:
        exits[int(dm.group(1))] = int(dm.group(4))
            
    return {
        'vnum': vnum,
        'name': name,
        'desc': desc,
        'sector': sector,
        'exits': exits
    }

def audit_road(wld_dir, start_vnum, end_vnum):
    current = start_vnum
    visited = set()
    path = []
    
    while current not in visited:
        visited.add(current)
        data = get_room_data(wld_dir, current)
        if not data:
            break
        
        path.append(data)
        if current == end_vnum:
            break
            
        next_vnum = None
        # Directions: 0:N, 1:E, 2:S, 3:W, 4:U, 5:D, 6:NE, 7:NW, 8:SE, 9:SW
        priority = [0, 2, 1, 3, 6, 7, 8, 9]
        for dir_idx in priority:
            if dir_idx not in data['exits']:
                continue
            dest = data['exits'][dir_idx]
            if dest in visited:
                continue
            dest_data = get_room_data(wld_dir, dest)
            if dest_data and dest_data['sector'] == 11:
                next_vnum = dest
                break
        
        if not next_vnum:
            break
        current = next_vnum
        
    return path

if __name__ == "__main__":
    wld_dir = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld"
    start = int(sys.argv[1])
    end = int(sys.argv[2])
    road_name_hint = sys.argv[3] if len(sys.argv) > 3 else "Road"
    
    path = audit_road(wld_dir, start, end)
    
    print(f"Audit results for {road_name_hint} ({start} -> {end}):")
    
    for p in path:
        issues = []
        
        # 1. Connectivity check
        opposites = {0:2, 1:3, 2:0, 3:1, 4:5, 5:4, 6:9, 7:8, 8:7, 9:6}
        for dir_idx, dest in p['exits'].items():
            dest_data = get_room_data(wld_dir, dest)
            if dest_data:
                opp = opposites.get(dir_idx)
                if opp is not None:
                    if dest_data['exits'].get(opp) != p['vnum']:
                        issues.append(f"Connectivity: Exit {dir_idx}->{dest} not reciprocal (Dest {opp}->{dest_data['exits'].get(opp)})")
            else:
                # Only report if it's within the overland range (roughly)
                if 46800 <= dest <= 64099:
                    issues.append(f"Connectivity: Exit {dir_idx}->{dest} destination missing")

        # 2. Naming check
        standard_patterns = [
            r"^The Road$",
            r".* Road runs .*",
            r"^Along the .* Road$",
            r".* Road Heads .*"
        ]
        # Relaxing naming check if it contains the road name hint
        if not any(re.match(pattern, p['name'], re.IGNORECASE) for pattern in standard_patterns):
            if road_name_hint.lower() not in p['name'].lower():
                issues.append(f"Naming: '{p['name']}' does not match standard patterns or contains '{road_name_hint}'")
        
        # 3. Description check
        if "The vast world stretches out in every direction" in p['desc']:
            issues.append("Description: Contains generic placeholder text")
        if len(p['desc']) < 100:
            issues.append(f"Description: Too short ({len(p['desc'])} chars)")
            
        if issues:
            print(f"VNUM: {p['vnum']} [{p['name']}]")
            for issue in issues:
                print(f"  - {issue}")
    
    if not path or path[-1]['vnum'] != end:
        print(f"FAILED to reach end vnum {end}. Stopped at {path[-1]['vnum'] if path else 'start'}")
