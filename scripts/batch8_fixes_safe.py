import re
import os

wld540 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/540.wld"
wld508 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/508.wld"
wld509 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/509.wld"
wld539 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/539.wld"

def rewrite_room_safe(file_path, vnum, new_name=None, new_desc=None):
    with open(file_path, 'r', encoding='latin-1') as f:
        content = f.read()
    
    # Match the entire block including the sector line to be safe
    # Pattern: #VNUM \n NAME~ \n DESC~ \n FLAGS_LINE
    pattern = rf'^#{vnum}\s*\n(.*?~)\n(.*?~)\n(\d+ .*?\n)'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    
    if match:
        old_name_with_tilde = match.group(1)
        old_desc_with_tilde = match.group(2)
        flags_line = match.group(3)
        
        target_name = f"{new_name}~" if new_name else old_name_with_tilde
        target_desc = f"{new_desc}\n~" if new_desc else old_desc_with_tilde
        
        old_block = f"#{vnum}\n{old_name_with_tilde}\n{old_desc_with_tilde}\n{flags_line}"
        new_block = f"#{vnum}\n{target_name}\n{target_desc}\n{flags_line}"
        
        new_content = content.replace(old_block, new_block)
        with open(file_path, 'w', encoding='latin-1') as f:
            f.write(new_content)
        print(f"Updated {vnum}")
    else:
        print(f"Could not find {vnum} with expected pattern")

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
rewrite_room_safe(wld540, 54086, "`@Braem Wood`7", generic_forest)
rewrite_room_safe(wld540, 54096, "`@Braem Wood`7", generic_forest)

# Zone 508/509/539 Description Fixes
vnums_508 = [50838, 50850, 50860, 50866, 50867, 50886, 50887, 50895, 50897]
for v in vnums_508:
    rewrite_room_safe(wld508, v, new_desc=generic_plains)

vnums_509 = [50903, 50934, 50964, 50972, 50989]
for v in vnums_509:
    rewrite_room_safe(wld509, v, new_desc=generic_plains)

vnums_539 = [53934, 53937, 53970, 53973, 53991]
for v in vnums_539:
    desc = generic_forest if v in [53937, 53970, 53991] else generic_plains
    name = "`@Braem Wood`7" if v in [53937, 53970, 53991] else "`@Rolling Grassland`7"
    rewrite_room_safe(wld539, v, new_name=name, new_desc=desc)
