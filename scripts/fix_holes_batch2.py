import re
import os

wld_dir = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld"

def get_full_content(file_path):
    with open(file_path, 'r', encoding='latin-1') as f:
        return f.read()

def rewrite_room(vnum, new_block):
    zone = vnum // 100
    file_path = os.path.join(wld_dir, f"{zone}.wld")
    content = get_full_content(file_path)
    
    # Find the room block more robustly
    pattern = rf'^#{vnum}\s*\n(.*?)(?=\n#|\Z)'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    
    if match:
        old_block = match.group(0)
        content = content.replace(old_block, new_block.strip() + "\n")
        with open(file_path, 'w', encoding='latin-1') as f:
            f.write(content)
        print(f"Fixed room {vnum}")
    else:
        print(f"Could not find room {vnum}")

# --- FIXING 50983 HOLE ---
rewrite_room(50983, """#50983
`@Rolling Grassland`7~
`7Open ground stretches out in every direction, a vast sea of grass 
broken only by the occasional cluster of small leafy trees. The horizon shimmers 
faintly in the heat, and the sky is a wide, pale blue that makes the land feel 
exposed. The air is clear and the view open across the fertile countryside.`7
~
509 a 2 10 10
D0
~
~
0 0 50973
D1
~
~
0 0 50984
D2
~
~
0 0 50993
D3
~
~
0 0 50982
R
In the Wake of an Army~
     `2It is immediately evident that a large number of troops
have passed through this area, recently.  The terrain has been
beaten and disturbed by great quantities of tracks, and the
foliage has taken a great pounding...`7
~
G
 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
S""")

# --- FIXING 53904 HOLE ---
rewrite_room(53904, """#53904
`6The River Erinin`7~
`6The mighty River Erinin flows steadily here, its deep blue waters carrying
the commerce of the Westlands. The river is wide and powerful, with a current
that demands respect from even the most seasoned rivermen. Along the banks,
the land is lush and green, and the occasional merchant vessel can be seen
moving slowly along its course.`7
~
539 a 6 10 10
D0
~
~
0 0 50994
D1
~
~
0 0 53905
D2
~
~
0 0 53914
D3
~
~
0 0 53903
D8
~
~
0 0 50993
R
In the Wake of an Army~
     `2It is immediately evident that a large number of troops
have passed through this area, recently.  The terrain has been
beaten and disturbed by great quantities of tracks, and the
foliage has taken a great pounding...`7
~
G
 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
S""")
