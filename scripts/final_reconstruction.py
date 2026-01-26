import re
import os

wld468 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/468.wld"
wld469 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/469.wld"
wld509 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/509.wld"
wld539 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/539.wld"
wld570 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/570.wld"

def get_block(vnum, content):
    pattern = rf'^#{vnum}\s*\n(.*?)(?=\n#|\Z)'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    return match.group(0) if match else None

# --- BERRYWOOD FIXES ---
with open(wld570, 'r', encoding='latin-1') as f: c570 = f.read()

# 57021: Move interior exit to D5, point D2 to 57031
old = get_block(57021, c570)
new = old.replace('D2\n~\n~\n1 0 61100', 'D2\n~\n~\n0 0 57031\nD5\n~\n~\n1 0 61100')
c570 = c570.replace(old, new)

# 57031: Full bidirectional grid connections
old = get_block(57031, c570)
new = """#57031
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
S"""
c570 = c570.replace(old, new)

# Neighbors of 57031 pointing back
for v, d, dest in [(57030, 'D1', 57031), (57032, 'D3', 57031), (57041, 'D0', 57031)]:
    old = get_block(v, c570)
    if d not in old:
        new = old.replace('S', f'{d}\n~\n~\n0 0 {dest}\nS')
        c570 = c570.replace(old, new)

with open(wld570, 'w', encoding='latin-1') as f: f.write(c570)

# --- DAREIN REVERT ---
with open(wld469, 'r', encoding='latin-1') as f: c469 = f.read()
old = get_block(46998, c469)
new = """#46998
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
S"""
c469 = c469.replace(old, new)
with open(wld469, 'w', encoding='latin-1') as f: f.write(c469)

# --- RIVER/HOLE FIXES ---
with open(wld509, 'r', encoding='latin-1') as f: c509 = f.read()
with open(wld539, 'r', encoding='latin-1') as f: c539 = f.read()

# 50983 Reciprocals
for v, d in [(50984, 'D3'), (50993, 'D0')]:
    old = get_block(v, c509)
    if d not in old:
        new = old.replace('S', f'{d}\n~\n~\n0 0 50983\nS')
        c509 = c509.replace(old, new)

# 53904 Reciprocals
old = get_block(53903, c539)
if 'D1' not in old:
    new = old.replace('S', 'D1\n~\n~\n0 0 53904\nS')
    c539 = c539.replace(old, new)

old = get_block(50993, c509)
if 'D7' not in old:
    new = old.replace('S', 'D7\n~\n~\n0 0 53904\nS')
    c509 = c509.replace(old, new)

with open(wld509, 'w', encoding='latin-1') as f: f.write(c509)
with open(wld539, 'w', encoding='latin-1') as f: f.write(c539)

print("Final reconstruction batch complete.")
