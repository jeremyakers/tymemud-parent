import os
import re

def strip_ansi(text):
    text = text.rstrip('~')
    text = re.sub(r'`.', '', text)
    text = re.sub(r'\^.', '', text)
    text = re.sub(r'&[0-9]+;?', '', text)
    return text.strip()

def get_city_pair(vnum):
    if 64022 >= vnum >= 50919 or 54000 <= vnum <= 54099 or 57000 <= vnum <= 57099: # Road 1
        # Actually Road 1 covers many zones. Let's be more precise.
        pass
    
    # Precise Road vnum ranges from previous audit script or plan
    road_ranges = {
        "Caemlyn - Tar Valon": [(64022, 64002), (61092, 61003), (57093, 57007), (54097, 54059), (53950, 53902), (50994, 50919)],
        "Caemlyn - Far Madding": [(64062, 64093)],
        "Caemlyn - Aringill": [(64044, 63861)],
        "Aringill - Cairhien": [(63864, 53786), (60897, 60761)],
        "Jangai": [(53746, 53739)],
        "Jangai Connector": [(53768, 53748)],
        "Cairhien - Tar Valon": [(53763, 46883), (53829, 53809), (50899, 50801)],
        "Luagde - Chachin/Shol Arbela": [(46949, 46800)],
        "Jualdhe - Maradon": [(46976, 46960)],
        "Darein - Dragonmount": [(46997, 50915)]
    }
    
    for pair, ranges in road_ranges.items():
        for start, end in ranges:
            low, high = min(start, end), max(start, end)
            if low <= vnum <= high:
                return pair
    return "Overland"

def fix_all_road_names(wld_dir, zones):
    direction_map = {0: "North", 1: "East", 2: "South", 3: "West", 6: "Northeast", 7: "Northwest", 8: "Southeast", 9: "Southwest"}
    
    # 1. Load all rooms into memory
    all_rooms = {}
    for z in zones:
        wld_file = os.path.join(wld_dir, f"{z}.wld")
        if not os.path.exists(wld_file): continue
        with open(wld_file, 'r', encoding='latin-1') as f:
            content = f.read()
        
        blocks = re.split(r'^#(\d+)', content, flags=re.MULTILINE)[1:]
        for i in range(0, len(blocks), 2):
            vnum = int(blocks[i])
            block = blocks[i+1]
            desc_end_pos = block.find('~', block.find('~') + 1)
            flags_line = block[desc_end_pos+1:].strip().split('\n')[0].split()
            sector = int(flags_line[2]) if len(flags_line) > 2 else -1
            exits = {}
            d_matches = re.finditer(r"^D(\d+)\n.*?\n.*?\n(\d+) (\d+) (\d+)", block, re.MULTILINE)
            for dm in d_matches:
                exits[int(dm.group(1))] = int(dm.group(4))
            
            all_rooms[vnum] = {'vnum': vnum, 'block': block, 'sector': sector, 'exits': exits, 'zone': z}

    # 2. Process each zone file
    for z in zones:
        wld_file = os.path.join(wld_dir, f"{z}.wld")
        if not os.path.exists(wld_file): continue
        with open(wld_file, 'r', encoding='latin-1') as f:
            content = f.read()
        
        new_content = content
        # Find all rooms in this zone
        zone_rooms = [v for v, r in all_rooms.items() if r['zone'] == z]
        zone_rooms.sort(reverse=True) # Process from end to avoid index issues
        
        for vnum in zone_rooms:
            room = all_rooms[vnum]
            if room['sector'] == 11:
                # Calculate road exits
                road_exits = []
                for d_idx, dest in room['exits'].items():
                    if dest in all_rooms and all_rooms[dest]['sector'] == 11:
                        road_exits.append(direction_map[d_idx])
                
                if not road_exits: continue
                
                # Format name
                city_pair = get_city_pair(vnum)
                road_name = f"The {city_pair} Road" if city_pair != "Jangai" else "The Jangai Road"
                if city_pair == "Jangai Connector": road_name = "The Jangai Connector Road"
                
                dirs_str = ""
                if len(road_exits) == 1:
                    dirs_str = f"runs `&{road_exits[0]}"
                elif len(road_exits) == 2:
                    dirs_str = f"runs `&{road_exits[0]}`6 and `&{road_exits[1]}"
                else:
                    dirs_str = "runs " + ", ".join([f"`&{d}" for d in road_exits[:-1]]) + f"`6, and `&{road_exits[-1]}"
                
                new_name = f"`6{road_name} {dirs_str}`7~"
                
                # Replace the name line in the content
                # Name is the first line of the block
                lines = room['block'].split('\n')
                old_name_line = lines[1]
                new_block = room['block'].replace(old_name_line, new_name, 1)
                
                # We need to replace the exact room block in new_content
                # To be safe, we match the #VNUM and the original block exactly
                pattern = re.escape(f"#{vnum}") + r"\s*\n" + re.escape(room['block'].strip())
                new_content = re.sub(pattern, f"#{vnum}\n{new_block.strip()}", new_content, flags=re.MULTILINE)

        with open(wld_file, 'w', encoding='latin-1') as f:
            f.write(new_content)

if __name__ == "__main__":
    wld_dir = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld"
    zones = [468, 469, 508, 509, 537, 538, 539, 540, 567, 568, 569, 570, 607, 608, 609, 610, 638, 639, 640]
    fix_all_road_names(wld_dir, zones)
    print("Road names truth-standardized.")
