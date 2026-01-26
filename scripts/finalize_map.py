import re
import os

wld_dir = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld"

# --- TEMPLATES ---
generic_plains_desc = """`7Open ground stretches out in every direction, a vast sea of grass 
broken only by the occasional cluster of small leafy trees. The horizon shimmers 
faintly in the heat, and the sky is a wide, pale blue that makes the land feel 
exposed. The air is clear and the view open across the fertile countryside.`7"""

generic_forest_desc = """`2A mix of trees make up the local woodland. Narrow, white-barked specimens 
grow everywhere, and thick, wrinkled oaks are clearly many generations old. 
Occasional stands of paper-barked trees appear haphazardly, and the trees 
themselves come in a variety of forms and sizes. A space of several paces lies 
between everything, allowing for easy passage.`7"""

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

caemlyn_tarvalon_road_desc = """`6This stretch of the road is wide and well-traveled, providing a vital link
between the capital of Andor and the island city of Tar Valon. Paving stones,
worn smooth by years of use, peek through the hard-packed dirt in places.
The surrounding fields and distant forests are alive with the sounds of 
nature, while the road itself remains a firm and reliable path for merchant 
wagons and lone travelers alike.`7"""

cairhien_tv_road_desc = """`6The main highway between Cairhien and Tar Valon travels through the heart of 
the eastern farmlands. This stretch of the road is wide and meticulously 
maintained to handle the massive flow of goods between the two great cities. 
Paving stones peek through the dirt in places, and the traffic is frequent, 
ranging from merchant wagons to riders on urgent business.`7"""

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

def rewrite_room(vnum, new_block):
    zone = vnum // 100
    file_path = os.path.join(wld_dir, f"{zone}.wld")
    if not os.path.exists(file_path): return
    
    with open(file_path, 'r', encoding='latin-1') as f:
        content = f.read()
    
    # Precise block matching
    pattern = rf'^#{vnum}\s*\n(.*?)(?=\n#|\Z)'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    
    if match:
        old_block = match.group(0)
        # Ensure the new block is properly formatted
        clean_new_block = new_block.strip() + "\n"
        content = content.replace(old_block, clean_new_block)
        with open(file_path, 'w', encoding='latin-1') as f:
            f.write(content)
        print(f"Surgically repaired {vnum}")
    else:
        print(f"Could not find {vnum} in {file_path}")

# --- BERRYWOOD AREA (Zone 570) ---
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
`2Tall trees press close here, their branches weaving overhead and turning the light
to a greenish gloom. The air smells of leaf-mold and damp earth, and the undergrowth
snags at boots and cloaks alike.`7
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

rewrite_room(57030, """#57030
`6Farmlands and Fields`7~
`3In the distance, on the horizon, a farmhouse makes a black speck against
the sky on a low hill.  Between here and there, fields of wheat stretch forth,
ever changing with the harvest cycle.  Shimmering and green as they rise up in
the spring, by midsummer they fade to amber waves, and by autumn there is nary
a grain to be found as the gatherers harvest the wheat for the coming winter. 
Some of the fields lie fallow, while others grow.`7
~
570 a 2 10 10
D0
~
~
0 0 57020
D1
~
~
0 0 57031
D2
~
~
0 0 57040
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

rewrite_room(57032, """#57032
`6The Deep Forest`7~
`2Trees crowd together here, their trunks dark with age. Ferns and brambles make the
going slow, and the forest floor is strewn with leaves and snapped twigs.`7
~
570 0 2 10 10
D0
~
~
0 0 57022
D1
~
~
0 0 57033
D2
~
~
0 0 57042
D3
~
~
0 0 57031
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

rewrite_room(57041, """#57041
`6The North Woods`7~
`2The wood is quiet here, the sound of birds muffled and distant, signs of
other animal life sparse.  What trails are present aren't quite what one would
expect game to make - they are too straight, too clear.  Broken branches and
axe-bitten tree stumps make it plain that these paths are frequented not by
animals, but by men.  `7 
~
570 a 3 10 10
D0
~
~
0 0 57031
D1
~
~
0 0 57042
D2
~
~
0 0 57051
D3
~
~
0 0 57040
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

rewrite_room(57022, """#57022
`6Between the Farms`7~
`3On the horizon to the west, a farmhouse makes a black speck against the sky
on a low hill in the midst of fertile fields.  Between here and there, a vast
`@g`2r`@e`2e`@n`3 `@m`2e`@ad`2o`@w`3 stretches out, tall grasses mingled with %w5i#l3d@f2l%o5w@e2r#s3, and the
occasional grove of trees.  To the east, another farmhouse is nestled in the
midst of fields of #g3o#ld3e#n w3h#e3a#t3.  To the north, the land rises and falls in
gently rolling hills, while to the south, the land stretches out in fields and
farmland as far as the eye can see.  A fence is blocking the way south,
protecting a farmhouse with a '1No Trespassing3' sign attached.  `7 
~
570 a 2 10 10
D0
~
~
0 0 57012
D2
~
~
0 0 57032
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

rewrite_room(57042, """#57042
`6Fields and Farmlands`7~
`3Fields of wheat stretch far and wide throughout this region, mingled with
the greens of plains and meadows.  To the west, a dark line of trees draws the
eye toward a hint of forest, and to the south as well.  North, a fence blocks
the way, preventing trespassers from entering a farmstead.  To the east, more
green fields greet the eye in the height of spring and summer, fading to gold
with the autumn.  Somewhere, a meadowlark sings its sad song as it guards its
young amidst the tall grasses.  `7 
~
570 a 2 10 10
D0
~
~
0 0 57032
D2
~
~
0 0 57052
D3
~
~
0 0 57041
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

# --- RIVER SEAM (Zone 509/539) ---
rewrite_room(50983, """#50983
`@Rolling Grassland`7~
`3Tall grass brushes at knees, moving in waves that never seem to repeat
themselves. The horizon looks closer than it is, and the emptiness between is
all grass and air. A rabbit freezes in the weeds, then bolts away in a blur of
brown. A drifting veil of cloud softens the light, turning the world gray for
a heartbeat.`7
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

rewrite_room(53904, """#53904
`6The River Erinin runs `&North `6and `&East`7~
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

rewrite_room(50984, """#50984
`6The Caemlyn - Tar Valon Road runs `&East, `&South`6, and `&West`7~
""" + caemlyn_tarvalon_road_desc + """
~
509 a 11 10 10
D0
~
~
0 0 50974
D1
~
~
0 0 50985
D2
~
~
0 0 50994
D3
~
~
0 0 50983
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

rewrite_room(50993, """#50993
`6The River Erinin runs `&North, `&East, `&South`6, and `&West`7~
""" + erinin_desc + """
~
509 a 6 10 10
D0
~
~
0 0 50983
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
D7
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
S""")

rewrite_room(53903, """#53903
`6The Caemlyn - Tar Valon Road runs `&North, `&West`6, and `&Northeast`7~
""" + caemlyn_tarvalon_road_desc + """
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

# --- DAREIN ---
rewrite_room(46998, """#46998
`*D`6a`&r`7e`6i`*n `7~
`7The village of Darein lies at the foot of the bridge from Tar Valon. The 
village was burned during the Trolloc Wars, sacked by Artur Hawkwing, 
looted during the Hundred Years War and burned again during the Aiel 
War. Every time it has been rebuilt. Red and brown brick houses and shops
	line the stone paved streets. The city of Tar Valon lies to the `&northeast`7, other 
villages are `&east`7 and `6west`7, and `&south`7 lies the open road.
~
469 a 1 10 10
D0
~
~
0 0 46988
D1
~
~
0 0 46999
D2
~
~
0 0 50908
D3
~
~
0 0 46997
D6
~
~
0 0 48603
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

# --- CAIRHIEN ROAD FIXES (Zone 468) ---
rewrite_room(46884, f"""#46884
`6The Cairhien - Tar Valon Road runs `&North, `&East, `&South`6, and `&West`7~
{cairhien_tv_road_desc}
~
468 a 11 10 10
D0
~
~
0 0 46874
D1
~
~
0 0 46885
D2
~
~
0 0 46894
D3
~
~
0 0 46883
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

for v, dirs in [(46883, "North, East, South, and West"), (46894, "North, South, and West")]:
    rewrite_room(v, f"""#{v}
`6The Cairhien - Tar Valon Road runs {dirs}`7~
{cairhien_tv_road_desc}
~
468 a 11 10 10
D0
~
~
0 0 {v-10 if v==46883 else 46884}
D1
~
~
0 0 {v+1}
D2
~
~
0 0 {v+10 if v==46883 else 50804}
D3
~
~
0 0 {v-1}
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

# --- MARADON ROAD ---
for v in range(46960, 46977):
    dirs = ""
    if v == 46960: dirs = "East"
    elif v == 46961: dirs = "South and West"
    elif v == 46971: dirs = "North and East"
    elif v == 46972 or v == 46973 or v == 46974 or v == 46975: dirs = "East and West"
    elif v == 46976: dirs = "West"
    
    name = f"`6The Tar Valon - Maradon Road runs {dirs}`7" if dirs else "`6The Tar Valon - Maradon Road`7"
    rewrite_room(v, f"""#{v}
{name}~
{maradon_road_desc}
~
469 a 11 10 10
D0
...
S""") # This is just a placeholder, I'll use a better logic below
