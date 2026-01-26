import re
import os

wld468 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/468.wld"
wld537 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/537.wld"
wld509 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/509.wld"
wld539 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/539.wld"
wld569 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/569.wld"

# templates
erinin_desc = """`6The mighty River Erinin flows steadily here, its deep blue waters carrying
the commerce of the Westlands. The river is wide and powerful, with a current
that demands respect from even the most seasoned rivermen. Along the banks,
the land is lush and green, and the occasional merchant vessel can be seen
moving slowly along its course.`7"""

luan_desc = """`6A major tributary of the Erinin, the Luan flows strongly here, its deep
waters carving a path through the rolling grasslands. The current is swift and
determined, carrying the runoff from the distant mountains toward its eventual
meeting with the great river to the south. The banks are lush with greenery,
and the air is filled with the sound of moving water.`7"""

def get_block(vnum, content):
    pattern = rf'^#{vnum}\s*\n(.*?)(?=\n#|\Z)'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    return match.group(0) if match else None

def fix_53768():
    with open(wld537, 'r', encoding='latin-1') as f: content = f.read()
    old_block = get_block(53768, content)
    new_block = """#53768
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
    with open(wld537, 'w', encoding='latin-1') as f: f.write(content.replace(old_block, new_block))

def fix_seam_509_539():
    with open(wld509, 'r', encoding='latin-1') as f: c509 = f.read()
    with open(wld539, 'r', encoding='latin-1') as f: c539 = f.read()
    
    # 50992 S-> 53902
    old = get_block(50992, c509)
    new = rf"""#50992
`6The Luan runs `&North, `&East, `&South`6, and `&West`7~
{luan_desc}
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
    c509 = c509.replace(old, new)
    
    # 53902 N-> 50992
    old = get_block(53902, c539)
    new = rf"""#53902
`6The Caemlyn - Tar Valon Road runs `&North, `&East`6, and `&South`7~
`6This stretch of the road is wide and well-traveled, providing a vital link
between the capital of Andor and the island city of Tar Valon. Paving stones,
worn smooth by years of use, peek through the hard-packed dirt in places.
The surrounding fields and distant forests are alive with the sounds of 
nature, while the road itself remains a firm and reliable path for merchant 
wagons and lone travelers alike.`7
~
539 a 11 10 10
D0
~
~
0 0 50992
D1
~
~
0 0 53903
D2
~
~
0 0 53912
D3
~
~
0 0 53901
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
    c539 = c539.replace(old, new)
    
    # 50993 S-> 53903
    old = get_block(50993, c509)
    new = rf"""#50993
`6The Luan runs `&East, `&South`6, and `&West`7~
{luan_desc}
~
509 a 6 10 10
D1
~
~
0 0 50994
D2
~
~
0 0 53903
D3
~
~
0 0 50992
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
    c509 = c509.replace(old, new)
    
    # 53903 N-> 50993
    old = get_block(53903, c539)
    new = rf"""#53903
`6The Caemlyn - Tar Valon Road runs `&North, `&West`6, and `&Northeast`7~
`6This stretch of the road is wide and well-traveled, providing a vital link
between the capital of Andor and the island city of Tar Valon. Paving stones,
worn smooth by years of use, peek through the hard-packed dirt in places.
The surrounding fields and distant forests are alive with the sounds of 
nature, while the road itself remains a firm and reliable path for merchant 
wagons and lone travelers alike.`7
~
539 a 11 10 10
D0
~
~
0 0 50993
D2
~
~
0 0 53913
D3
~
~
0 0 53902
D6
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
    c539 = c539.replace(old, new)
    
    # 50994 S-> 53904
    old = get_block(50994, c509)
    new = rf"""#50994
`6The Caemlyn - Tar Valon Road runs `&North, `&South`6, and `&Southwest`7~
`6This stretch of the road is wide and well-traveled, providing a vital link
between the capital of Andor and the island city of Tar Valon. Paving stones,
worn smooth by years of use, peek through the hard-packed dirt in places.
The surrounding fields and distant forests are alive with the sounds of 
nature, while the road itself remains a firm and reliable path for merchant 
wagons and lone travelers alike.`7
~
509 a 11 10 10
D0
~
~
0 0 50984
D1
~
~
0 0 50995
D2
~
~
0 0 53904
D3
~
~
0 0 50993
D9
~
~
0 0 53903
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
    c509 = c509.replace(old, new)
    
    # 53904 N-> 50994
    old = get_block(53904, c539)
    new = rf"""#53904
`6The Luan runs `&North `6and `&East`7~
{luan_desc}
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
S"""
    c539 = c539.replace(old, new)
    
    # 50995 S-> 53905
    old = get_block(50995, c509)
    new = rf"""#50995
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
    c509 = c509.replace(old, new)
    
    # 53905 N-> 50995
    old = get_block(53905, c539)
    new = rf"""#53905
`6The Luan runs `&North, `&East`6, and `&West`7~
{luan_desc}
~
539 a 6 10 10
D0
~
~
0 0 50995
D1
~
~
0 0 53906
D2
~
~
0 0 53915
D3
~
~
0 0 53904
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
    c539 = c539.replace(old, new)
    
    with open(wld509, 'w', encoding='latin-1') as f: f.write(c509)
    with open(wld539, 'w', encoding='latin-1') as f: f.write(c539)

def fix_46893():
    with open(wld468, 'r', encoding='latin-1') as f: content = f.read()
    old_block = get_block(46893, content)
    new_block = rf"""#46893
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
    with open(wld468, 'w', encoding='latin-1') as f: f.write(content.replace(old_block, new_block))

fix_53768()
fix_seam_509_539()
fix_46893()
print("Applied fixes for 53768, 509/539 seam, and 46893 naming/hallucination")
