import os
import re

wld_dir = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld"

def parse_wld_file(wld_file):
    if not os.path.exists(wld_file): return {}
    with open(wld_file, 'r', encoding='latin-1') as f:
        content = f.read()
    rooms = {}
    blocks = re.split(r'^#(\d+)', content, flags=re.MULTILINE)[1:]
    for i in range(0, len(blocks), 2):
        vnum = int(blocks[i])
        block = blocks[i+1]
        exits = {}
        d_matches = re.finditer(r"^D(\d+)\n.*?\n.*?\n(\d+) (\d+) (\d+)", block, re.MULTILINE)
        for dm in d_matches:
            exits[int(dm.group(1))] = int(dm.group(4))
        rooms[vnum] = {'exits': exits}
    return rooms

def check_reciprocity(vnums_to_check):
    # Load required zones
    zones = set(v // 100 for v in vnums_to_check)
    all_rooms = {}
    for z in zones:
        all_rooms.update(parse_wld_file(os.path.join(wld_dir, f"{z}.wld")))
    
    # Also load potential destination zones
    for v in vnums_to_check:
        if v in all_rooms:
            for dest in all_rooms[v]['exits'].values():
                dz = dest // 100
                if dz not in zones:
                    all_rooms.update(parse_wld_file(os.path.join(wld_dir, f"{dz}.wld")))
                    zones.add(dz)

    opp_map = {0:2, 1:3, 2:0, 3:1, 4:5, 5:4, 6:9, 7:8, 8:7, 9:6}
    dir_names = {0:"N", 1:"E", 2:"S", 3:"W", 6:"NE", 7:"NW", 8:"SE", 9:"SW"}

    for v in sorted(vnums_to_check):
        if v not in all_rooms:
            print(f"Room {v} not found.")
            continue
        
        for d, dest in all_rooms[v]['exits'].items():
            opp = opp_map.get(d)
            if opp is None: continue
            
            if dest not in all_rooms:
                print(f"VNUM {v} {dir_names[d]} -> {dest} (DEST NOT FOUND)")
                continue
            
            if all_rooms[dest]['exits'].get(opp) != v:
                print(f"VNUM {v} {dir_names[d]} -> {dest} (ONE-WAY! {dest} {dir_names[opp]} -> {all_rooms[dest]['exits'].get(opp)})")

if __name__ == "__main__":
    area1 = [46916, 46926, 46937, 46906, 46917, 46927, 46938, 46947, 46905, 46915, 46925, 46936, 46946, 46948]
    area2 = [53744, 53753, 53763, 53734, 53745, 53754, 53743, 53762, 53752, 53764, 53733, 53735, 53746, 53755, 53765]
    print("--- Area 1 Reciprocity ---")
    check_reciprocity(area1)
    print("\n--- Area 2 Reciprocity ---")
    check_reciprocity(area2)
