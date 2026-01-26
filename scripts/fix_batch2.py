import re
import os

wld468 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/468.wld"
wld469 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/469.wld"
wld509 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/509.wld"
wld537 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/537.wld"
wld570 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/570.wld"

# Templates
maradon_desc = """`6This ancient highway stretches through the northern borderlands, connecting 
the great city of Tar Valon to the distant city of Maradon. The road is 
constructed of heavy, weathered stones, laid down by builders whose names 
have been lost to history. To the north, the terrain grows increasingly wild 
as it approaches the Blight, while the road itself remains a vital artery 
for commerce and the defense of the realm.`7"""

dragonmount_desc = """`6This well-worn road leads away from the bridges of Tar Valon, heading west 
toward the jagged shadow of Dragonmount. The peak loomes large on the horizon, 
a constant reminder of the Breaking. The air is cool and sharp this close to 
the mountains, and the road carries travelers past isolated farmsteads and 
sparse woodlands at the base of the Great Peak.`7"""

cairhien_tv_desc = """`6The main highway between Cairhien and Tar Valon travels through the heart of 
the eastern farmlands. This stretch of the road is wide and meticulously 
maintained to handle the massive flow of goods between the two great cities. 
Paving stones peek through the dirt in places, and the traffic is frequent, 
ranging from merchant wagons to riders on urgent business.`7"""

def get_block(vnum, content):
    pattern = rf'^#{vnum}\s*\n(.*?)(?=\n#|\Z)'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    return match.group(0) if match else None

# 1. Clean up 57022 duplicate lines
with open(wld570, 'r', encoding='latin-1') as f: content = f.read()
old = get_block(57022, content)
if old:
    new = old.replace('570 0 2 10 10', '').replace('\n\n', '\n')
    content = content.replace(old, new)
with open(wld570, 'w', encoding='latin-1') as f: f.write(content)

# 2. Rename Maradon Road (46976-46960)
with open(wld469, 'r', encoding='latin-1') as f: content = f.read()
for v in range(46960, 46977):
    old = get_block(v, content)
    if not old: continue
    # Extract directions from current name if they exist
    name_match = re.search(r'`6The Cairhien - Tar Valon Road runs (.*?)~', old)
    dirs = name_match.group(1) if name_match else ""
    new_name = f"`6The Tar Valon - Maradon Road runs {dirs}" if dirs else "`6The Tar Valon - Maradon Road`7"
    if not new_name.endswith('~'): new_name += '~'
    
    # Simple replacement for name and desc
    lines = old.split('\n')
    lines[1] = new_name
    # Update description (line 2 until next ~)
    # This is safer:
    new_block = re.sub(r'^(#\d+\n).*?~\n.*?~', rf'\1{new_name}\n{maradon_desc}\n~', old, flags=re.MULTILINE | re.DOTALL)
    content = content.replace(old, new_block)
with open(wld469, 'w', encoding='latin-1') as f: f.write(content)

# 3. Rename Dragonmount Road (46997-50915)
# Zone 469 part
with open(wld469, 'r', encoding='latin-1') as f: content = f.read()
for v in range(46997, 47000):
    old = get_block(v, content)
    if not old: continue
    new_name = "`6The Tar Valon - Dragonmount Road`7~"
    new_block = re.sub(r'^(#\d+\n).*?~\n.*?~', rf'\1{new_name}\n{dragonmount_desc}\n~', old, flags=re.MULTILINE | re.DOTALL)
    content = content.replace(old, new_block)
with open(wld469, 'w', encoding='latin-1') as f: f.write(content)

# Zone 509 part
with open(wld509, 'r', encoding='latin-1') as f: content = f.read()
for v in [50906, 50907, 50915, 50916]:
    old = get_block(v, content)
    if not old: continue
    new_name = "`6The Tar Valon - Dragonmount Road`7~"
    new_block = re.sub(r'^(#\d+\n).*?~\n.*?~', rf'\1{new_name}\n{dragonmount_desc}\n~', old, flags=re.MULTILINE | re.DOTALL)
    content = content.replace(old, new_block)
with open(wld509, 'w', encoding='latin-1') as f: f.write(content)

# 4. Fix Cairhien - Tar Valon Road (46883, 46884, 46894)
with open(wld468, 'r', encoding='latin-1') as f: content = f.read()
# 46884 resector and rename
old = get_block(46884, content)
new = f"""#46884
`6The Cairhien - Tar Valon Road`7~
{cairhien_tv_desc}
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
S"""
content = content.replace(old, new)

# 46883 and 46894 naming/desc
for v in [46883, 46894]:
    old = get_block(v, content)
    if not old: continue
    new_name = "`6The Cairhien - Tar Valon Road`7~"
    new_block = re.sub(r'^(#\d+\n).*?~\n.*?~', rf'\1{new_name}\n{cairhien_tv_desc}\n~', old, flags=re.MULTILINE | re.DOTALL)
    content = content.replace(old, new_block)
with open(wld468, 'w', encoding='latin-1') as f: f.write(content)

print("Batch 2 fixes complete.")
