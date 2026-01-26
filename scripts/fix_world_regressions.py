import re
import os

wld_file = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/468.wld"

with open(wld_file, 'r', encoding='latin-1') as f:
    content = f.read()

def get_good_block(vnum):
    if vnum == 46851:
        return """#46851
`6The Road`7~
`3Rocky hills divide two villages from one another. The land is
useless for farming. Weeds have made a home among the rocks and
are the only source of vegetation. North is the `^River Erinin`3
The `6road`3 lies just south of here, and both east and west
lead towards `8v`&i`8ll`&a`8g`&e`8s.`0
~
468 a 11 10 10
D1
~
~
0 0 46852
D2
~
~
0 0 46861
D3
~
~
0 0 46850
D6
~
~
0 0 46841
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
    elif vnum == 46883:
        return """#46883
`6The Road`7~
`3F`#a`3rmh`#ou`3s`#e`3s and `1b`7a`1rns `3are scattered throughout this 
area. Crops of `#corn `3and `3wh`#ea`3t dot the ground. Men 
can be seen working in the fields. Roads wind to 
the north and west, and the `^River Erinin `3lay close 
to the east.`0
~
468 a 11 10 10
D0
~
~
0 0 46873
D1
~
~
0 0 46884
D2
~
~
0 0 46893
D3
~
~
0 0 46882
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
    return None

def fix_room(vnum, content):
    pattern = rf'^#{vnum}\s*\n(.*?)(?=\n#|\Z)'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    if not match: 
        print(f"Could not find # {vnum}")
        return content
    old_block = match.group(0)
    new_block = get_good_block(vnum)
    if new_block:
        print(f"Replacing {vnum}")
        return content.replace(old_block, new_block)
    return content

content = fix_room(46851, content)
content = fix_room(46883, content)

with open(wld_file, 'w', encoding='latin-1') as f:
    f.write(content)
