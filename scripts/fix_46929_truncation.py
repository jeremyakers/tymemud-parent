import re
import os

wld_file = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/469.wld"

with open(wld_file, 'r', encoding='latin-1') as f:
    content = f.read()

# Fix 46929 truncation
# Find the room block for 46929
pattern = r'(#46929\n.*?D3\n)(#46930\n)'
new_block = r"""#46929
`@Rolling Grassland`7~
`7Open ground stretches out, broken only by wildflowers and stubborn scrub.
The wind moves steadily across the land, and far things look deceptively close.
To the south, the main road junction at Luagde is visible, with the busy
sounds of travelers and merchant wagons carrying on the breeze.`7
~
469 a 2 10 10
D0
~
~
0 0 46919
D1
~
~
0 0 46810
D2
~
~
0 0 46939
D3
~
~
0 0 46928
R
In the Wake of an Army~
     `2It is immediately evident that a large number of troops
have passed through this area, recently.  The terrain has been
beaten and disturbed by great quantities of tracks, and the
foliage has taken a great pounding...`7
~
G
 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
S
#46930
"""

if re.search(pattern, content, re.DOTALL):
    content = re.sub(pattern, new_block, content, flags=re.DOTALL)
    with open(wld_file, 'w', encoding='latin-1') as f:
        f.write(content)
    print("Fixed 46929 truncation")
else:
    print("Pattern not found - check if 46929 is already fixed or different")
    # Let's print the actual content around 46929 to be sure
    match = re.search(r'#46929\n.*?#46930', content, re.DOTALL)
    if match:
        print("Actual content found:")
        print(match.group(0))
