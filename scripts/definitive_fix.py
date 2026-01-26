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

generic_plains_desc = """`7Open ground stretches out in every direction, a vast sea of grass 
broken only by the occasional cluster of small leafy trees. The horizon shimmers 
faintly in the heat, and the sky is a wide, pale blue that makes the land feel 
exposed. The air is clear and the view open across the fertile countryside.`7"""

generic_forest_desc = """`2A mix of trees make up the local woodland. Narrow, white-barked specimens 
grow everywhere, and thick, wrinkled oaks are clearly many generations old. 
Occasional stands of paper-barked trees appear haphazardly, and the trees 
themselves come in a variety of forms and sizes. A space of several paces lies 
between everything, allowing for easy passage.`7"""

# City descriptions
darein_desc = """`7The village of Darein lies at the foot of the bridge from Tar Valon. The 
village was burned during the Trolloc Wars, sacked by Artur Hawkwing, 
looted during the Hundred Years War and burned again during the Aiel 
War. Every time it has been rebuilt. Red and brown brick houses and shops
	line the stone paved streets. The city of Tar Valon lies to the `&northeast`7, other 
villages are `&east`7 and `6west`7, and `&south`7 lies the open road.`7"""

def get_block(vnum, content):
    pattern = rf'^#{vnum}\s*\n(.*?)(?=\n#|\Z)'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    return match.group(0) if match else None

def rewrite_room(file_path, vnum, name, desc, sector, exits, zone):
    with open(file_path, 'r', encoding='latin-1') as f: content = f.read()
    old = get_block(vnum, content)
    if not old:
        print(f"FAILED TO FIND {vnum}")
        return
    
    # Build new block
    new = f"#{vnum}\n{name}~\n{desc}\n~\n{zone} a {sector} 10 10"
    for d_idx in sorted(exits.keys()):
        e = exits[d_idx]
        new += f"\nD{d_idx}\n{e['desc']}\n{e['keyword']}\n{e['coords']}"
    new += """\nR
In the Wake of an Army~
     `2It is immediately evident that a large number of troops
have passed through this area, recently.  The terrain has been
beaten and disturbed by great quantities of tracks, and the
foliage has taken a great pounding...`7
~
G
 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
S"""
    with open(file_path, 'w', encoding='latin-1') as f: f.write(content.replace(old, new))
    print(f"Fixed {vnum}")

def main():
    # --- 1. CONNECTIVITY HOLES & GRID ---
    
    # 57031 (The center hole)
    rewrite_room(f"{wld_dir}/570.wld", 57031, "`6The Deep Forest`7", generic_forest_desc, 2, 
        {0: {'desc':'~','keyword':'~','coords':'0 0 57021'},
         1: {'desc':'~','keyword':'~','coords':'0 0 57032'},
         2: {'desc':'~','keyword':'~','coords':'0 0 57041'},
         3: {'desc':'~','keyword':'~','coords':'0 0 57030'}}, 570)

    # 57021 (Berrywood - move interior to D5)
    rewrite_room(f"{wld_dir}/570.wld", 57021, "`6The `%B`5err`@y`2wo`5o`%d`6 Farm`7", "`3This land is rich and `@f`2e`@r`2t`@i`2l`@e`3, filled with fields...`7", 2,
        {0: {'desc':'~','keyword':'~','coords':'0 0 57011'},
         1: {'desc':'~','keyword':'~','coords':'0 0 57022'},
         2: {'desc':'~','keyword':'~','coords':'0 0 57031'},
         3: {'desc':'~','keyword':'~','coords':'0 0 57020'},
         5: {'desc':'~','keyword':'~','coords':'1 0 61100'}}, 570)

    # 50983 (Grid hole)
    rewrite_room(f"{wld_dir}/509.wld", 50983, "`@Rolling Grassland`7", generic_plains_desc, 2,
        {0: {'desc':'~','keyword':'~','coords':'0 0 50973'},
         1: {'desc':'~','keyword':'~','coords':'0 0 50984'},
         2: {'desc':'~','keyword':'~','coords':'0 0 50993'},
         3: {'desc':'~','keyword':'~','coords':'0 0 50982'}}, 509)

    # 53904 (Grid hole - River)
    rewrite_room(f"{wld_dir}/539.wld", 53904, "`6The River Erinin`7", erinin_desc, 6,
        {0: {'desc':'~','keyword':'~','coords':'0 0 50994'},
         1: {'desc':'~','keyword':'~','coords':'0 0 53905'},
         2: {'desc':'~','keyword':'~','coords':'0 0 53914'},
         3: {'desc':'~','keyword':'~','coords':'0 0 53903'},
         8: {'desc':'~','keyword':'~','coords':'0 0 50993'}}, 539)

    # Neighbors reciprocals
    rewrite_room(f"{wld_dir}/509.wld", 50984, "`6The Caemlyn - Tar Valon Road runs East, South, and West`7", road_desc, 11,
        {0: {'desc':'~','keyword':'~','coords':'0 0 50974'},
         1: {'desc':'~','keyword':'~','coords':'0 0 50985'},
         2: {'desc':'~','keyword':'~','coords':'0 0 50994'},
         3: {'desc':'~','keyword':'~','coords':'0 0 50983'}}, 509)

    rewrite_room(f"{wld_dir}/509.wld", 50993, "`6The River Erinin runs North, East, South, and West`7", erinin_desc, 6,
        {0: {'desc':'~','keyword':'~','coords':'0 0 50983'},
         1: {'desc':'~','keyword':'~','coords':'0 0 50994'},
         2: {'desc':'~','keyword':'~','coords':'0 0 53903'},
         3: {'desc':'~','keyword':'~','coords':'0 0 50992'},
         7: {'desc':'~','keyword':'~','coords':'0 0 53904'}}, 509)

    rewrite_room(f"{wld_dir}/539.wld", 53903, "`6The Caemlyn - Tar Valon Road runs North, West, and Northeast`7", road_desc, 11,
        {0: {'desc':'~','keyword':'~','coords':'0 0 50993'},
         1: {'desc':'~','keyword':'~','coords':'0 0 53904'},
         2: {'desc':'~','keyword':'~','coords':'0 0 53913'},
         3: {'desc':'~','keyword':'~','coords':'0 0 53902'},
         6: {'desc':'~','keyword':'~','coords':'0 0 50994'}}, 539)

    # --- 2. CITY RESTORATION ---
    rewrite_room(f"{wld_dir}/469.wld", 46998, "`*D`6a`&r`7e`6i`*n `7", darein_desc, 1,
        {0: {'desc':'~','keyword':'~','coords':'0 0 46988'},
         1: {'desc':'~','keyword':'~','coords':'0 0 46999'},
         2: {'desc':'~','keyword':'~','coords':'0 0 50908'},
         3: {'desc':'~','keyword':'~','coords':'0 0 46997'},
         6: {'desc':'~','keyword':'~','coords':'0 0 48603'}}, 469)

    # --- 3. CAIRHIEN ROAD (46884 exception) ---
    rewrite_room(f"{wld_dir}/468.wld", 46884, "`6The Cairhien - Tar Valon Road runs North, East, South, and West`7", road_desc, 11,
        {0: {'desc':'~','keyword':'~','coords':'0 0 46874'},
         1: {'desc':'~','keyword':'~','coords':'0 0 46885'},
         2: {'desc':'~','keyword':'~','coords':'0 0 46894'},
         3: {'desc':'~','keyword':'~','coords':'0 0 46883'}}, 468)

    print("Definitive reconstruction complete.")

if __name__ == "__main__": main()
