import re
import os

wld638 = "/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld/638.wld"

with open(wld638, 'r', encoding='latin-1') as f:
    content = f.read()

# Replace "Caemlyn Road" with "Aringill Road" ONLY when it's not "Caemlyn - Aringill Road"
content = content.replace("Somewhere off, the Caemlyn Road", "Somewhere off, the Aringill Road")
content = content.replace("stood watch over the Caemlyn road", "stood watch over the Aringill road")
content = content.replace("through which the Caemlyn road", "through which the Aringill road")
content = content.replace("The Caemlyn road can be seen", "The Aringill road can be seen")

# Description in 63861 mentions "winding its way to the capital city of Andor" - this is OK if talking about Caemlyn
# but 63861 is near Aringill.
# Let's check 63861 again.
# #63861
# `6The Caemlyn - Aringill Road runs `&West`7~
# The road between Caemlyn and Aringill continues to wind its way
# steadily east and west.  Directly to the east, Aringill can be seen, its
# western guard towers looming up in the
# distance.  To the north is the fertile farmland of eastern Andor
# and to the south, a sparse forest springs to life.

# This looks fine.

with open(wld638, 'w', encoding='latin-1') as f:
    f.write(content)
print("Fixed 638 hallucinations correctly")
