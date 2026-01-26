import re
import os

wld569 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/569.wld"

erinin_desc = """`6The mighty River Erinin flows steadily here, its deep blue waters carrying
the commerce of the Westlands. The river is wide and powerful, with a current
that demands respect from even the most seasoned rivermen. Along the banks,
the land is lush and green, and the occasional merchant vessel can be seen
moving slowly along its course.`7"""

def get_block(vnum, content):
    pattern = rf'^#{vnum}\s*\n(.*?)(?=\n#|\Z)'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    return match.group(0) if match else None

with open(wld569, 'r', encoding='latin-1') as f: content = f.read()

for v in [56906, 56916, 56926]:
    old = get_block(v, content)
    # Standardize name
    new_name = "`6The River Erinin`7"
    if v == 56906: new_name = "`6The River Erinin runs `&East`6 and `&South`7"
    elif v == 56916: new_name = "`6The River Erinin runs `&North `6and `&South`7"
    elif v == 56926: new_name = "`6The River Erinin runs `&North `6and `&West`7"
    
    new = rf"""#{v}
{new_name}~
{erinin_desc}
~
569 a 6 10 10"""
    # Keep existing exits
    exits = re.findall(r'^D\d+\n.*?\n.*?\n-?\d+ -?\d+ \d+', old, re.MULTILINE)
    for e in exits:
        new += f"\n{e}"
    new += "\nR\nIn the Wake of an Army~\n     `2It is immediately evident that a large number of troops\nhave passed through this area, recently.  The terrain has been\nbeaten and disturbed by great quantities of tracks, and the\nfoliage has taken a great pounding...`7\n~\nG\n 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\nS"
    content = content.replace(old, new)

with open(wld569, 'w', encoding='latin-1') as f: f.write(content)
print("Standardized river rooms in 569.wld")
