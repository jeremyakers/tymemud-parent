import re
import os

wld540 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/540.wld"
wld508 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/508.wld"
wld509 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/509.wld"
wld539 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/539.wld"

def rewrite_room(file_path, vnum, new_name=None, new_desc=None):
    with open(file_path, 'r', encoding='latin-1') as f:
        content = f.read()
    
    room_pattern = rf'^#{vnum}\s*\n(.*?)\n(.*?)\n~'
    match = re.search(room_pattern, content, re.MULTILINE | re.DOTALL)
    if match:
        old_name = match.group(1)
        old_desc = match.group(2)
        
        target_name = new_name if new_name else old_name
        target_desc = new_desc if new_desc else old_desc
        
        new_room_content = f"#{vnum}\n{target_name}\n{target_desc}\n~"
        old_block = f"#{vnum}\n{old_name}\n{old_desc}\n~"
        
        new_content = content.replace(old_block, new_room_content)
        with open(file_path, 'w', encoding='latin-1') as f:
            f.write(new_content)
        print(f"Updated {vnum}")
    else:
        print(f"Could not find {vnum}")

generic_plains = """`7Open ground stretches out in every direction, a vast sea of grass 
broken only by the occasional cluster of small leafy trees. The horizon shimmers 
faintly in the heat, and the sky is a wide, pale blue that makes the land feel 
exposed. The air is clear and the view open across the fertile countryside.`7"""

generic_forest = """`2A mix of trees make up the local woodland. Narrow, white-barked specimens 
grow everywhere, and thick, wrinkled oaks are clearly many generations old. 
Occasional stands of paper-barked trees appear haphazardly, and the trees 
themselves come in a variety of forms and sizes. A space of several paces lies 
between everything, allowing for easy passage.`7"""

# Zone 540 Naming Fixes
rewrite_room(wld540, 54086, "`@Braem Wood`7", generic_forest)
rewrite_room(wld540, 54096, "`@Braem Wood`7", generic_forest)

# Zone 508/509/539 Description Fixes
vnums_508 = [50838, 50850, 50860, 50866, 50867, 50886, 50887, 50895, 50897]
for v in vnums_508:
    rewrite_room(wld508, v, new_desc=generic_plains)

vnums_509 = [50903, 50934, 50964, 50972, 50989]
for v in vnums_509:
    rewrite_room(wld509, v, new_desc=generic_plains)

vnums_539 = [53934, 53937, 53970, 53973, 53991]
for v in vnums_539:
    # Check sector for forest/plains
    # 53937, 53970, 53991 are sector 3 (Forest) in audit
    desc = generic_forest if v in [53937, 53970, 53991] else generic_plains
    name = "`@Braem Wood`7" if v in [53937, 53970, 53991] else "`@Rolling Grassland`7"
    rewrite_room(wld539, v, new_name=name, new_desc=desc)
