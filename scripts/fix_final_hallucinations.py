import re
import os

wld_dir = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld"
zones = [468, 469, 508, 509, 638]

# High-quality river template
erinin_desc = """`6The mighty River Erinin flows steadily here, its deep blue waters carrying
the commerce of the Westlands. The river is wide and powerful, with a current
that demands respect from even the most seasoned rivermen. Along the banks,
the land is lush and green, and the occasional merchant vessel can be seen
moving slowly along its course.`7"""

def fix_surrounds_and_hallucinations(file_path):
    with open(file_path, 'r', encoding='latin-1') as f:
        content = f.read()
    
    # 1. Fix "Surrounds Tar Valon" in names
    content = content.replace("`^The Erinin Surrounds Tar Valon`0", "`6The River Erinin`7")
    content = content.replace("River Erinin Surrounds Tar Valon", "River Erinin")
    
    # 2. Fix specific hallucinations
    # Zone 468: White Tower south -> north
    if "468.wld" in file_path:
        content = content.replace("south the `7Wh`&i`7t`&e `7T`&owe`7r", "north the `7Wh`&i`7t`&e `7T`&owe`7r")
        content = content.replace("south the White Tower", "north the White Tower")

    # Zone 638: Caemlyn -> Aringill
    if "638.wld" in file_path:
        content = content.replace("Caemlyn", "Aringill")
        content = content.replace("capital of Andor", "port of Aringill")

    with open(file_path, 'w', encoding='latin-1') as f:
        f.write(content)
    print(f"Processed {file_path}")

for z in zones:
    fix_surrounds_and_hallucinations(os.path.join(wld_dir, f"{z}.wld"))
