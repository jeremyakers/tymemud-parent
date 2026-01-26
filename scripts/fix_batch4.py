import re
import os

wld468 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/468.wld"
wld469 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/469.wld"
wld509 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/509.wld"

def get_block(vnum, content):
    pattern = rf'^#{vnum}\s*\n(.*?)(?=\n#|\Z)'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    return match.group(0) if match else None

# Fix 468 road names with directions
with open(wld468, 'r', encoding='latin-1') as f: content = f.read()
for v, dirs in [(46883, "North, East, South, and West"), (46884, "North, East, South, and West"), (46894, "North, South, and West")]:
    old = get_block(v, content)
    if not old: continue
    new = re.sub(r'^(#\d+\n).*?~', rf'\1`6The Cairhien - Tar Valon Road runs {dirs}~', old, flags=re.MULTILINE | re.DOTALL, count=1)
    content = content.replace(old, new)
with open(wld468, 'w', encoding='latin-1') as f: f.write(content)

# Fix 469 river names
with open(wld469, 'r', encoding='latin-1') as f: content = f.read()
for v in [46968, 46969, 46999]:
    old = get_block(v, content)
    if not old: continue
    new = re.sub(r'^(#\d+\n).*?~', rf'\1`6The River Erinin`7~', old, flags=re.MULTILINE | re.DOTALL, count=1)
    content = content.replace(old, new)
# Fix 469 Maradon road names (remove old placeholder parts)
for v in range(46960, 46977):
    old = get_block(v, content)
    if not old: continue
    # Re-standardize the name line to be clean
    # directions for 46960-46976? 
    # 46960 E, 46961 S/W, 46971 N/E, 46972 E/W, 46973 E/W, 46974 E/W, 46975 E/W, 46976 W
    dirs = ""
    if v == 46960: dirs = "East"
    elif v == 46961: dirs = "South and West"
    elif v == 46971: dirs = "North and East"
    elif v == 46972 or v == 46973 or v == 46974 or v == 46975: dirs = "East and West"
    elif v == 46976: dirs = "West"
    
    if dirs:
        new_name = f"`6The Tar Valon - Maradon Road runs {dirs}`7~"
    else:
        new_name = "`6The Tar Valon - Maradon Road`7~"
    
    new = re.sub(r'^(#\d+\n).*?~', rf'\1{new_name}', old, flags=re.MULTILINE | re.DOTALL, count=1)
    # Also clean up "builder" placeholder in 46962-46970 (Sector 2 rooms)
    if v >= 46962 and v <= 46970:
        new = new.replace("The Builder Road", "Open Plains").replace("builder", "plains")
    content = content.replace(old, new)
with open(wld469, 'w', encoding='latin-1') as f: f.write(content)

# Fix 509 Dragonmount road names
with open(wld509, 'r', encoding='latin-1') as f: content = f.read()
for v, dirs in [(50906, "East and South"), (50907, "North and West"), (50915, "East"), (50916, "North and West")]:
    old = get_block(v, content)
    if not old: continue
    new = re.sub(r'^(#\d+\n).*?~', rf'\1`6The Tar Valon - Dragonmount Road runs {dirs}`7~', old, flags=re.MULTILINE | re.DOTALL, count=1)
    content = content.replace(old, new)
with open(wld509, 'w', encoding='latin-1') as f: f.write(content)

print("Batch 4 fixes complete (Naming truth and cleanup)")
