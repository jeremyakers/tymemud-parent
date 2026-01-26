import re
import os

wld468 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/468.wld"
wld537 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/537.wld"
wld509 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/509.wld"
wld539 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/539.wld"

def rewrite_room(file_path, vnum, new_block):
    if not os.path.exists(file_path): return
    with open(file_path, 'r', encoding='latin-1') as f:
        content = f.read()
    pattern = rf'^#{vnum}\s*\n(.*?)(?=\n#|\Z)'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    if match:
        old_block = match.group(0)
        content = content.replace(old_block, new_block)
        with open(file_path, 'w', encoding='latin-1') as f:
            f.write(content)
        print(f"Rewrote {vnum}")
    else:
        print(f"Could not find {vnum} in {file_path}")

# 1. Fix 53747 Name
block_53747 = """#53747
`6The Jangai Road runs `&East`6 and `&West`7~
`3The well-worn Jangai road crests, revealing a magnificent view of the
fabled topless towers of Cairhien rising defiantly beside the eastern bank of 
the river Alguenya. Jagged towertops emerge from tight cages of scaffolding,
a constant reminder of their former glory and the devestating concequences
of war. Beneath the towers, the great city of Cairhien dominates the 
landscape. With cold precision, its broad avenues and smaller side streets
form a perfect grid of straight lines and right angles. Even the terraced
hillsides impose order on the otherwise rolling Cairhienin landscape.
Surrounding the city on three sides, a wide swath of ash scars the land, the
only reminder of the colorful and boisterous Foregate that once enveloped
the great city. To the north, the hills of Cairhien mellow to rolling plains as
they approach the river Gaelin.`7
~
537 a 11 10 10
D0
~
~
0 0 53737
D1
~
~
0 0 53748
D3
~
~
0 0 53746
R
In the Wake of an Army~
     `2It is immediately evident that a large number of troops
have passed through this area, recently.  The terrain has been
beaten and disturbed by great quantities of tracks, and the
foliage has taken a great pounding...`7
~
G
 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
S"""

# 2. Fix 53768 West Exit to 13093
block_53768 = """#53768
`6The Jangai Connector Road runs `&North`6 and `&West`7~
`3 The road comes in from the north, widening and well maintained as it
reaches westward towards the Jangai gate of the city of Cairhien.  Just to the
west of this stretch is the massive jumble of the Foregate where a kind of
shanty town has developed, consisting of the lower classes of the city's
inhabitants.  In contrast to the generally reserved nature of most Cairhienen,
the Foregators to the west can be seen garishly clothed, nearly like tinkers. 
Beyond the Foregate lies the massive eastern gate of the city itself.  `7 
~
537 a 11 10 10
D0
~
~
0 0 53758
D1
~
~
0 0 53769
D2
~
~
0 0 53778
D3
~
~
0 0 13093
R
In the Wake of an Army~
     `2It is immediately evident that a large number of troops
have passed through this area, recently.  The terrain has been
beaten and disturbed by great quantities of tracks, and the
foliage has taken a great pounding...`7
~
G
 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
S"""

# 3. Fix 46893 Name and Hallucination
block_46893 = """#46893
`6The River Erinin runs `&North, `&West`6, and `&Southeast`7~
`6The River `^Erinin`6 circles the island of Tar Valon. To the 
north the `7Wh`&i`7t`&e `7T`&owe`7r `6stands proudly in the midst of the 
city. The river is at least fifty spans wide, and it's 
waters move slowly. Many ships drift to and from the city 
and surrounding areas.`0 
`7The riverway continues north, west, and southeast.`7
~
468 a 6 10 10
D0
~
~
0 0 46883
D1
~
~
0 0 46894
D2
~
~
0 0 50803
D3
~
~
0 0 46892
R
In the Wake of an Army~
     `2It is immediately evident that a large number of troops
have passed through this area, recently.  The terrain has been
beaten and disturbed by great quantities of tracks, and the
foliage has taken a great pounding...`7
~
G
 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
S"""

# 4. Fix 50992 South Exit to 53902
block_50992 = """#50992
`6The Luan runs `&North, `&East, `&South`6, and `&West`7~
`6A major tributary of the Erinin, the Luan flows strongly here, its deep
waters carving a path through the rolling grasslands. The current is swift and
determined, carrying the runoff from the distant mountains toward its eventual
meeting with the great river to the south. The banks are lush with greenery,
and the air is filled with the sound of moving water.`7
~
509 a 6 10 10
D0
~
~
0 0 50982
D1
~
~
0 0 50993
D2
~
~
0 0 53902
D3
~
~
0 0 50991
R
In the Wake of an Army~
     `2It is immediately evident that a large number of troops
have passed through this area, recently.  The terrain has been
beaten and disturbed by great quantities of tracks, and the
foliage has taken a great pounding...`7
~
G
 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
S"""

# 5. Fix 50995 South Exit to 53905
block_50995 = """#50995
`@Rolling Grassland runs `&North, `&East, `&South`6, and `&West`7~
`7Low, wide hilltops roll away toward the horizon, their slopes covered in a 
patchwork of thick grass and stubborn wildflowers. The air is quiet here, 
disturbed only by the steady rustle of the wind and the occasional cry of a 
distant bird. To the north, the terrain continues its gentle rise and fall, 
offering an open view of the vast Andoran countryside.`7
~
509 a 2 10 10
D0
~
~
0 0 50985
D1
~
~
0 0 50996
D2
~
~
0 0 53905
D3
~
~
0 0 50994
R
In the Wake of an Army~
     `2It is immediately evident that a large number of troops
have passed through this area, recently.  The terrain has been
beaten and disturbed by great quantities of tracks, and the
foliage has taken a great pounding...`7
~
G
 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
S"""

rewrite_room(wld537, 53747, block_53747)
rewrite_room(wld537, 53768, block_53768)
rewrite_room(wld468, 46893, block_46893)
rewrite_room(wld509, 50992, block_50992)
rewrite_room(wld509, 50995, block_50995)
