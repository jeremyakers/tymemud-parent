import re
import os

wld_dir = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld"

# Templates for high-quality road descriptions
caemlyn_tarvalon_desc = """`6This stretch of the road is wide and well-traveled, providing a vital link
between the capital of Andor and the island city of Tar Valon. Paving stones,
worn smooth by years of use, peek through the hard-packed dirt in places.
The surrounding fields and distant forests are alive with the sounds of 
nature, while the road itself remains a firm and reliable path for merchant 
wagons and lone travelers alike.`7"""

caemlyn_madding_desc = """`6A broad road travels through the heart of the countryside, its edges 
marked by low stone walls and the occasional boundary fence. To the south, 
the road stretches toward the distant hills of Kintara and the city of Far 
Madding. The air is quiet, save for the gentle rustle of the wind and the 
rhythmic sound of travel along the well-maintained highway.`7"""

caemlyn_aringill_desc = """`6This well-maintained road cuts through the center of the farmlands, its 
surface worn smooth by the passage of countless merchant wagons and 
travelers. On either side, the land is meticulously tended, with rows of crops 
stretching away toward distant farmhouses. The air is clear and the view open, 
revealing the vastness of the Andoran countryside as the road continues 
toward the River Erinin.`7"""

aringill_cairhien_desc = """`6The road between Aringill and Cairhien follows the path carved out near 
the River Alguenya. The hard-packed dirt shows the signs of centuries of 
travel, connecting the busy port of Aringill to the topless towers of 
Cairhien. Merchant traffic is frequent here, and the view of the surrounding 
countryside is open and vast.`7"""

def rewrite_room_desc(vnum, zone, new_desc):
    file_path = os.path.join(wld_dir, f"{zone}.wld")
    if not os.path.exists(file_path): return
    
    with open(file_path, 'r', encoding='latin-1') as f:
        content = f.read()
    
    # Match the room block structure carefully
    # #VNUM \n NAME~ \n DESC~ \n FLAGS
    pattern = rf'^#{vnum}\s*\n(.*?~)\n(.*?~)\n(\d+ .*?\n)'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    
    if match:
        name_line = match.group(1)
        old_desc = match.group(2)
        flags_line = match.group(3)
        
        # Determine name for standardization if needed
        # (Though we already standardized names, let's keep it safe)
        standardized_desc = f"{new_desc}\n~"
        
        old_block = f"#{vnum}\n{name_line}\n{old_desc}\n{flags_line}"
        new_block = f"#{vnum}\n{name_line}\n{standardized_desc}\n{flags_line}"
        
        content = content.replace(old_block, new_block)
        with open(file_path, 'w', encoding='latin-1') as f:
            f.write(content)
        print(f"Fixed description for {vnum}")
    else:
        print(f"Could not match pattern for {vnum}")

# Map of VNUMs to fix (from our audit)
to_fix = [
    (46823, 468, caemlyn_aringill_desc),
    (46928, 469, caemlyn_tarvalon_desc),
    (46949, 469, caemlyn_aringill_desc),
    (46971, 469, caemlyn_aringill_desc),
    (46972, 469, caemlyn_aringill_desc),
    (46974, 469, caemlyn_aringill_desc),
    (46975, 469, caemlyn_aringill_desc),
    (46976, 469, caemlyn_aringill_desc),
    (46997, 469, caemlyn_aringill_desc),
    (50805, 508, caemlyn_tarvalon_desc),
    (50806, 508, caemlyn_tarvalon_desc),
    (50817, 508, caemlyn_tarvalon_desc),
    (50827, 508, caemlyn_tarvalon_desc),
    (50837, 508, caemlyn_tarvalon_desc),
    (50848, 508, caemlyn_tarvalon_desc),
    (50858, 508, caemlyn_tarvalon_desc),
    (50868, 508, caemlyn_tarvalon_desc),
    (50878, 508, caemlyn_tarvalon_desc),
    (50888, 508, caemlyn_tarvalon_desc),
    (50898, 508, caemlyn_tarvalon_desc),
    (50906, 509, caemlyn_tarvalon_desc),
    (50907, 509, caemlyn_tarvalon_desc),
    (50915, 509, caemlyn_tarvalon_desc),
    (50916, 509, caemlyn_tarvalon_desc),
    (50919, 509, caemlyn_tarvalon_desc),
    (50938, 509, caemlyn_tarvalon_desc),
    (50948, 509, caemlyn_tarvalon_desc),
    (50957, 509, caemlyn_tarvalon_desc),
    (50966, 509, caemlyn_tarvalon_desc),
    (50975, 509, caemlyn_tarvalon_desc),
    (50976, 509, caemlyn_tarvalon_desc),
    (50984, 509, caemlyn_tarvalon_desc),
    (50985, 509, caemlyn_tarvalon_desc),
    (50994, 509, caemlyn_tarvalon_desc),
    (53902, 539, caemlyn_tarvalon_desc),
    (53903, 539, caemlyn_tarvalon_desc),
    (53912, 539, caemlyn_tarvalon_desc),
    (53921, 539, caemlyn_tarvalon_desc),
    (53922, 539, caemlyn_tarvalon_desc)
]

for v, z, d in to_fix:
    rewrite_room_desc(v, z, d)
