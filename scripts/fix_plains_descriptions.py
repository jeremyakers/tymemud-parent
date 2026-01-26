import re
import os

wld468 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/468.wld"
wld469 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/469.wld"

def rewrite_desc(file_path, vnum, new_desc):
    with open(file_path, 'r', encoding='latin-1') as f:
        content = f.read()
    
    pattern = rf'#({vnum})\n(.*?)\n(.*?)\n(.*?)\n'
    # Actually, let's find the description block between the first and second ~
    room_pattern = rf'^#{vnum}\s*\n(.*?)\n(.*?)\n~'
    match = re.search(rf'^#{vnum}\s*\n(.*?)\n(.*?)\n~', content, re.MULTILINE | re.DOTALL)
    if match:
        name_line = match.group(1)
        old_desc = match.group(2)
        
        # New description with standard formatting
        new_room_content = f"#{vnum}\n{name_line}\n{new_desc}\n~"
        
        # Simple replacement
        old_block = f"#{vnum}\n{name_line}\n{old_desc}\n~"
        content = content.replace(old_block, new_room_content)
        
        with open(file_path, 'w', encoding='latin-1') as f:
            f.write(content)
        print(f"Rewrote {vnum} description")
    else:
        print(f"Could not find {vnum}")

generic_plains = """`7Open ground stretches out in every direction, a vast sea of grass 
broken only by the occasional cluster of small leafy trees. The horizon shimmers 
faintly in the heat, and the sky is a wide, pale blue that makes the land feel 
exposed. The air is clear and the view open across the fertile countryside.`7"""

vnums_468 = [46808, 46836, 46846, 46856, 46877]
vnums_469 = [46900, 46922, 46923, 46933, 46934, 46945, 46980]

for v in vnums_468:
    rewrite_desc(wld468, v, generic_plains)

for v in vnums_469:
    rewrite_desc(wld469, v, generic_plains)
