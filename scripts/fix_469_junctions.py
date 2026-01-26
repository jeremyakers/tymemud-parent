import re
import os

wld469 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/469.wld"

with open(wld469, 'r', encoding='latin-1') as f:
    content = f.read()

def rewrite_room(vnum, new_block):
    global content
    # Find block starting with #VNUM until the next # or end
    pattern = rf'^#{vnum}\s*\n(.*?)(?=\n#|\Z)'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    if match:
        old_block = match.group(0)
        content = content.replace(old_block, new_block)
        print(f"Rewrote {vnum}")
    else:
        print(f"Could not find {vnum}")

# Corrected 46929
block_46929 = """#46929
`@Rolling Grassland`7~
`7Open ground stretches out, broken only by wildflowers and stubborn scrub.
The wind moves steadily across the land, and far things look deceptively close.
To the south, the main road junction at Luagde is visible, with the busy
sounds of travelers and merchant wagons carrying on the breeze.`7
~
469 a 2 10 10
D0
~
~
0 0 46919
D1
~
~
0 0 46820
D2
~
~
0 0 46939
D3
~
~
0 0 46928
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

# Corrected 46939
block_46939 = """#46939
`6The Luagde - Chachin/Shol Arbela Road runs `&South, `&Northeast`6, and `&Northwest`7~
`6The main highway reaches a major split here in the northern farmlands of
Tar Valon. To the northwest, the road leads toward the village of Chachin,
while to the northeast it branches toward Shol Arbela. To the south, the
well-traveled path continues toward the village of Luagde and the eventual
turn toward the city's western bridges. The traffic is frequent, with merchant
wagons and lone riders frequenting this vital junction.`7
~
469 a 11 10 10
D0
~
~
0 0 46929
D1
~
~
0 0 46830
D2
~
~
0 0 46949
D3
~
~
0 0 46938
D6
~
~
0 0 46820
D7
~
~
0 0 46928
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

rewrite_room(46929, block_46929)
rewrite_room(46939, block_46939)

with open(wld469, 'w', encoding='latin-1') as f:
    f.write(content)
