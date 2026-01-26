import re
import os

wld_dir = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld"

# Templates for descriptions
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

def get_full_content(file_path):
    with open(file_path, 'r', encoding='latin-1') as f:
        return f.read()

def rewrite_room(vnum, new_block):
    zone = vnum // 100
    file_path = os.path.join(wld_dir, f"{zone}.wld")
    content = get_full_content(file_path)
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

# --- 1. Tar Valon - Maradon Road (46960-46976) ---
# Note: I'll only fix the endpoints and a few key rooms for this batch to be safe.
for v in [46960, 46961, 46971, 46972, 46973, 46974, 46975, 46976]:
    dirs = ""
    if v == 46960: dirs = "East"
    elif v == 46961: dirs = "South and West"
    elif v == 46971: dirs = "North and East"
    elif v == 46972: dirs = "East and West"
    elif v == 46973: dirs = "East and West"
    elif v == 46974: dirs = "East and West"
    elif v == 46975: dirs = "East and West"
    elif v == 46976: dirs = "West"
    
    name = f"`6The Tar Valon - Maradon Road runs {dirs}`7" if dirs else "`6The Tar Valon - Maradon Road`7"
    
    # We need to preserve exits, so we'll just update name and desc.
    file_path = os.path.join(wld_dir, "469.wld")
    content = get_full_content(file_path)
    pattern = rf'^#{v}\s*\n(.*?~)\n(.*?~)\n'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    if match:
        old_name = match.group(1)
        old_desc = match.group(2)
        new_name_tilde = f"{name}~"
        new_desc_tilde = f"{maradon_desc}\n~"
        
        # Surgical replacement within the file
        content = content.replace(f"#{v}\n{old_name}\n{old_desc}\n", f"#{v}\n{new_name_tilde}\n{new_desc_tilde}\n")
        with open(file_path, 'w', encoding='latin-1') as f:
            f.write(content)
        print(f"Renamed Maradon road room {v}")

# --- 2. Tar Valon - Dragonmount Road (46997-50915) ---
for v in [46997, 50906, 50907, 50915, 50916]:
    z = v // 100
    name = "`6The Tar Valon - Dragonmount Road`7"
    file_path = os.path.join(wld_dir, f"{z}.wld")
    content = get_full_content(file_path)
    pattern = rf'^#{v}\s*\n(.*?~)\n(.*?~)\n'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    if match:
        old_name = match.group(1)
        old_desc = match.group(2)
        content = content.replace(f"#{v}\n{old_name}\n{old_desc}\n", f"#{v}\n{name}~\n{dragonmount_desc}\n~\n")
        with open(file_path, 'w', encoding='latin-1') as f:
            f.write(content)
        print(f"Renamed Dragonmount road room {v}")

# --- 3. Darein Restoration (46998) ---
darein_block = """#46998
`*D`6a`&r`7e`6i`*n `7~
`7The village of Darein lies at the foot of the bridge from Tar Valon. The 
village was burned during the Trolloc Wars, sacked by Artur Hawkwing, 
looted during the Hundred Years War and burned again during the Aiel 
War. Every time it has been rebuilt. Red and brown brick houses and shops
	line the stone paved streets. The city of Tar Valon lies to the `&northeast`7, other 
villages are `&east`7 and `6west`7, and `&south`7 lies the open road.`7
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
rewrite_room(46998, darein_block)

# --- 4. Cairhien Road fix (46884 re-sector) ---
# Room 46884: Change sector to 11
file_path = os.path.join(wld_dir, "468.wld")
content = get_full_content(file_path)
pattern = rf'^#46884\s*\n(.*?~)\n(.*?~)\n(\d+ a )(\d+)'
match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
if match:
    # Set sector to 11, update name/desc
    new_block = f"""#46884
`6The Cairhien - Tar Valon Road runs North, East, South, and West`7~
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
    # Replace whole block
    block_pattern = rf'^#46884\s*\n(.*?)(?=\n#|\Z)'
    old_block = re.search(block_pattern, content, re.MULTILINE | re.DOTALL).group(0)
    content = content.replace(old_block, new_block)
    with open(file_path, 'w', encoding='latin-1') as f:
        f.write(content)
    print("Re-sectored and updated 46884")

# Update 46883 and 46894
for v in [46883, 46894]:
    name = "`6The Cairhien - Tar Valon Road`7"
    content = get_full_content(file_path)
    pattern = rf'^#{v}\s*\n(.*?~)\n(.*?~)\n'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    if match:
        old_name = match.group(1)
        old_desc = match.group(2)
        content = content.replace(f"#{v}\n{old_name}\n{old_desc}\n", f"#{v}\n{name}~\n{cairhien_tv_desc}\n~\n")
        with open(file_path, 'w', encoding='latin-1') as f:
            f.write(content)
        print(f"Standardized road room {v}")
