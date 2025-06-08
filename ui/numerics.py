# numerics gittree menu

# ui_cards:
#                appear below the gittree.
# ui_sub_cards:
#                appear below ui_cards, change depending on settings in ui_cards.
# dialog_cards:
#                popup-window called from button in ui_cards.
# @state.change:
#                called from ui_cards, ui_sub_cards or dialog_cards, sets the configuration option.

# note that in the main menu, we need to call/add the following:
# 1) from ui.numerics import *
# 2) call numerics_card() in SinglePageWithDrawerLayout
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

############################################################################
# Numerics models - list options #
############################################################################

# List: numerics model: spatial gradients NUM_METHOD_GRAD
LNumericsGrad= [
  {"text": "Green-Gauss", "value": 0, "json": "GREEN_GAUSS"},
  {"text": "Weighted Least Squares", "value": 1, "json": "WEIGHTED_LEAST_SQUARES"},
]

# List: numerics model: gradient reconstruction for MUSCL (NUM_METHOD_GRAD_RECON)
LNumericsGradRecon= [
  {"text": "Green-Gauss", "value": 0, "json": "GREEN_GAUSS"},
  {"text": "Weighted Least Squares", "value": 1, "json": "WEIGHTED_LEAST_SQUARES"},
]

# set the state variables using the json data from the config file
def set_json_numerics():
    if 'CFL_NUMBER' in state.jsonData:
        try:
            state.CFL_idx = float(state.jsonData['CFL_NUMBER'])
        except Exception as e:
            log("error", f"Error in setting CFL number in Numeric Tab:  \n {e}")
    if 'NUM_METHOD_GRAD' in state.jsonData:
        state.numerics_grad_idx = GetJsonIndex(state.jsonData['NUM_METHOD_GRAD'],LNumericsGrad)
    if 'NUM_METHOD_GRAD_RECON' in state.jsonData:
        state.numerics_grad_recon_idx = GetJsonIndex(state.jsonData['NUM_METHOD_GRAD_RECON'],LNumericsGradRecon)
    state.dirty('CFL_idx')
    state.dirty('numerics_grad_idx')
    state.dirty('numerics_grad_recon_idx')

###############################################################
# PIPELINE CARD : Numerics
###############################################################
def numerics_card():
    with ui_card(title="Numerics", ui_name="Numerics"):
        log("info", "## Numerics Selection ##")

        # 1 row of option lists
        with vuetify.VRow(classes="pt-2"):
          with vuetify.VCol(cols="10"):

            # Then a list selection for numerics submodels
            vuetify.VSelect(
                # What to do when something is selected
                v_model=("numerics_grad_idx", 0),
                # The items in the list
                items=("representations_grad",LNumericsGrad),
                # the name of the list box
                label="Spatial Gradients",
                hide_details=True,
                dense=True,
                outlined=True,
                classes="pt-1 mt-1",
            )
            vuetify.VSelect(
                # What to do when something is selected
                v_model=("numerics_grad_recon_idx", 0),
                # The items in the list
                items=("representations_grad_recon",LNumericsGradRecon),
                # the name of the list box
                label="MUSCL Spatial Gradients",
                hide_details=True,
                dense=True,
                outlined=True,
                classes="pt-1 mt-1",
            )
            vuetify.VTextField(
                # What to do when something is selected
                v_model=("CFL_idx", 1.0),
                # the name of the list box
                label="CFL",
            )

###############################################################
# Numerics - state changes
###############################################################
@state.change("numerics_grad_idx")
def update_material(numerics_grad_idx, **kwargs):
    log("info", f"numerics spatial gradient selection:  = {numerics_grad_idx}")
    # we want to call a submenu
    #state.active_sub_ui = "submaterials_fluid"
    # update config option value
    state.jsonData['NUM_METHOD_GRAD']= GetJsonName(numerics_grad_idx,LNumericsGrad)

@state.change("numerics_grad_recon_idx")
def update_material(numerics_grad_recon_idx, **kwargs):
    log("info", f"numerics MUSCL spatial gradient selection:  = {numerics_grad_recon_idx}")
    # we want to call a submenu
    #state.active_sub_ui = "submaterials_fluid"
    # update config option value
    state.jsonData['NUM_METHOD_GRAD_RECON']= GetJsonName(numerics_grad_recon_idx,LNumericsGradRecon)

@state.change("CFL_idx")
def update_material(CFL_idx, **kwargs):
    log("info", f"CFL value:  = {CFL_idx}")
    # we want to call a submenu
    #state.active_sub_ui = "submaterials_fluid"
    # update config option value
    try:
        state.jsonData['CFL_NUMBER']= float(CFL_idx)
    except Exception as e:
        log("error", f"Error in setting CFL number in Numeric Tab:  \n {e}")
   
