import re
import os

wld468 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/468.wld"
wld469 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/469.wld"

def rewrite_room(file_path, vnum, new_block):
    with open(file_path, 'r', encoding='latin-1') as f:
        content = f.read()
    pattern = rf'^#{vnum}\s*\n(.*?)(?=\n#|\Z)'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    if match:
        old_block = match.group(0)
        new_content = content.replace(old_block, new_block)
        with open(file_path, 'w', encoding='latin-1') as f:
            f.write(new_content)
        print(f"Rewrote {vnum}")
    else:
        print(f"Could not find {vnum}")

# Corrected 46820
block_46820 = """#46820
`6The Luagde - Shol Arbela Road runs `&North `6and `&Southwest`7~
`6The road to Shol Arbela stretches north from the Luagde junction.
Paving stones, worn by generations of use, provide a firm surface for the
merchant wagons and lone riders that frequent this route. To the southwest,
the road continues toward the junction at Luagde, while to the north it
continues toward the Borderlands. The view is open and vast, revealing the
breadth of the Tar Valon countryside.`7
~
468 a 11 10 10
D0
~
~
0 0 46810
D1
~
~
0 0 46821
D2
~
~
0 0 46830
D3
~
~
0 0 46929
D9
~
~
0 0 46939
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

rewrite_room(wld468, 46820, block_46820)
rewrite_room(wld469, 46939, block_46939)
