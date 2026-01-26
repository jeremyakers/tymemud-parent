import re
import os

wld_dir = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld"

# Templates
erinin_desc = """`6The mighty River Erinin flows steadily here, its deep blue waters carrying
the commerce of the Westlands. The river is wide and powerful, with a current
that demands respect from even the most seasoned rivermen. Along the banks,
the land is lush and green, and the occasional merchant vessel can be seen
moving slowly along its course.`7"""

generic_forest_desc = """`2A mix of trees make up the local woodland. Narrow, white-barked specimens 
grow everywhere, and thick, wrinkled oaks are clearly many generations old. 
Occasional stands of paper-barked trees appear haphazardly, and the trees 
themselves come in a variety of forms and sizes. A space of several paces lies 
between everything, allowing for easy passage.`7"""

generic_plains_desc = """`7Open ground stretches out in every direction, a vast sea of grass 
broken only by the occasional cluster of small leafy trees. The horizon shimmers 
faintly in the heat, and the sky is a wide, pale blue that makes the land feel 
exposed. The air is clear and the view open across the fertile countryside.`7"""

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
    
    name_match = re.search(r'^#\d+\s*\n(.*?)\n', block)
    name = name_match.group(1).rstrip('~') if name_match else ""
    
    exits = {}
    d_matches = re.finditer(r'^D(\d+)\n(.*?)\n(.*?)\n(-?\d+ -?\d+ \d+)', block, re.MULTILINE)
    for dm in d_matches:
        d_idx = int(dm.group(1))
        exits[d_idx] = {'desc': dm.group(2), 'keyword': dm.group(3), 'coords': dm.group(4)}
    
    return {'vnum': vnum, 'name': name, 'exits': exits, 'block': block}

def build_block(vnum, name, desc, sector, exits, zone):
    res = f"#{vnum}\n{name}~\n{desc}\n~\n{zone} a {sector} 10 10"
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
    files = {z: get_full_content(os.path.join(wld_dir, f"{z}.wld")) for z in [468, 469, 508, 509, 537, 538, 539, 540, 567, 568, 569, 570, 607, 608, 609, 610, 638, 639, 640]}

    # 1. BERRYWOOD HOLE (57031)
    r57031 = parse_room(57031, files[570])
    exits = r57031['exits']
    exits[0] = {'desc': '~', 'keyword': '~', 'coords': '0 0 57021'}
    exits[1] = {'desc': '~', 'keyword': '~', 'coords': '0 0 57032'}
    exits[2] = {'desc': '~', 'keyword': '~', 'coords': '0 0 57041'}
    exits[3] = {'desc': '~', 'keyword': '~', 'coords': '0 0 57030'}
    files[570] = files[570].replace(r57031['block'], build_block(57031, "`6The Deep Forest`7", generic_forest_desc, 2, exits, 570))

    # Berrywood Farm (57021)
    r57021 = parse_room(57021, files[570])
    exits = r57021['exits']
    exits[2] = {'desc': '~', 'keyword': '~', 'coords': '0 0 57031'}
    exits[5] = {'desc': '~', 'keyword': '~', 'coords': '1 0 61100'}
    files[570] = files[570].replace(r57021['block'], build_block(57021, r57021['name'], r57021['block'].split('~')[1].strip(), 2, exits, 570))

    # Neighbors of 57031
    for v, d, dest in [(57030, 1, 57031), (57032, 3, 57031), (57041, 0, 57031)]:
        r = parse_room(v, files[570])
        r['exits'][d] = {'desc': '~', 'keyword': '~', 'coords': f'0 0 {dest}'}
        files[570] = files[570].replace(r['block'], build_block(v, r['name'], r['block'].split('~')[1].strip(), 2 if v!=57041 else 3, r['exits'], 570))

    # 2. ZONE 509/539 HOLES
    r50983 = parse_room(50983, files[509])
    exits = r50983['exits']
    exits[0] = {'desc': '~', 'keyword': '~', 'coords': '0 0 50973'}
    exits[1] = {'desc': '~', 'keyword': '~', 'coords': '0 0 50984'}
    exits[2] = {'desc': '~', 'keyword': '~', 'coords': '0 0 50993'}
    exits[3] = {'desc': '~', 'keyword': '~', 'coords': '0 0 50982'}
    files[509] = files[509].replace(r50983['block'], build_block(50983, "`@Rolling Grassland`7", generic_plains_desc, 2, exits, 509))

    # 50984 D3 -> 50983
    r50984 = parse_room(50984, files[509])
    r50984['exits'][3] = {'desc': '~', 'keyword': '~', 'coords': '0 0 50983'}
    files[509] = files[509].replace(r50984['block'], build_block(50984, r50984['name'], r50984['block'].split('~')[1].strip(), 11, r50984['exits'], 509))

    # 50993 D0 -> 50983, D7 -> 53904
    r50993 = parse_room(50993, files[509])
    r50993['exits'][0] = {'desc': '~', 'keyword': '~', 'coords': '0 0 50983'}
    r50993['exits'][7] = {'desc': '~', 'keyword': '~', 'coords': '0 0 53904'}
    files[509] = files[509].replace(r50993['block'], build_block(50993, r50993['name'], erinin_desc, 6, r50993['exits'], 509))

    # 53904 Hole (River)
    r53904 = parse_room(53904, files[539])
    exits = r53904['exits']
    exits[0] = {'desc': '~', 'keyword': '~', 'coords': '0 0 50994'}
    exits[1] = {'desc': '~', 'keyword': '~', 'coords': '0 0 53905'}
    exits[3] = {'desc': '~', 'keyword': '~', 'coords': '0 0 53903'}
    exits[8] = {'desc': '~', 'keyword': '~', 'coords': '0 0 50993'}
    files[539] = files[539].replace(r53904['block'], build_block(53904, "`6The River Erinin`7", erinin_desc, 6, exits, 539))

    # 53903 D1 -> 53904
    r53903 = parse_room(53903, files[539])
    r53903['exits'][1] = {'desc': '~', 'keyword': '~', 'coords': '0 0 53904'}
    files[539] = files[539].replace(r53903['block'], build_block(53903, r53903['name'], r53903['block'].split('~')[1].strip(), 11, r53903['exits'], 539))

    # 3. DAREIN (46998)
    r46998 = parse_room(46998, files[469])
    desc = """`7The village of Darein lies at the foot of the bridge from Tar Valon. The 
village was burned during the Trolloc Wars, sacked by Artur Hawkwing, 
looted during the Hundred Years War and burned again during the Aiel 
War. Every time it has been rebuilt. Red and brown brick houses and shops
	line the stone paved streets. The city of Tar Valon lies to the `&northeast`7, other 
villages are `&east`7 and `6west`7, and `&south`7 lies the open road.`7"""
    files[469] = files[469].replace(r46998['block'], build_block(46998, "`*D`6a`&r`7e`6i`*n `7", desc, 1, r46998['exits'], 469))

    # 4. CAIRHIEN ROAD
    for v in [46883, 46884, 46894]:
        r = parse_room(v, files[468])
        if not r: continue
        dirs = "North, East, South, and West" if v in [46883, 46884] else "North, South, and West"
        files[468] = files[468].replace(r['block'], build_block(v, f"`6The Cairhien - Tar Valon Road runs {dirs}`7", cairhien_tv_road_desc, 11, r['exits'], 468))

    for z, content in files.items():
        with open(os.path.join(wld_dir, f"{z}.wld"), 'w', encoding='latin-1') as f:
            f.write(content)

if __name__ == "__main__":
    main()
