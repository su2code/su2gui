# monitor gittree menu

# note that in the main menu, we need to call add the following:
# 1) from ui.monitor import *
# 2) call monitor_card() in SinglePageWithDrawerLayout
# 3) define a node in the gittree (pipeline)
# 4) define any global state variables that might be needed

import sys
import os
from pathlib import Path

# Add parent directory to path to allow importing from sibling directories
parent_dir = str(Path(__file__).parent.parent.absolute())
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# definition of ui_card
from ui.uicard import ui_card, ui_subcard, server
from trame.widgets import vuetify
from core.su2_json import *

state, ctrl = server.state, server.controller

# monitoring points
#