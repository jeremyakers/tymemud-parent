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

jangai_desc = """`6The well-worn Jangai road crests, revealing a magnificent view of the
fabled topless towers of Cairhien rising defiantly beside the eastern bank of 
the Alguenya river. Paving stones, worn by generations of use, provide a 
firm surface for the merchant wagons and lone riders that frequent this 
vital route.`7"""

def rewrite_room_desc(vnum, zone, new_desc):
    file_path = os.path.join(wld_dir, f"{zone}.wld")
    if not os.path.exists(file_path): return
    
    with open(file_path, 'r', encoding='latin-1') as f:
        content = f.read()
    
    pattern = rf'^#{vnum}\s*\n(.*?~)\n(.*?~)\n(\d+ .*?\n)'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    
    if match:
        name_line = match.group(1)
        old_desc = match.group(2)
        flags_line = match.group(3)
        
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
    (46833, 468, caemlyn_aringill_desc),
    (46851, 468, caemlyn_aringill_desc),
    (46895, 468, caemlyn_tarvalon_desc),
    (53746, 537, jangai_desc),
    (56735, 567, aringill_cairhien_desc),
    (60889, 608, aringill_cairhien_desc)
]

for v, z, d in to_fix:
    rewrite_room_desc(v, z, d)
