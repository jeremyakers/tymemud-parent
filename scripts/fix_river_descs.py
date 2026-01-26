import re
import os

wld_dir = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld"

# Templates for high-quality river descriptions
erinin_desc = """`6The mighty River Erinin flows steadily here, its deep blue waters carrying
the commerce of the Westlands. The river is wide and powerful, with a current
that demands respect from even the most seasoned rivermen. Along the banks,
the land is lush and green, and the occasional merchant vessel can be seen
moving slowly along its course.`7"""

luan_desc = """`6A major tributary of the Erinin, the Luan flows strongly here, its deep
waters carving a path through the rolling grasslands. The current is swift and
determined, carrying the runoff from the distant mountains toward its eventual
meeting with the great river to the south. The banks are lush with greenery,
and the air is filled with the sound of moving water.`7"""

alguenya_desc = """`6The Alguenya river flows majestically through the heart of the land, its 
deep blue waters carrying the commerce of the Westlands. To the north, the 
river continues past the towers of Cairhien, while to the south it flows toward 
the Erinin. The current is strong and steady here, and the banks are lined 
with lush vegetation.`7"""

gaelin_desc = """`6The Gaelin river flows smoothly here, its clear waters winding through 
the countryside before eventually joining the Alguenya. Small ripples catch 
the light, breaking it into bright fragments, and the sound of the flow is 
a constant, peaceful murmur against the banks.`7"""

def rewrite_room_desc(vnum, zone, new_desc, new_name=None):
    file_path = os.path.join(wld_dir, f"{zone}.wld")
    if not os.path.exists(file_path): return
    
    with open(file_path, 'r', encoding='latin-1') as f:
        content = f.read()
    
    pattern = rf'^#{vnum}\s*\n(.*?~)\n(.*?~)\n(\d+ .*?\n)'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    
    if match:
        old_name_with_tilde = match.group(1)
        old_desc = match.group(2)
        flags_line = match.group(3)
        
        target_name = f"{new_name}~" if new_name else old_name_with_tilde
        standardized_desc = f"{new_desc}\n~"
        
        old_block = f"#{vnum}\n{old_name_with_tilde}\n{old_desc}\n{flags_line}"
        new_block = f"#{vnum}\n{target_name}\n{standardized_desc}\n{flags_line}"
        
        content = content.replace(old_block, new_block)
        with open(file_path, 'w', encoding='latin-1') as f:
            f.write(content)
        print(f"Fixed description for {vnum}")
    else:
        print(f"Could not match pattern for {vnum}")

# Map of VNUMs to fix (from our river audit)
to_fix = [
    (46891, 468, erinin_desc, "`6The River Erinin`7"),
    (46948, 469, erinin_desc, "`6The River Erinin`7"),
    (50803, 508, erinin_desc, "`6The River Erinin`7"),
    (50814, 508, erinin_desc, "`6The River Erinin`7"),
    (50824, 508, erinin_desc, "`6The River Erinin`7"),
    (50834, 508, erinin_desc, "`6The River Erinin`7"),
    (50844, 508, erinin_desc, "`6The River Erinin`7"),
    (50853, 508, erinin_desc, "`6The River Erinin`7"),
    (50863, 508, erinin_desc, "`6The River Erinin`7"),
    (50873, 508, erinin_desc, "`6The River Erinin`7"),
    (50882, 508, erinin_desc, "`6The River Erinin`7"),
    (50892, 508, erinin_desc, "`6The River Erinin`7"),
    (50982, 509, luan_desc, "`6The Luan`7"),
    (50992, 509, luan_desc, "`6The Luan`7"),
    (50993, 509, luan_desc, "`6The Luan`7"),
    (53704, 537, alguenya_desc, "`6The Alguenya`7"),
    (53714, 537, alguenya_desc, "`6The Alguenya`7"),
    (53754, 537, alguenya_desc, "`6The Alguenya`7"),
    (60700, 607, alguenya_desc, "`6The Alguenya`7"),
    (60829, 608, alguenya_desc, "`6The Alguenya`7"),
    (60890, 608, erinin_desc, "`6The River Erinin`7"),
    (63800, 638, erinin_desc, "`6The River Erinin`7"),
    (63810, 638, erinin_desc, "`6The River Erinin`7"),
    (63811, 638, erinin_desc, "`6The River Erinin`7"),
    (63821, 638, erinin_desc, "`6The River Erinin`7"),
    (63831, 638, erinin_desc, "`6The River Erinin`7")
]

for v, z, d, n in to_fix:
    rewrite_room_desc(v, z, d, n)
