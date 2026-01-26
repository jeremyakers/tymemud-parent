import sys
import os
import re

def strip_ansi(text):
    return re.sub(r'[\x1b\x1d].*?[m~]|\^[^\s]|`[^~]*~', '', text)

def get_room_data(wld_dir, vnum):
    zone = vnum // 100
    wld_file = os.path.join(wld_dir, f"{zone}.wld")
    if not os.path.exists(wld_file):
        return None
    
    with open(wld_file, 'r', encoding='latin-1') as f:
        content = f.read()
    
    # Find the room block starting with #VNUM until the next # or end
    room_match = re.search(fr"^#{vnum}\s*\n(.*?)\nS" , content, re.MULTILINE | re.DOTALL)
    if not room_match:
        return None
    
    block = room_match.group(0)
    lines = block.split('\n')
    
    name = strip_ansi(lines[1].strip())
    
    # Find the line with room flags and sector
    # Format: zone_num flags sector ...
    # Usually the line after the description tilde
    desc_end_idx = -1
    for i, line in enumerate(lines):
        if line.strip() == '~' and i > 1:
            desc_end_idx = i
            break
    
    sector = -1
    if desc_end_idx != -1 and desc_end_idx + 1 < len(lines):
        flags_line = lines[desc_end_idx + 1].strip().split()
        if len(flags_line) >= 3:
            try:
                sector = int(flags_line[2])
            except ValueError:
                pass
    
    exits = {}
    d_matches = re.finditer(r"^D(\d+)\n.*?\n.*?\n(\d+) (\d+) (\d+)", block, re.MULTILINE)
    for dm in d_matches:
        exits[int(dm.group(1))] = int(dm.group(4))
            
    return {
        'vnum': vnum,
        'name': name,
        'sector': sector,
        'exits': exits
    }

def walk_road(wld_dir, start_vnum, end_vnum):
    current = start_vnum
    visited = set()
    path = []
    
    while current not in visited:
        visited.add(current)
        data = get_room_data(wld_dir, current)
        if not data:
            print(f"Error: Could not find room {current}")
            break
        
        path.append(data)
        if current == end_vnum:
            break
            
        # Try to find the next road tile
        next_vnum = None
        # Priority: N, S, E, W, NE, NW, SE, SW
        priority = [0, 2, 1, 3, 6, 7, 8, 9]
        for dir_idx in priority:
            if dir_idx not in data['exits']:
                continue
            dest = data['exits'][dir_idx]
            if dest in visited:
                continue
            dest_data = get_room_data(wld_dir, dest)
            if dest_data and dest_data['sector'] == 11: # Main road
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
    
    path = walk_road(wld_dir, start, end)
    for p in path:
        recip_issues = []
        for dir_idx, dest in p['exits'].items():
            dest_data = get_room_data(wld_dir, dest)
            if dest_data:
                # Directions: 0:N, 1:E, 2:S, 3:W, 4:U, 5:D, 6:NE, 7:NW, 8:SE, 9:SW
                opposites = {0:2, 1:3, 2:0, 3:1, 4:5, 5:4, 6:9, 7:8, 8:7, 9:6}
                opp = opposites.get(dir_idx)
                if opp is not None:
                    if dest_data['exits'].get(opp) != p['vnum']:
                        recip_issues.append(f"Exit {dir_idx}->{dest} not reciprocal (Dest {opp}->{dest_data['exits'].get(opp)})")
            else:
                recip_issues.append(f"Exit {dir_idx}->{dest} destination missing")
        
        print(f"[{p['vnum']}] {p['name']} (Sector {p['sector']})")
        if recip_issues:
            for ri in recip_issues:
                print(f"  !! {ri}")
    
    if path and path[-1]['vnum'] == end:
        print("Reached end vnum.")
    else:
        print(f"Walk stopped at {path[-1]['vnum'] if path else 'start'}")
