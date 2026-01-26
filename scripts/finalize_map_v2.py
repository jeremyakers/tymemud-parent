import re
import os

wld_dir = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld"

# Templates
erinin_desc = """`6The mighty River Erinin flows steadily here, its deep blue waters carrying
the commerce of the Westlands. The river is wide and powerful, with a current
that demands respect from even the most seasoned rivermen. Along the banks,
the land is lush and green, and the occasional merchant vessel can be seen
moving slowly along its course.`7"""

road_desc = """`6This stretch of the road is wide and well-traveled, providing a vital link
through the countryside. Paving stones, worn by years of use, peek through the 
hard-packed dirt in places. The surrounding fields are alive with the sounds 
of nature, while the road itself remains a firm and reliable path for merchant 
wagons and lone travelers alike.`7"""

maradon_road_desc = """`6This ancient highway stretches through the northern borderlands, connecting 
the great city of Tar Valon to the distant city of Maradon. The road is 
constructed of heavy, weathered stones, laid down by builders whose names 
have been lost to history. To the north, the terrain grows increasingly wild 
as it approaches the Blight, while the road itself remains a vital artery 
for commerce and the defense of the realm.`7"""

dragonmount_road_desc = """`6This well-worn road leads away from the bridges of Tar Valon, heading west 
toward the jagged shadow of Dragonmount. The peak loomes large on the horizon, 
a constant reminder of the Breaking. The air is cool and sharp this close to 
the mountains, and the road carries travelers past isolated farmsteads and 
sparse woodlands at the base of the Great Peak.`7"""

cairhien_tv_road_desc = """`6The main highway between Cairhien and Tar Valon travels through the heart of 
the eastern farmlands. This stretch of the road is wide and meticulously 
maintained to handle the massive flow of goods between the two great cities. 
Paving stones peek through the dirt in places, and the traffic is frequent, 
ranging from merchant wagons to riders on urgent business.`7"""

def get_full_content(file_path):
    with open(file_path, 'r', encoding='latin-1') as f:
        return f.read()

def parse_room(vnum, content):
    pattern = rf'^#{vnum}\s*\n(.*?)(?=\n#|\Z)'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    if not match: return None
    block = match.group(0)
    
    # Extract parts
    name_match = re.search(r'^#\d+\s*\n(.*?)\n', block)
    name = name_match.group(1) if name_match else ""
    
    # Exits: find all lines starting with D# and the 3 following lines
    exits = {}
    d_matches = re.finditer(r'^D(\d+)\n(.*?)\n(.*?)\n(-?\d+ -?\d+ \d+)', block, re.MULTILINE)
    for dm in d_matches:
        d_idx = int(dm.group(1))
        exits[d_idx] = {
            'desc': dm.group(2),
            'keyword': dm.group(3),
            'coords': dm.group(4)
        }
    
    # Flags: line after the second ~
    m = re.search(r'~.*?\n(.*)', block, re.DOTALL)
    flags = m.group(1).strip().split('\n')[0] if m else ""
    
    return {'vnum': vnum, 'name': name, 'exits': exits, 'flags': flags, 'block': block}

def build_block(vnum, name, desc, sector, exits, zone):
    # Standard format: #VNUM \n NAME~ \n DESC~ \n ZONE FLAGS SECTOR \n EXITS \n R \n G \n S
    # For simplicity, we'll keep the zone and flags from the original or default
    flags = f"{zone} a {sector} 10 10"
    
    res = f"#{vnum}\n{name}~\n{desc}\n~\n{flags}"
    for d_idx in sorted(exits.keys()):
        e = exits[d_idx]
        res += f"\nD{d_idx}\n{e['desc']}\n{e['keyword']}\n{e['coords']}"
    
    res += """\nR
In the Wake of an Army~
     `2It is immediately evident that a large number of troops
have passed through this area, recently.  The terrain has been
beaten and disturbed by great quantities of tracks, and the
foliage has taken a great pounding...`7
~
G
 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
S"""
    return res

def main():
    # Load all files
    files = {z: get_full_content(os.path.join(wld_dir, f"{z}.wld")) for z in [468, 469, 508, 509, 537, 538, 539, 540, 567, 568, 569, 570, 607, 608, 609, 610, 638, 639, 640]}

    # 1. Fix 57031 Hole
    r57031 = parse_room(57031, files[570])
    exits = r57031['exits']
    exits[0] = {'desc': '~', 'keyword': '~', 'coords': '0 0 57021'}
    exits[1] = {'desc': '~', 'keyword': '~', 'coords': '0 0 57032'}
    exits[2] = {'desc': '~', 'keyword': '~', 'coords': '0 0 57041'}
    exits[3] = {'desc': '~', 'keyword': '~', 'coords': '0 0 57030'}
    new_block = build_block(57031, "`6The Deep Forest`7", generic_forest_desc, 2, exits, 570)
    files[570] = files[570].replace(r57031['block'], new_block)

    # 57021 Berrywood Fix: Move interior to D5, point D2 to 57031
    r57021 = parse_room(57021, files[570])
    exits = r57021['exits']
    exits[2] = {'desc': '~', 'keyword': '~', 'coords': '0 0 57031'}
    exits[5] = {'desc': '~', 'keyword': '~', 'coords': '1 0 61100'}
    new_block = build_block(57021, r57021['name'], r57021['block'].split('~')[1].strip(), 2, exits, 570)
    files[570] = files[570].replace(r57021['block'], new_block)

    # 2. Fix 50983 Hole
    r50983 = parse_room(50983, files[509])
    exits = r50983['exits']
    # Ensure all grid links are bidirectional
    exits[0] = {'desc': '~', 'keyword': '~', 'coords': '0 0 50973'}
    exits[1] = {'desc': '~', 'keyword': '~', 'coords': '0 0 50984'}
    exits[2] = {'desc': '~', 'keyword': '~', 'coords': '0 0 50993'}
    exits[3] = {'desc': '~', 'keyword': '~', 'coords': '0 0 50982'}
    new_block = build_block(50983, "`@Rolling Grassland`7", generic_plains_desc, 2, exits, 509)
    files[509] = files[509].replace(r50983['block'], new_block)

    # 3. Fix 53904 Hole
    r53904 = parse_room(53904, files[539])
    exits = r53904['exits']
    exits[0] = {'desc': '~', 'keyword': '~', 'coords': '0 0 50994'}
    exits[1] = {'desc': '~', 'keyword': '~', 'coords': '0 0 53905'}
    exits[3] = {'desc': '~', 'keyword': '~', 'coords': '0 0 53903'}
    exits[8] = {'desc': '~', 'keyword': '~', 'coords': '0 0 50993'}
    new_block = build_block(53904, "`6The River Erinin`7", erinin_desc, 6, exits, 539)
    files[539] = files[539].replace(r53904['block'], new_block)

    # 4. Revert Darein (46998)
    r46998 = parse_room(46998, files[469])
    name = "`*D`6a`&r`7e`6i`*n `7"
    desc = """`7The village of Darein lies at the foot of the bridge from Tar Valon. The 
village was burned during the Trolloc Wars, sacked by Artur Hawkwing, 
looted during the Hundred Years War and burned again during the Aiel 
War. Every time it has been rebuilt. Red and brown brick houses and shops
	line the stone paved streets. The city of Tar Valon lies to the `&northeast`7, other 
villages are `&east`7 and `6west`7, and `&south`7 lies the open road.`7"""
    new_block = build_block(46998, name, desc, 1, r46998['exits'], 469)
    files[469] = files[469].replace(r46998['block'], new_block)

    # 5. Fix Cairhien - Tar Valon Road
    for v in [46883, 46884, 46894]:
        r = parse_room(v, files[468])
        if not r: continue
        dirs = "North, East, South, and West" if v in [46883, 46884] else "North, South, and West"
        name = f"`6The Cairhien - Tar Valon Road runs {dirs}`7"
        new_block = build_block(v, name, cairhien_tv_road_desc, 11, r['exits'], 468)
        files[468] = files[468].replace(r['block'], new_block)

    # Save all files
    for z, content in files.items():
        with open(os.path.join(wld_dir, f"{z}.wld"), 'w', encoding='latin-1') as f:
            f.write(content)

if __name__ == "__main__":
    main()
