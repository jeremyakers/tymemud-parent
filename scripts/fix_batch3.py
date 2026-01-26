import re
import os

wld469 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/469.wld"
wld567 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/567.wld"
wld638 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/638.wld"

erinin_desc = """`6The mighty River Erinin flows steadily here, its deep blue waters carrying
the commerce of the Westlands. The river is wide and powerful, with a current
that demands respect from even the most seasoned rivermen. Along the banks,
the land is lush and green, and the occasional merchant vessel can be seen
moving slowly along its course.`7"""

road_desc = """`6This stretch of the road is wide and well-traveled, providing a vital link
through the countryside. Paving stones, worn by years of use, peek through the 
hard-packed dirt in places. The surrounding fields are alive with the sounds 
of nature, while the road itself remains a firm and reliable path for merchant 
wagons and lone travelers alike.`7"""

def get_block(vnum, content):
    pattern = rf'^#{vnum}\s*\n(.*?)(?=\n#|\Z)'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    return match.group(0) if match else None

# Fix 469 river rooms that got road descs
with open(wld469, 'r', encoding='latin-1') as f: content = f.read()
for v in [46968, 46969, 46999]:
    old = get_block(v, content)
    if not old: continue
    new = re.sub(r'~(.*?)~', rf'~\n{erinin_desc}\n~', old, flags=re.MULTILINE | re.DOTALL, count=1)
    content = content.replace(old, new)
with open(wld469, 'w', encoding='latin-1') as f: f.write(content)

# Fix 56783 road
with open(wld567, 'r', encoding='latin-1') as f: content = f.read()
old = get_block(56783, content)
if old:
    new = re.sub(r'~(.*?)~', rf'~\n{road_desc}\n~', old, flags=re.MULTILINE | re.DOTALL, count=1)
    content = content.replace(old, new)
with open(wld567, 'w', encoding='latin-1') as f: f.write(content)

# Fix 638 river rooms
with open(wld638, 'r', encoding='latin-1') as f: content = f.read()
for v in [63800, 63811]:
    old = get_block(v, content)
    if not old: continue
    new = re.sub(r'~(.*?)~', rf'~\n{erinin_desc}\n~', old, flags=re.MULTILINE | re.DOTALL, count=1)
    content = content.replace(old, new)
with open(wld638, 'w', encoding='latin-1') as f: f.write(content)

print("Batch 3 fixes complete (fixing accidental river clobbers)")
