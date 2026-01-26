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

# --- FIXING 53903 & 53904 ---
rewrite_room(53903, """#53903
`6The Caemlyn - Tar Valon Road runs North, West, and Northeast`7~
`6This stretch of the road is wide and well-traveled, providing a vital link
through the countryside. Paving stones, worn by years of use, peek through the 
hard-packed dirt in places. The surrounding fields are alive with the sounds 
of nature, while the road itself remains a firm and reliable path for merchant 
wagons and lone travelers alike.`7
~
539 a 11 10 10
D0
~
~
0 0 50993
D1
~
~
0 0 53904
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
S""")

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

# --- FIXING 50982 & 50983 ---
rewrite_room(50982, """#50982
`6The Luan`7~
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
0 0 50972
D1
~
~
0 0 50983
D2
~
~
0 0 50992
D3
~
~
0 0 50981
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

# --- FIXING BERRYWOOD 57021 & 57031 ---
rewrite_room(57021, """#57021
`6The `%B`5err`@y`2wo`5o`%d`6 Farm`7~
`3This land is rich and `@f`2e`@r`2t`@i`2l`@e`3, filled with leagues and leagues of thriving
fields of wheat, interspersed with bright clouds of `%l`5a`&v`7en`&d`5e`%r`3 and `#m`3u`#s`3t`#a`3r`#d`3.  In
the midst of it all, there is a farmhouse, which looks to be newly whitewashed,
with a broad front porch featuring a pair of rocking chairs.  There is a barn
behind the house, and off to the side is a distillery.  Further beyond that,
`%g`5ra`@p`2ev`@i`5ne`%s`3 grow in somewhat sandier soil, strung up around slim sticks and
along strings so that their vines can grow unhindered.  Closer to the house,
neat rows of vegetables grow in a vast garden, including potatoes, squash,
cabbage, tomatoes, and even rows of `!s`1tra`@w`2ber`!r`1ie`@s`3, all growing in their proper
seasons.  This is the Berrywood farm, and they are famous for their heady
Berrywood Wines, and are one of the more prosperous farming families.`7
~
570 0 2 10 10
D0
~
~
0 0 57011
D1
~
~
0 0 57022
D2
~
~
0 0 57031
D3
~
~
0 0 57020
D5
~
~
1 0 61100
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

rewrite_room(57031, """#57031
`6The Deep Forest`7~
`2A mix of trees make up the local woodland. Narrow, white-barked specimens 
grow everywhere, and thick, wrinkled oaks are clearly many generations old. 
Occasional stands of paper-barked trees appear haphazardly, and the trees 
themselves come in a variety of forms and sizes. A space of several paces lies 
between everything, allowing for easy passage.`7
~
570 0 2 10 10
D0
~
~
0 0 57021
D1
~
~
0 0 57032
D2
~
~
0 0 57041
D3
~
~
0 0 57030
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
