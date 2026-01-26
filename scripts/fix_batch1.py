import re
import os

wld509 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/509.wld"
wld539 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/539.wld"
wld570 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/570.wld"

def get_block(vnum, content):
    pattern = rf'^#{vnum}\s*\n(.*?)(?=\n#|\Z)'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    return match.group(0) if match else None

# Fix 50983 missing S
with open(wld509, 'r', encoding='latin-1') as f: content = f.read()
old = get_block(50983, content)
if old and not old.strip().endswith('\nS'):
    new = old.rstrip() + '\nS'
    content = content.replace(old, new)
with open(wld509, 'w', encoding='latin-1') as f: f.write(content)

# Fix 53904 missing S
with open(wld539, 'r', encoding='latin-1') as f: content = f.read()
old = get_block(53904, content)
if old and not old.strip().endswith('\nS'):
    new = old.rstrip() + '\nS'
    content = content.replace(old, new)
with open(wld539, 'w', encoding='latin-1') as f: f.write(content)

# Fix 570 exits
with open(wld570, 'r', encoding='latin-1') as f: content = f.read()

# 57032 exits
old = get_block(57032, content)
new = """#57032
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
S"""
content = content.replace(old, new)

# Reciprocal 57022 D2 -> 57032
old = get_block(57022, content)
new = old.replace('~', '~\n570 a 2 10 10\nD2\n~\n~\n0 0 57032', 1) # This is a bit risky, let's be more precise
# Actually 57022 is missing the sector line!
pattern = rf'^#57022\s*\n(.*?~)\n(.*?~)\n'
match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
if match:
    old_full = match.group(0)
    new_full = old_full + "570 a 2 10 10\nD2\n~\n~\n0 0 57032\n"
    content = content.replace(old_full, new_full)

# Reciprocal 57042 D0 -> 57032
old = get_block(57042, content)
new = old.replace('570 a 2 10 10', '570 a 2 10 10\nD0\n~\n~\n0 0 57032')
content = content.replace(old, new)

# Reciprocal 57031 D1 -> 57032
old = get_block(57031, content)
new = old.replace('570 0 2 10 10', '570 0 2 10 10\nD1\n~\n~\n0 0 57032')
content = content.replace(old, new)

with open(wld570, 'w', encoding='latin-1') as f: f.write(content)
print("Batch 1 fixes complete.")
