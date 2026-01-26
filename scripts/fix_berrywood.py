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

# --- FIXING BERRYWOOD 57021 & 57031 ---

# 57021 Fix: Correct D5 flags and ensure all exits bidirectional
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
0 0 61100
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

# 57031 Fix: Ensure full bidirectional grid connections
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
