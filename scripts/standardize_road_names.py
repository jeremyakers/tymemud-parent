import re
import os

wld640 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/640.wld"
wld610 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/610.wld"

def standardize_names(file_path, vnum_range, old_pattern, new_name):
    with open(file_path, 'r', encoding='latin-1') as f:
        content = f.read()
    
    rooms = re.split(r'^#(\d+)', content, flags=re.MULTILINE)[1:]
    new_content = re.split(r'^#(\d+)', content, flags=re.MULTILINE)[0]
    
    modified = 0
    for i in range(0, len(rooms), 2):
        vnum = int(rooms[i])
        block = rooms[i+1]
        
        if vnum in vnum_range:
            # Match the first line (name line)
            name_match = re.search(r"^(.*?)~", block, re.MULTILINE)
            if name_match:
                name_line = name_match.group(1)
                if old_pattern.search(name_line):
                    # Keep directions
                    dirs_match = re.search(r"runs (.*)$", name_line)
                    dirs = dirs_match.group(1) if dirs_match else ""
                    
                    new_name_line = f"`6{new_name}"
                    if dirs:
                        new_name_line += f" runs {dirs}"
                    
                    new_block = block.replace(name_line, new_name_line, 1)
                    block = new_block
                    modified += 1
        
        new_content += f"#{vnum}{block}"
        
    with open(file_path, 'w', encoding='latin-1') as f:
        f.write(new_content)
    print(f"Modified {modified} rooms in {file_path}")

# Road 1: Caemlyn - Tar Valon Road
road1_vnums_640 = [64022, 64012, 64002]
road1_vnums_610 = list(range(61000, 61100)) # Zone 610 is mostly road

# Road 2: Caemlyn - Far Madding Road
road2_vnums_640 = [64062, 64072, 64073, 64083, 64093]

# Road 3: Caemlyn - Aringill Road
road3_vnums_640 = [64044, 64045, 64046, 64056, 64057, 64067, 64068, 64069]

standardize_names(wld640, road1_vnums_640, re.compile(r"Road", re.I), "The Caemlyn - Tar Valon Road")
standardize_names(wld610, road1_vnums_610, re.compile(r"Road", re.I), "The Caemlyn - Tar Valon Road")
standardize_names(wld640, road2_vnums_640, re.compile(r"Road", re.I), "The Caemlyn - Far Madding Road")
standardize_names(wld640, road3_vnums_640, re.compile(r"Road", re.I), "The Caemlyn - Aringill Road")
