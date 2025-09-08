# boundaries gittree menu

# note that in the main menu, we need to call/add the following:
# 1) from ui.boundaries import *
# 2) call boundaries_card() in SinglePageWithDrawerLayout
# 3) define a node in the gittree (pipeline)
# 4) define any global state variables that might be needed

import sys
import os
import json
import traceback
from pathlib import Path

# Add parent directory to path to allow importing from sibling directories
parent_dir = str(Path(__file__).parent.parent.absolute())
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# definition of ui_card
from core.su2_py_wrapper import generate_dynamic_temperature_wrapper
from ui.uicard import ui_card, ui_subcard, ui_card_children_only, ui_card_parent_only, server
from trame.widgets import vuetify
from core.su2_json import *
from ui.materials import *
from core.logger import log
state, ctrl = server.state, server.controller

# for dialog cards:
#1. define a boolean to show//hide the dialog
#2. define dialog_card
#3. define an update for the boolean to show/hide the dialog
#4. initialize the dialog by calling it in the singlepagewithdrawerlayout
#5. couple to a button in the main ui dialog

# 1. define a boolean to show//hide the dialog
state.show_boundaries_dialog_card_inlet = False
state.show_boundaries_dialog_card_outlet = False
state.show_boundaries_dialog_card_wall = False
state.show_boundaries_dialog_card_farfield = False
state.show_boundaries_dialog_card_supersonic_inlet = False

# Initialize custom temperature state variables
state.enable_custom_temperature = True
state.custom_temperature_function = "560.0 - 260.0*sin(x*pi / 4)"  # Position-based formula that works
state.wrapper_type = "simple"  # Only "simple" position-based supported

# Initialize user variables (a, b, c, d, e, f, g, h) - COMMENTED OUT FOR POSITION-BASED
# state.var_a = 293.0  # Base temperature
# state.var_b = 57.0   # Amplitude
# state.var_c = 2.0    # Frequency multiplier
# state.var_d = 0.0    # Additional variable
# state.var_e = 0.0    # Additional variable
# state.var_f = 0.0    # Additional variable
# state.var_g = 0.0    # Additional variable
# state.var_h = 0.0    # Additional variable

# Initialize wrapper type options - COMMENTED OUT UNSTEADY CHT
state.LWrapperTypes = [
    # {"text": "Full Unsteady CHT (time-based)", "value": "unsteady_cht"},  # COMMENTED OUT
    {"text": "Simple Position-based", "value": "simple"}
]

# Initialize required state variables if not present
# if not hasattr(state, 'case_name') or not state.case_name:
#     state.case_name = "default_case"
if not hasattr(state, 'python_wrapper_filename'):
    state.python_wrapper_filename = "run_su2_dynamic.py"
if not hasattr(state, 'filename_json_export'):
    state.filename_json_export = "config.json"
if not hasattr(state, 'filename_cfg_export'):
    state.filename_cfg_export = "config.cfg"

state.boundaries_main_idx = 0

# note that boundary information is stored in the state.BCDictList
# {"bcName":bcName.get("text"), "bcType":"Wall", "bc_subtype":"Heatflux", "json":"MARKER_HEATFLUX", "bcValue":0.0}
# note that the currently selected boundary is in state.SelectedBoundaryName, selectedBoundaryIndex
############################################################################
# Boundaries models - list options #
############################################################################

# List: boundaries model: Main boundary selection
# note that we have to set this for each of the boundaries
state.LBoundariesMain= [
  {"text": "Inlet", "value": 0},
  {"text": "Outlet", "value": 1},
  {"text": "Wall", "value": 2},
  {"text": "Far-field", "value": 3},
  {"text": "Symmetry", "value": 4},
  {"text": "Supersonic Inlet", "value": 5},
  {"text": "Supersonic Outlet", "value": 6},
]

state.LBoundariesInlet= [
  {"text": "Velocity inlet", "value": 0},
  {"text": "Pressure inlet", "value": 1},
]


state.LBoundariesOutlet= [
  {"text": "Pressure outlet", "value": 0},
  {"text": "Target mass flow rate", "value": 1},
]

LBoundariesWall= [
  {"text": "Temperature", "value": 0},
  {"text": "Heat flux", "value": 1},
  {"text": "Heat transfer", "value": 2}, 
  {"text": "Euler", "value": 3}, 
]

# determine which boundary dialog card to show based on the boundary selection
def update_boundaries_dialog_card(idx):
  log("info", f"idx =  = {idx}")
  if(idx==0):
    update_boundaries_dialog_card_inlet()
  elif(idx==1):
    update_boundaries_dialog_card_outlet()
  elif(idx==2):
    update_boundaries_dialog_card_wall()
  elif(idx==3):
    update_boundaries_dialog_card_farfield()
  elif (idx==5):
    update_boundaries_dialog_card_supersonic_inlet()


#2. define dialog_card
######################################################################
# popup window for boundaries model - inlet
def boundaries_dialog_card_inlet():
    with vuetify.VDialog(width=300,position='{X:10,Y:10}',transition="dialog-top-transition",v_model=("show_boundaries_dialog_card_inlet",False)):
      with vuetify.VCard():

        vuetify.VCardTitle("Inlet",
                           classes="grey lighten-1 py-1 grey--text text--darken-3")

        #with vuetify.VContainer(fluid=True, v_if=("jsonData['FLUID_MODEL']=='CONSTANT_DENSITY' ")):
        with vuetify.VContainer(fluid=True):

          # ####################################################### #
          with vuetify.VRow(classes="py-0 my-0"):
            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              # Then a list selection for turbulence submodels
              vuetify.VSelect(
                # What to do when something is selected
                v_model=("boundaries_inc_inlet_idx", 0),
                # The items in the list
                items=("LBoundariesInlet",state.LBoundariesInlet),
                # the name of the list box
                label="Inlet type",
                hide_details=True,
                dense=True,
                outlined=True,
                classes="py-0 my-0",
            )

        with vuetify.VContainer(fluid=True,v_if=("(boundaries_inc_inlet_idx == 3) | (boundaries_inc_inlet_idx == 0)"),):
          # ####################################################### #
          with vuetify.VRow(classes="py-0 my-0"):
            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                # What to do when something is selected
                v_model=("boundaries_inc_velocity_magnitude_idx", 1.0),
                # the name of the list box
                label="Velocity magnitude [m/s]",
              )

        with vuetify.VContainer(fluid=True,v_if=("(boundaries_inc_inlet_idx == 1) | (boundaries_inc_inlet_idx == 2)"),):
          # ####################################################### #
          with vuetify.VRow(classes="py-0 my-0"):
            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                # What to do when something is selected
                v_model=("boundaries_inc_pressure_idx", 1.0),
                # the name of the list box
                label="Pressure [Pa]",
              )

        with vuetify.VContainer(fluid=True,v_if=("boundaries_inc_inlet_idx!=3"),):
          # ####################################################### #
          with vuetify.VRow(classes="py-0 my-0"):
            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                # What to do when something is selected
                v_model=("boundaries_inc_temperature_idx", 300.0),
                # no temperature for incompressible when energy equation is off
                disabled=("jsonData['INC_ENERGY_EQUATION']==0",0),
                # the name of the list box
                label="Temperature [K]",
              )

        with vuetify.VContainer(fluid=True,v_if=("boundaries_inc_inlet_idx==3"),):
          # ####################################################### #
          with vuetify.VRow(classes="py-0 my-0"):
            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                # What to do when something is selected
                v_model=("boundaries_inc_density_idx", 300.0),
                # the name of the list box
                label="Density [kg/m3]",
              )

        with vuetify.VContainer(fluid=True):  
          with vuetify.VRow(classes="py-0 my-0"):
            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              # checkbox for energy (can only be deselected for incompressible)
              vuetify.VCheckbox(
                  v_model=("boundary_inc_vel_usenormals_idx", False),
                  label="velocity normal to inlet (global)",
                  # activate or deactivate/disable the checkbox
                  # only active for incompressible flow
                  # else, default is on
                  classes="mt-1 pt-1",
                  hide_details=True,
                  dense=True,
              )
          # ####################################################### #
          with vuetify.VRow(classes="py-0 my-0"):
            with vuetify.VCol(cols="3", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                # What to do when something is selected
                v_model=("boundaries_nx_idx", 1.0),
                disabled=("boundary_inc_vel_usenormals_idx",0),
                # the name of the list box
                label="n_x",
              )
            with vuetify.VCol(cols="3", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                # What to do when something is selected
                v_model=("boundaries_ny_idx", 0.0),
                disabled=("boundary_inc_vel_usenormals_idx",0),
                # the name of the list box
                label="n_y",
              )
            with vuetify.VCol(cols="3", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                # What to do when something is selected
                v_model=("boundaries_nz_idx", 0.0),
                disabled=("boundary_inc_vel_usenormals_idx",0),
                # the name of the list box
                label="n_z",
              )



          # ####################################################### #
          #with vuetify.VRow(classes="py-0 my-0"):
          #  with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
          #    vuetify.VTextField(
          #      # What to do when something is selected
          #      v_model=("boundaries_inc_inlet_damping_idx", 0.1),
          #      # the name of the list box
          #      label="inlet damping factor",
          #    )
        with vuetify.VCardText():
          vuetify.VBtn("close", click=update_boundaries_dialog_card_inlet)

        # Per-marker inlet types editor (arrays)
        with vuetify.VContainer(fluid=True):
          vuetify.VDivider()
          vuetify.VSubheader("Per-marker inlet types")
          # Incompressible per-marker inlet types
          with vuetify.VContainer(fluid=True, v_if=("jsonData['SOLVER'] && jsonData['SOLVER'].includes('INC')",)):
            with vuetify.VList(dense=True):
              with vuetify.VListItem(v_for="(bc,i) in BCDictList.filter(b => b.bcType === 'Inlet')", key="i"):
                with vuetify.VListItemContent():
                  vuetify.VListItemTitle("`$${bc.bcName}`")
                  vuetify.VListItemSubtitle("`$${bc.bc_subtype}`")
                with vuetify.VListItemAction():
                  vuetify.VBtn("Velocity", small=True, outlined=True, click=(ctrl.set_inlet_bc_subtype, "[bc.bcName, 'Velocity inlet']"))
                  vuetify.VBtn("Pressure", small=True, outlined=True, classes="ml-2", click=(ctrl.set_inlet_bc_subtype, "[bc.bcName, 'Pressure inlet']"))
          # Compressible per-marker inlet types
          with vuetify.VContainer(fluid=True, v_if=("jsonData['SOLVER'] && !jsonData['SOLVER'].includes('INC')",)):
            with vuetify.VList(dense=True):
              with vuetify.VListItem(v_for="(bc,i) in BCDictList.filter(b => b.bcType === 'Inlet')", key="i"):
                with vuetify.VListItemContent():
                  vuetify.VListItemTitle("`$${bc.bcName}`")
                  vuetify.VListItemSubtitle("`$${bc.bc_subtype}`")
                with vuetify.VListItemAction():
                  vuetify.VBtn("Total Conditions", small=True, outlined=True, click=(ctrl.set_inlet_bc_subtype, "[bc.bcName, 'Total Conditions']"))
                  vuetify.VBtn("Mass Flow", small=True, outlined=True, classes="ml-2", click=(ctrl.set_inlet_bc_subtype, "[bc.bcName, 'Mass Flow']"))

#3. define an update for the boolean to show/hide the dialog
# switch the visibility of the popup window on/off
def update_boundaries_dialog_card_inlet():
    state.show_boundaries_dialog_card_inlet = not state.show_boundaries_dialog_card_inlet

#2. define dialog_card
######################################################################
# popup window for boundaries model - outlet
def boundaries_dialog_card_outlet():
    with vuetify.VDialog(width=300,position='{X:10,Y:10}',transition="dialog-top-transition",v_model=("show_boundaries_dialog_card_outlet",False)):
      with vuetify.VCard():

        vuetify.VCardTitle("Outlet",
                           classes="grey lighten-1 py-1 grey--text text--darken-3")

        #with vuetify.VContainer(fluid=True, v_if=("jsonData['FLUID_MODEL']=='CONSTANT_DENSITY' ")):
        with vuetify.VContainer(fluid=True):
          # ####################################################### #
          with vuetify.VRow(classes="py-0 my-0"):
            with vuetify.VCol(cols="10", classes="py-1 my-1 pr-0 mr-0"):
              # Then a list selection for turbulence submodels
              vuetify.VSelect(
                # What to do when something is selected
                v_model=("boundaries_inc_outlet_idx", 0),
                # The items in the list
                items=("LBoundariesOutlet", state.LBoundariesOutlet),
                # the name of the list box
                label="Outlet type",
                hide_details=True,
                dense=True,
                outlined=True,
                classes="py-0 my-0",
            )

        # pressure outlet
        with vuetify.VContainer(fluid=True,v_if=("boundaries_inc_outlet_idx==0"),):
          # ####################################################### #
          with vuetify.VRow(classes="py-0 my-0"):
            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                # What to do when something is selected
                v_model=("boundaries_inc_outlet_P_idx", 300.0),
                # the name of the list box
                label="Pressure [Pa]",
              )
        # target massflow
        with vuetify.VContainer(fluid=True,v_if=("boundaries_inc_outlet_idx==1"),):
          # ####################################################### #
          with vuetify.VRow(classes="py-0 my-0"):
            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                # What to do when something is selected
                v_model=("boundaries_inc_outlet_m_idx", 0.0),
                # the name of the list box
                label="Target mass-flow [kg/s]",
              )
        with vuetify.VCardText():
          vuetify.VBtn("close", click=update_boundaries_dialog_card_outlet)

        # Per-marker outlet types editor (arrays)
        with vuetify.VContainer(fluid=True):
          vuetify.VDivider()
          vuetify.VSubheader("Per-marker outlet types")
          with vuetify.VList(dense=True):
            with vuetify.VListItem(v_for="(bc,i) in BCDictList.filter(b => b.bcType === 'Outlet')", key="i"):
              with vuetify.VListItemContent():
                vuetify.VListItemTitle("`$${bc.bcName}`")
                vuetify.VListItemSubtitle("`$${bc.bc_subtype}`")
              with vuetify.VListItemAction():
                vuetify.VBtn("Pressure", small=True, outlined=True, click=(ctrl.set_outlet_bc_subtype, "[bc.bcName, 'Pressure outlet']"))
                vuetify.VBtn("Mass Flow", small=True, outlined=True, classes="ml-2", click=(ctrl.set_outlet_bc_subtype, "[bc.bcName, 'Target mass flow rate']"))

#3. define an update for the boolean to show/hide the dialog
# switch the visibility of the popup window on/off
def update_boundaries_dialog_card_outlet():
    state.show_boundaries_dialog_card_outlet = not state.show_boundaries_dialog_card_outlet


#2. define dialog_card
######################################################################
# popup window for boundaries model - wall
def boundaries_dialog_card_wall():
    with vuetify.VDialog(width=500,position='{X:10,Y:10}',transition="dialog-top-transition",v_model=("show_boundaries_dialog_card_wall",False)):
      with vuetify.VCard(width=500, style_="min-width: 500px"):
        vuetify.VCardTitle("Wall",
                          classes="grey lighten-1 py-1 grey--text text--darken-3",
                          style_="width: 100%")

        with vuetify.VContainer(fluid=True, style_="width: 100%; max-width: 500px"):
          # ####################################################### #
          with vuetify.VRow(classes="py-0 my-0", style_="width: 100%"):
            with vuetify.VCol(cols="12", classes="py-1 my-1"):
              # Then a list selection for wall submodels
              vuetify.VSelect(
                # What to do when something is selected
                v_model=("boundaries_wall_idx", 0),
                # The items in the list
                items=("representations_wall",LBoundariesWall),
                # the name of the list box
                label="Wall type",
                hide_details=True,
                dense=True,
                outlined=True,
                classes="py-0 my-0",
            )
        
        # temperature
        with vuetify.VContainer(fluid=True, v_if=("boundaries_wall_idx==0"), style_="width: 100%; max-width: 500px"):
          # ####################################################### #
          with vuetify.VRow(classes="py-0 my-0", style_="width: 100%"):
            with vuetify.VCol(cols="12", classes="py-1 my-1"):
              vuetify.VTextField(
                # What to do when something is selected
                v_model=("boundaries_inc_temperature_idx", 300.0),
                # the name of the list box
                label="Base Temperature [K]",                #    label= ("selectedBoundaryIndex","none"),
              )
            
          # Custom Temperature Section
          with vuetify.VRow(classes="py-1 my-1", style_="width: 100%"):
            with vuetify.VCol(cols="12", classes="py-1 my-1"):
              vuetify.VCheckbox(
                v_model=("enable_custom_temperature", True),
                label="Enable Custom Temperature Function",
                dense=True,
                classes="py-0 my-0"
              )
            # Wrapper Type Selection COMMENTED OUT - only position-based supported
          # with vuetify.VContainer(fluid=True, v_if=("enable_custom_temperature",), style_="width: 100%; max-width: 500px"):
          #   with vuetify.VRow(classes="py-0 my-0", style_="width: 100%"):
          #     with vuetify.VCol(cols="12", classes="py-1 my-1"):
          #       vuetify.VSelect(
          #         v_model=("wrapper_type", "simple"),
          #         items=("LWrapperTypes", []),
          #         label="Python Wrapper Type",
          #         hint="Select the type of SU2 Python wrapper to generate",
          #         persistent_hint=True,
          #         dense=True,
          #         outlined=True,
          #         classes="py-0 my-0"
          #       )
            # Custom temperature function input (only shown when checkbox is enabled)
          with vuetify.VContainer(fluid=True, v_if=("enable_custom_temperature",), style_="width: 100%; max-width: 500px"):
            with vuetify.VRow(classes="py-0 my-0", style_="width: 100%"):
              with vuetify.VCol(cols="12", classes="py-1 my-1"):
                vuetify.VTextField(
                  v_model=("custom_temperature_function", "560.0 - 260.0*sin(x*pi / 4)"),
                  label="Temperature Function",
                  hint="Position-based formula using x,y,z coordinates. Examples: 560.0 - 260.0*sin(x*pi/4), 300 + 50*(x*y), 400 + 100*sin(x)*cos(y), 350 + 25*sqrt(x**2 + y**2)",
                  persistent_hint=True,
                  classes="py-0 my-0"
                )
                
            # User-defined variables section - COMMENTED OUT FOR POSITION-BASED ONLY
            # with vuetify.VRow(classes="py-1 my-1", style_="width: 100%"):
            #   with vuetify.VCol(cols="12", classes="py-0 my-0"):
            #     vuetify.VSubheader("User Variables (a, b, c, d...)")
            # 
            # with vuetify.VRow(classes="py-0 my-0", style_="width: 100%"):
            #   with vuetify.VCol(cols="3", classes="py-1 my-1"):
            #     vuetify.VTextField(v_model=("var_a", 293.0), label="a", type="number", dense=True)
            #   with vuetify.VCol(cols="3", classes="py-1 my-1"):
            #     vuetify.VTextField(v_model=("var_b", 57.0), label="b", type="number", dense=True)
            #   with vuetify.VCol(cols="3", classes="py-1 my-1"):
            #     vuetify.VTextField(v_model=("var_c", 2.0), label="c", type="number", dense=True)
            #   with vuetify.VCol(cols="3", classes="py-1 my-1"):
            #     vuetify.VTextField(v_model=("var_d", 0.0), label="d", type="number", dense=True)
            # 
            # with vuetify.VRow(classes="py-0 my-0", style_="width: 100%"):
            #   with vuetify.VCol(cols="3", classes="py-1 my-1"):
            #     vuetify.VTextField(v_model=("var_e", 0.0), label="e", type="number", dense=True)
            #   with vuetify.VCol(cols="3", classes="py-1 my-1"):
            #     vuetify.VTextField(v_model=("var_f", 0.0), label="f", type="number", dense=True)
            #   with vuetify.VCol(cols="3", classes="py-1 my-1"):
            #     vuetify.VTextField(v_model=("var_g", 0.0), label="g", type="number", dense=True)
            #   with vuetify.VCol(cols="3", classes="py-1 my-1"):
            #     vuetify.VTextField(v_model=("var_h", 0.0), label="h", type="number", dense=True)
            # DYNAMIC TEMPERATURE WRAPPER FILENAME SECTION
          with vuetify.VRow(classes="mt-4", v_if=("enable_custom_temperature",), style_="width: 100%"):
            with vuetify.VCol(cols="12"):
              vuetify.VTextField(
                v_model=("python_wrapper_filename", "run_su2_dynamic.py"),
                label="Dynamic Temperature Wrapper Filename",
                hint="e.g., run_su2_dynamic.py, run_su2_airfoil.py",
                outlined=True,                dense=True,
              )
            # Test button to verify clicks work (keeping original functionality)
          with vuetify.VRow(classes="py-1 my-1", style_="width: 100%"):
            with vuetify.VCol(cols="12", classes="py-1 my-1"):
              vuetify.VBtn(
                "Generate Dynamic Temp Wrapper",
                click=ctrl.test_button_click,
                color="primary",
                outlined=True,
                small=True,
                block=True
              )        # heat flux
        with vuetify.VContainer(fluid=True, v_if=("boundaries_wall_idx==1"), style_="width: 100%; max-width: 500px"):
          # ####################################################### #
          with vuetify.VRow(classes="py-0 my-0", style_="width: 100%"):
            with vuetify.VCol(cols="12", classes="py-1 my-1"):
              vuetify.VTextField(
                # What to do when something is selected
                v_model=("boundaries_inc_heatflux_idx", 0.0),
                # the name of the list box
                label="Heat flux [J/m^2]",
                #    label= ("selectedBoundaryIndex","none"),
              )        # heat transfer
        with vuetify.VContainer(fluid=True, v_if=("boundaries_wall_idx==2"), style_="width: 100%; max-width: 500px"):
          # ####################################################### #
          with vuetify.VRow(classes="py-0 my-0", style_="width: 100%"):
            with vuetify.VCol(cols="12", classes="py-1 my-1"):
              vuetify.VTextField(                # What to do when something is selected
                v_model=("boundaries_inc_heattransfer_h_idx", 1000.0),
                # the name of the list box
                label="Heat Transfer Coefficient [J/K.m^2]",
                #    label= ("selectedBoundaryIndex","none"),
              )
          
          # Far-field temperature row for heat transfer
          with vuetify.VRow(classes="py-0 my-0", style_="width: 100%"):
            with vuetify.VCol(cols="12", classes="py-1 my-1", v_if=("boundaries_wall_idx!=3")):
              vuetify.VTextField(
                # What to do when something is selected
                v_model=("boundaries_inc_heattransfer_T_idx", 300.0),
                # the name of the list box
                label="Far-field temperature [K]",
                #    label= ("selectedBoundaryIndex","none"),
              )
        
        with vuetify.VCardText():
          vuetify.VBtn("close", click=update_boundaries_dialog_card_wall, style_="width: 100%")

#3. define an update for the boolean to show/hide the dialog
# switch the visibility of the popup window on/off
def update_boundaries_dialog_card_wall():
    state.show_boundaries_dialog_card_wall = not state.show_boundaries_dialog_card_wall

# Controller function for the button
def generate_python_wrapper_with_dynamic_temp():
    """Generate Python wrapper with dynamic wall temperature for the selected boundary."""
    print("here")
    log("info", "=== BUTTON CLICKED: Dynamic Temperature Wrapper Generation Started ===")
    try:        
        print("Generating dynamic temperature wrapper...")
        # Check if case_name exists, if not create a default one
        if not hasattr(state, 'case_name') or not state.case_name:
            state.case_name = "default_case"
            log("info", f"No case name found, using default: {state.case_name}")
            
        if not hasattr(state, 'selectedBoundaryName') or not state.selectedBoundaryName:
            log("warning", "No boundary selected. Using default boundary name 'airfoil'")
            state.selectedBoundaryName = "airfoil"

        print(f"Selected boundary: {state.selectedBoundaryName}")
        # Get current temperature value and custom settings
        base_temp = getattr(state, 'boundaries_inc_temperature_idx', 300.0)
        boundary_name = state.selectedBoundaryName
        custom_function = getattr(state, 'custom_temperature_function', "560.0 - 260.0*sin(x*pi / 4)")
        
        log("info", f"Generating dynamic temperature wrapper for boundary '{boundary_name}'")
        log("info", f"Base temperature: {base_temp}K")
        log("info", f"Custom function: {custom_function}")
        
        # Get user variables from the boundary card - COMMENTED OUT FOR POSITION-BASED ONLY
        # variables = {
        #     'a': getattr(state, 'var_a', 293.0),
        #     'b': getattr(state, 'var_b', 57.0),
        #     'c': getattr(state, 'var_c', 2.0),
        #     'd': getattr(state, 'var_d', 0.0),
        #     'e': getattr(state, 'var_e', 0.0),
        #     'f': getattr(state, 'var_f', 0.0),
        #     'g': getattr(state, 'var_g', 0.0),
        #     'h': getattr(state, 'var_h', 0.0),
        # }
        variables = {}  # No user variables for position-based
        
        log("info", f"Using variables: {variables}")
        
        if not hasattr(state, 'jsonData'):
            state.jsonData = {}
            
        state.jsonData['MARKER_ISOTHERMAL'] = [(boundary_name, base_temp)]
        
        # Set Python custom marker for dynamic control
        if 'MARKER_PYTHON_CUSTOM' not in state.jsonData:
            state.jsonData['MARKER_PYTHON_CUSTOM'] = []
        if boundary_name not in state.jsonData['MARKER_PYTHON_CUSTOM']:
            state.jsonData['MARKER_PYTHON_CUSTOM'].append(boundary_name)
        
        # Import the wrapper generation function        from core.su2_py_wrapper import generate_dynamic_temperature_wrapper
        # Generate the wrapper with dynamic temperature and variables
        wrapper_path = generate_dynamic_temperature_wrapper(
            boundary_marker=boundary_name,
            base_temperature=base_temp,
            filename_py_export=getattr(state, 'python_wrapper_filename', 'run_su2_dynamic.py'),
            variables=variables,
            temperature_formula=custom_function,
            wrapper_type=getattr(state, 'wrapper_type', 'simple')  # Force simple position-based
        )
        
        # Also save the updated configuration files - import function that exists
        try:
            from core.su2_io import save_json_cfg_file
            save_json_cfg_file(                filename_json_export=getattr(state, 'filename_json_export', 'config.json'),
                filename_cfg_export=getattr(state, 'filename_cfg_export', 'config.cfg')
            )
        except ImportError:
            # If su2_io doesn't exist, save JSON manually
            log("warning", "Could not import save_json_cfg_file, saving JSON manually")
        
        try:
            import json
            from pathlib import Path
            export_dir = Path(__file__).parent.parent / "user" / state.case_name
            export_dir.mkdir(parents=True, exist_ok=True)
            json_path = export_dir / "config.json"
            with json_path.open("w", encoding="utf-8") as fp:
                json.dump(state.jsonData, fp, indent=4, sort_keys=True, ensure_ascii=False)
            log("info", f"Wrote JSON to {json_path}")
        except Exception as e:
            log("warning", f"Could not save configuration files: {str(e)}")
            log("warning", f"Continuing with wrapper generation...")
        
        log("info", f"Dynamic temperature wrapper generated successfully for {boundary_name}")
        log("info", f"Wrapper file: {wrapper_path}")
        log("info", f"Configuration updated with MARKER_ISOTHERMAL and MARKER_PYTHON_CUSTOM")
        
        # Update state to show the generated wrapper path
        if hasattr(state, 'last_generated_wrapper_path'):
            state.last_generated_wrapper_path = str(wrapper_path)
            state.show_wrapper_path_info = True
        
    except Exception as e:
        log("error", f"Failed to generate dynamic temperature wrapper: {str(e)}")
        import traceback
        log("error", f"Traceback: {traceback.format_exc()}")

# Register the function with the controller
ctrl.generate_python_wrapper_with_dynamic_temp = generate_python_wrapper_with_dynamic_temp

#2. define dialog_card
######################################################################
# popup window for boundaries model - farfield
def boundaries_dialog_card_farfield():
    with vuetify.VDialog(width=500, position='{X:10,Y:10}', transition="dialog-top-transition", v_model=("show_boundaries_dialog_card_farfield", False)):
      with vuetify.VCard(width=500, style_="min-width: 500px"):
        
        vuetify.VCardTitle("Far-field",
                           classes="grey lighten-1 py-1 grey--text text--darken-3",
                           style_="width: 100%")
                           
        with vuetify.VContainer(fluid=True, style_="width: 100%; max-width: 500px"):
          with vuetify.VRow(classes="py-0 my-0", style_="width: 100%"):
            with vuetify.VCol(cols="4", classes="py-1 my-1"):
              vuetify.VTextField(
                # What to do when something is selected
                v_model=("boundaries_farfield_Vx_idx", 1.0),
                # the name of the list box
                label="Far-field X-Velocity [m/s]",
              )
            with vuetify.VCol(cols="4", classes="py-1 my-1"):
              vuetify.VTextField(
                # What to do when something is selected
                v_model=("boundaries_farfield_Vy_idx", 0.0),
                # the name of the list box
                label="Far-field Y-Velocity [m/s]",
              )
            with vuetify.VCol(cols="4", classes="py-1 my-1"):
              vuetify.VTextField(
                # What to do when something is selected                v_model=("boundaries_farfield_Vz_idx", 0.0),
                # the name of the list box
                label="Far-field Z-Velocity [m/s]",
              )
              
          with vuetify.VRow(classes="py-0 my-0", style_="width: 100%"):
            with vuetify.VCol(cols="12", classes="py-1 my-1"):
              vuetify.VTextField(
                # What to do when something is selected
                v_model=("boundaries_farfield_P_idx", 101325.0),
                # the name of the list box
                label="Far-field pressure [Pa]",
              )

          with vuetify.VRow(classes="py-0 my-0", style_="width: 100%"):
            with vuetify.VCol(cols="12", classes="py-1 my-1"):
              vuetify.VTextField(
                # What to do when something is selected
                v_model=("boundaries_farfield_T_idx", 300.0),                # the name of the list box
                label="Far-field temperature [K]",
              )

          with vuetify.VRow(classes="py-0 my-0", style_="width: 100%"):
            with vuetify.VCol(cols="12", classes="py-1 my-1"):
              vuetify.VTextField(
                # What to do when something is selected
                v_model=("boundaries_farfield_rho_idx", 1.2),
                # the name of the list box                label="Far-field density [kg/m^3]",
              )
              
        with vuetify.VCardText():
          vuetify.VBtn("close", click=update_boundaries_dialog_card_farfield, style_="width: 100%")

#3. define an update for the boolean to show/hide the dialog
# switch the visibility of the popup window on/off
def update_boundaries_dialog_card_farfield():
    state.show_boundaries_dialog_card_farfield = not state.show_boundaries_dialog_card_farfield


#2. define dialog_card
######################################################################
# popup window for boundaries model - inlet
def boundaries_dialog_card_supersonic_inlet():
    with vuetify.VDialog(width=300,position='{X:10,Y:10}',transition="dialog-top-transition",v_model=("show_boundaries_dialog_card_supersonic_inlet",False)):
      with vuetify.VCard():

        vuetify.VCardTitle("Supersonic Inlet",
                           classes="grey lighten-1 py-1 grey--text text--darken-3")

        with vuetify.VContainer(fluid=True):
          # ####################################################### #
          with vuetify.VRow(classes="py-0 my-0"):
            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                # What to do when something is selected
                v_model=("boundaries_inc_spr_pressure_idx", 1.0),
                # the name of the list box
                label="Pressure [Pa]",
              )

        with vuetify.VContainer(fluid=True):
          # ####################################################### #
          with vuetify.VRow(classes="py-0 my-0"):
            with vuetify.VCol(cols="12", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                # What to do when something is selected
                v_model=("boundaries_inc_spr_temperature_idx", 300.0),
                # the name of the list box
                label="Temperature [K]",
              )


          # ####################################################### #
          with vuetify.VRow(classes="py-0 my-0"):
            with vuetify.VCol(cols="3", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                # What to do when something is selected
                v_model=("boundaries_spr_nx_idx", 1.0),
                # the name of the list box
                label="n_x",
              )
            with vuetify.VCol(cols="3", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                # What to do when something is selected
                v_model=("boundaries_spr_ny_idx", 0.0),
                # the name of the list box
                label="n_y",
              )
            with vuetify.VCol(cols="3", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                # What to do when something is selected
                v_model=("boundaries_spr_nz_idx", 0.0),
                # the name of the list box
                label="n_z",
              )

        with vuetify.VCardText():
          vuetify.VBtn("close", click=update_boundaries_dialog_card_supersonic_inlet)

#3. define an update for the boolean to show/hide the dialog
# switch the visibility of the popup window on/off
def update_boundaries_dialog_card_supersonic_inlet():
    state.show_boundaries_dialog_card_supersonic_inlet = not state.show_boundaries_dialog_card_supersonic_inlet


# search in a list of dictionaries and return the entry based on the value of the key
def get_entry_from_name(val,key,List):
  #log("info", List[0][key])
  log("info", f"val= = {val}")
  log("info", f"key= = {key}")

  #NOTE: if the entry is not in the list, we return the first item.
  # This happens when we want to retrieve the subtype, of bctype, but bctype has changed
  # in the mean time. Since we have only one subtype that is shared with all types, there is
  # a mismatch.
  entry=List[0]

  # loop over all dict items in the list
  for item in List:
      log("debug", f"item= = {item}")
      if item[key]==val:
        log("debug", f"value found for item: = {item}")
        entry=item
        break
  return entry

# now get the index in state.LBoundariesMain using the name
def get_boundaries_main_idx_from_name(bcname):
    # get the entry in the list
    entry = get_entry_from_name(bcname,'bcName',state.BCDictList)
    idx = 0

    if not (entry==None):
      bctype = entry['bcType']
      entry = get_entry_from_name(bctype,'text',state.LBoundariesMain)
      idx = entry['value']
    return(idx)

###############################################################
# PIPELINE CARD : Boundaries
###############################################################
def boundaries_card_parent():
    # note that we want to show the card only for the children of the head/parent node
    with ui_card_parent_only(title="Boundaries", parent_ui_name="Boundaries"):
        log("info", "     ## Boundaries Selection ##")

        #vuetify.VTextField(
        #    #v_model=("idx", 0),
        #    label= "boundaries field",
        #    outlined=True,
        #)


def boundaries_card_children():
    # note that we want to show the card only for the children of the head/parent node
    with ui_card_children_only(title="Boundaries", parent_ui_name="Boundaries"):
        log("info", "     ## Boundaries Selection ##")

        # we show the boundary options only if the boundary is not internal
        with vuetify.VContainer(fluid=True, v_if=("selectedBoundaryName!='internal' ")):

          vuetify.VTextField(
            #v_model=("idx", 0),
            label= ("selectedBoundaryName","none"),
            outlined=True,
          )

          #vuetify.VTextField(
          #    #v_model=("idx", 0),
          #    label= ("selectedBoundaryIndex","none"),
          #    outlined=True,
          #)

          # note that for each boundary we have to keep track of the status of:
          # 1. state.LBoundariesMain
          #    This is in state.BCDictList
          #    'name' : name of the boundary
          #    'bcType' : type of the boundary, options are in state.LBoundariesMain
          # so we need BCDictList entry with 'name'
          # and we need to get the corresponding index in state.LBoundariesMain into boundaries_main_idx
          with vuetify.VRow(classes="pt-2"):
            with vuetify.VCol(cols="6"):
                # first a list selection for the main boundary types
                vuetify.VSelect(
                    # What to do when something is selected
                    v_model=("boundaries_main_idx", 0),
                    # The items in the list
                    items=("LBoundariesMain", state.LBoundariesMain),
                    # the name of the list box
                    label="Boundary type:",
                    hide_details=True,
                    dense=True,
                    outlined=True,
                    classes="mt-0 pt-0",
                )
            # Button to call/show the dialog card. Which dialog card to show depends on the chosen boundary condition
            with vuetify.VCol(cols="4", classes=""):
              with vuetify.VBtn(classes="mx-0 py-0 mt-0 mb-0",elevation=1,variant="text",color="white", click=(update_boundaries_dialog_card,"[boundaries_main_idx]"), icon="mdi-dots-vertical"):
                vuetify.VIcon("mdi-dots-vertical",density="compact",color="green")



###############################################################
# UI value update: boundaries model selection #
###############################################################
# we get here either if we change gittree selection or if we select a different option in the VSelect
# here, we have to update the values for the dialog windows from the stored BCDict values to show the correct
# values for each boundary
@state.change("boundaries_main_idx")
def update_boundaries_main(boundaries_main_idx, **kwargs):
    log("info", f"update boundaries main, idx= = {boundaries_main_idx}")
    entry = get_entry_from_name(boundaries_main_idx,'value',state.LBoundariesMain)
    bctype = entry['text']

    # update the BCDictList with the new boundary type
    for index in range(len(state.BCDictList)):
      if state.BCDictList[index]['bcName']==state.selectedBoundaryName:
        state.BCDictList[index]['bcType'] = bctype
        break


    log("debug", f"boundaries_main_idx::selected index= = {index}")
    state.selectedBoundaryIndex = index

    # from the main ui, we can call a dialog window.
    # 1. We have to get the dialog window corresponding to the chosen boundary condition.
    # 2. We have to set the values in the dialog window to the ones that were chosen/stored before.
    log("debug", f"boundaries_main_idx::bc type =  = {bctype}")
    if bctype == "Wall":
      # set the wall subtype for the dialog window from the saved state
      bc_subtype = state.BCDictList[index]['bc_subtype']
      # now find the subtype in the list LBoundariesWall and retrieve the index in the list
      entry = get_entry_from_name(bc_subtype,'text',LBoundariesWall)
      # set the state - this also calls the state function
      state.boundaries_wall_idx = entry['value']
      # force update of state, so we call the state.change
      state.dirty('boundaries_wall_idx')

    elif bctype == "Outlet":
      # massflow or pressure
      bc_subtype = state.BCDictList[index]['bc_subtype']
      log("info", f"bc_subtype= = {bc_subtype}")
      # now find the subtype in the list LBoundariesWall and retrieve the index in the list
      entry = get_entry_from_name(bc_subtype,'text',state.LBoundariesOutlet)
      # set the state - this also calls the state function
      state.boundaries_inc_outlet_idx = entry['value']
      # force update of state, so we call the state.change
      state.dirty('boundaries_inc_outlet_idx')

    elif bctype == "Inlet":
      # velocity or pressure
      bc_subtype = state.BCDictList[index]['bc_subtype']
      log("info", f"bc_subtype= = {bc_subtype}")
      # now find the subtype in the list state.LBoundariesInlet and retrieve the index in the list
      entry = get_entry_from_name(bc_subtype,'text',state.LBoundariesInlet)
      # set the state - this also calls the state function
      state.boundaries_inc_inlet_idx = entry['value']
      if 'INC_INLET_USENORMAL' in state.jsonData:
        state.boundary_inc_vel_usenormals_idx=state.jsonData['INC_INLET_USENORMAL']
      log("info", f"usenormals:  = {state.boundary_inc_vel_usenormals_idx}")
      # force update of state, so we call the state.change
      state.dirty('boundaries_inc_inlet_idx')

      state.dirty('boundary_inc_vel_usenormals_idx')

    elif bctype == "Symmetry":
      # symmetry has no other options
      #bc_subtype = state.BCDictList[index]['bc_subtype']
      log("info", "bc_type=symmetry")
      # set the subtype to symmetry because this is what we use in the su2_io file writing
      state.BCDictList[state.selectedBoundaryIndex]['bc_subtype'] = "Symmetry"

      # now find the subtype in the list LBoundariesWall and retrieve the index in the list
      #entry = get_entry_from_name(bc_subtype,'text',state.LBoundariesOutlet)
      # set the state - this also calls the state function
      #state.boundaries_inc_outlet_idx = entry['value']
      # force update of state, so we call the state.change
      #state.dirty('boundaries_inc_outlet_idx')
    elif bctype == "Far-field":
      log("info", f"bc_type=farfield : = {state.BCDictList[state.selectedBoundaryIndex]}")
      state.BCDictList[state.selectedBoundaryIndex]['bc_subtype'] = "Far-field"
      #state.boundaries_farfield_Vx_idx = state.BCDictList[state.selectedBoundaryIndex]['bc_velocity_normal'][0]
      #state.boundaries_farfield_Vy_idx = state.BCDictList[state.selectedBoundaryIndex]['bc_velocity_normal'][1]
      #state.boundaries_farfield_Vz_idx = state.BCDictList[state.selectedBoundaryIndex]['bc_velocity_normal'][2]
      #state.boundaries_farfield_T_idx = state.BCDictList[state.selectedBoundaryIndex]['bc_temperature']
      #state.boundaries_farfield_P_idx = state.BCDictList[state.selectedBoundaryIndex]['bc_pressure']
      #state.boundaries_farfield_rho_idx = state.BCDictList[state.selectedBoundaryIndex]['bc_density']
      if 'FREESTREAM_VELOCITY' in state.jsonData:
        state.boundaries_farfield_Vx_idx = state.jsonData['FREESTREAM_VELOCITY'][0]
        state.boundaries_farfield_Vy_idx = state.jsonData['FREESTREAM_VELOCITY'][1]
        state.boundaries_farfield_Vz_idx = state.jsonData['FREESTREAM_VELOCITY'][2]
      if 'FREESTREAM_TEMPERATURE' in state.jsonData:
        state.boundaries_farfield_T_idx = state.jsonData['FREESTREAM_TEMPERATURE']
      if 'FREESTREAM_PRESSURE' in state.jsonData:
        state.boundaries_farfield_P_idx = state.jsonData['FREESTREAM_PRESSURE']
      if 'FREESTREAM_DENSITY' in state.jsonData:
        state.boundaries_farfield_rho_idx = state.jsonData['FREESTREAM_DENSITY']
      # in the case of farfield, the farfield is:
      # 1. the same for all farfield boundaries
      # 2. stored in the freestream conditions
      state.dirty('boundaries_farfield_Vx_idx')
      state.dirty('boundaries_farfield_Vy_idx')
      state.dirty('boundaries_farfield_Vz_idx')
      state.dirty('boundaries_farfield_T_idx')
      state.dirty('boundaries_farfield_P_idx')
      state.dirty('boundaries_farfield_rho_idx')

      # set the state - this also calls the state function
      #state.boundaries_farfield_idx = entry['value']
      # force update of state, so we call the state.change
      #state.dirty('boundaries_farfield_idx')

    elif bctype == "Supersonic Inlet":
      # Supersonic Inlet has no other options
      state.BCDictList[state.selectedBoundaryIndex]['bc_subtype'] = "Supersonic Inlet"

    elif bctype == "Supersonic Outlet":
      # Supersonic Outlet has no other options
      state.BCDictList[state.selectedBoundaryIndex]['bc_subtype'] = "Supersonic Outlet"


# when the boundary selection changes in the gittree, we go here
# we then update the boundary_main_index
# when the state of boundary index changes, we get the actual boundary condition name
# and type that we stored for the boundary
@state.change("selectedBoundaryName")
def update_boundaries_main(selectedBoundaryName, **kwargs):
    # get the index from the boundary name
    # this shows the right boundary type
    log("info", f"update boundaries main, selected name= = {selectedBoundaryName}")
    # ignore selection of the internal boundary (for now, we do not do anything)
    if selectedBoundaryName != 'internal':
      state.boundaries_main_idx = get_boundaries_main_idx_from_name(selectedBoundaryName)
      state.dirty('boundaries_main_idx')
      
      # Load custom temperature settings if they exist for this boundary
      if hasattr(state, 'selectedBoundaryIndex') and state.selectedBoundaryIndex is not None:
          boundary_data = state.BCDictList[state.selectedBoundaryIndex]
          
          # Load custom temperature settings
          state.enable_custom_temperature = boundary_data.get('custom_temperature', False)
          state.custom_temperature_function = boundary_data.get(
              'temperature_function', 
              "560.0 - 260.0*sin(x*pi / 4)"
          )
          state.temperature_amplitude = boundary_data.get('temperature_amplitude', 257.0)
          state.temperature_frequency = boundary_data.get('temperature_frequency', 0.5)
          
          log("info", f"Loaded custom temperature settings for {selectedBoundaryName}: "
                     f"enabled={state.enable_custom_temperature}, "
                     f"function={state.custom_temperature_function}")



###############################################################
# Boundaries - state changes
###############################################################

# wall type - we get here when we change the wall type in the selection list
# we also have to set/update all the values that are shown in the same dialog window
@state.change("boundaries_wall_idx")
def update_material(boundaries_wall_idx, **kwargs):
    #log("info", f"boundaries wall type index:  = {boundaries_wall_idx}")
    if boundaries_wall_idx==0:
      #log("info", "boundaries_wall_idx:T")
      state.BCDictList[state.selectedBoundaryIndex]['bc_subtype'] = "Temperature"
      state.boundaries_inc_temperature_idx = state.BCDictList[state.selectedBoundaryIndex]['bc_temperature']

    elif boundaries_wall_idx==1:
      #log("info", "boundaries_wall_idx:hf")
      state.BCDictList[state.selectedBoundaryIndex]['bc_subtype'] = "Heat flux"
      state.boundaries_inc_heatflux_idx = state.BCDictList[state.selectedBoundaryIndex]['bc_heatflux']

    elif boundaries_wall_idx==2:
      #log("info", "boundaries_wall_idx:ht")
      state.BCDictList[state.selectedBoundaryIndex]['bc_subtype'] = "Heat transfer"
      state.boundaries_inc_heattransfer_h_idx = state.BCDictList[state.selectedBoundaryIndex]['bc_heattransfer'][0]
      state.boundaries_inc_heattransfer_T_idx = state.BCDictList[state.selectedBoundaryIndex]['bc_heattransfer'][1]
    #log("info", f"BCDictList =  = {state.BCDictList}")

    elif boundaries_wall_idx==3:
      #log("info", "boundaries_wall_idx:hf")
      state.BCDictList[state.selectedBoundaryIndex]['bc_subtype'] = "Euler"

# incompressible temperature has been selected. This means the boundary is of type ISOTHERMAL
@state.change("boundaries_inc_temperature_idx")
def update_material(boundaries_inc_temperature_idx, **kwargs):
    #log("info", f"T:boundaries wall type index:  = {boundaries_inc_temperature_idx}")
    # update config option value we cannot directly add it to the json MARKER_ISOTHERMAL
    # because we do not know about the other boundaries so we add the information to BCDictList
    # so first we have to get which boundary is selected
    #log("info", f"selected boundary name=  = {state.selectedBoundaryName}")
    #log("info", f"selected boundary index=  = {state.selectedBoundaryIndex}")
    #log("info", f"selected boundary value=  = {boundaries_inc_temperature_idx}")
    #state.BCDictList[state.selectedBoundaryIndex]['bcType'] = "Wall"
    #state.BCDictList[state.selectedBoundaryIndex]['bc_subtype'] = "Temperature"
    state.BCDictList[state.selectedBoundaryIndex]['bc_temperature'] = boundaries_inc_temperature_idx
    #log("info", f"BCDictList =  = {state.BCDictList}")

# incompressible heatflux has been selected. This means the boundary is of type HEATFLUX
@state.change("boundaries_inc_heatflux_idx")
def update_material(boundaries_inc_heatflux_idx, **kwargs):
    #log("info", f"HF: boundaries wall type index:  = {boundaries_inc_heatflux_idx}")
    # update config option value we cannot directly add it to the json MARKER_ISOTHERMAL
    # because we do not know about the other boundaries so we add the information to BCDictList
    # so first we have to get which boundary is selected
    #log("info", f"selected boundary name=  = {state.selectedBoundaryName}")
    #log("info", f"selected boundary index=  = {state.selectedBoundaryIndex}")
    #log("info", f"selected boundary value=  = {boundaries_inc_heatflux_idx}")
    state.BCDictList[state.selectedBoundaryIndex]['bcType'] = "Wall"
    state.BCDictList[state.selectedBoundaryIndex]['bc_subtype'] = "Heat flux"
    state.BCDictList[state.selectedBoundaryIndex]['bc_heatflux'] = boundaries_inc_heatflux_idx
    #log("info", f"BCDictList =  = {state.BCDictList}")

# incompressible heattransfer has been selected. This means the boundary is of type HEATTRANSFER
@state.change("boundaries_inc_heattransfer_h_idx")
def update_material(boundaries_inc_heattransfer_h_idx, **kwargs):
    #log("info", f"HT:boundaries wall type index:  = {boundaries_inc_heattransfer_h_idx}")
    # update config option value we cannot directly add it to the json MARKER_HEATTRANSFER
    # because we do not know about the other boundaries so we add the information to BCDictList
    # so first we have to get which boundary is selected
    #log("info", f"selected boundary name=  = {state.selectedBoundaryName}")
    #log("info", f"selected boundary index=  = {state.selectedBoundaryIndex}")
    #log("info", f"selected boundary value=  = {boundaries_inc_heattransfer_h_idx}")
    state.BCDictList[state.selectedBoundaryIndex]['bcType'] = "Wall"
    state.BCDictList[state.selectedBoundaryIndex]['bc_subtype'] = "Heat transfer"
    state.BCDictList[state.selectedBoundaryIndex]['bc_heattransfer'][0] = boundaries_inc_heattransfer_h_idx
    #log("info", f"BCDictList =  = {state.BCDictList}")

@state.change("boundaries_inc_heattransfer_T_idx")
def update_material(boundaries_inc_heattransfer_T_idx, **kwargs):
    log("info", f"boundaries wall type index:  = {boundaries_inc_heattransfer_T_idx}")
    # update config option value we cannot directly add it to the json MARKER_HEATTRANSFER
    # because we do not know about the other boundaries so we add the information to BCDictList
    # so first we have to get which boundary is selected
    #log("info", f"selected boundary name=  = {state.selectedBoundaryName}")
    #log("info", f"selected boundary index=  = {state.selectedBoundaryIndex}")
    state.BCDictList[state.selectedBoundaryIndex]['bcType'] = "Wall"
    state.BCDictList[state.selectedBoundaryIndex]['bc_subtype'] = "Heat transfer"
    state.BCDictList[state.selectedBoundaryIndex]['bc_heattransfer'][1] = boundaries_inc_heattransfer_T_idx
    #log("info", f"BCDictList =  = {state.BCDictList}")

# #################################################################### #
# ############################## INLET ############################### #
# #################################################################### #

# Inlet type
@state.change("boundaries_inc_inlet_idx")
def update_material(boundaries_inc_inlet_idx, **kwargs):
    #log("info", f"boundaries wall type index:  = {boundaries_inc_inlet_idx}")
    # velocity inlet
    if boundaries_inc_inlet_idx==0:
      state.BCDictList[state.selectedBoundaryIndex]['bc_subtype'] = "Velocity inlet"
      # set the state, this will also call state.change
      state.boundaries_inc_velocity_magnitude_idx = state.BCDictList[state.selectedBoundaryIndex]['bc_velocity_magnitude']
      # normal vector (when not using 'normal to boundary face')
      state.boundaries_inc_nx_idx = state.BCDictList[state.selectedBoundaryIndex]['bc_velocity_normal'][0]
      state.boundaries_inc_ny_idx = state.BCDictList[state.selectedBoundaryIndex]['bc_velocity_normal'][1]
      state.boundaries_inc_nz_idx = state.BCDictList[state.selectedBoundaryIndex]['bc_velocity_normal'][2]

      # temperature (only when energy equation is active)
      state.boundaries_inc_temperature_idx = state.BCDictList[state.selectedBoundaryIndex]['bc_temperature']

    # pressure inlet
    elif boundaries_inc_inlet_idx==1:
      state.BCDictList[state.selectedBoundaryIndex]['bc_subtype'] = "Pressure inlet"
      # set the state, this will also call state.change
      state.boundaries_inc_pressure_idx = state.BCDictList[state.selectedBoundaryIndex]['bc_pressure']

      # temperature (only when energy equation is active)
      state.boundaries_inc_temperature_idx = state.BCDictList[state.selectedBoundaryIndex]['bc_temperature']

    # Total Conditions
    elif boundaries_inc_inlet_idx==2:
      state.BCDictList[state.selectedBoundaryIndex]['bc_subtype'] = "Total Conditions"
      # set the state, this will also call state.change
      state.boundaries_inc_pressure_idx = state.BCDictList[state.selectedBoundaryIndex]['bc_pressure']

      # temperature (only when energy equation is active)
      state.boundaries_inc_temperature_idx = state.BCDictList[state.selectedBoundaryIndex]['bc_temperature']

    # Mass Flow
    elif boundaries_inc_inlet_idx==3:
      state.BCDictList[state.selectedBoundaryIndex]['bc_subtype'] = "Mass Flow"
      # set the state, this will also call state.change
      state.boundaries_inc_velocity_magnitude_idx = state.BCDictList[state.selectedBoundaryIndex]['bc_velocity_magnitude']
      # normal vector (when not using 'normal to boundary face')
      state.boundaries_inc_nx_idx = state.BCDictList[state.selectedBoundaryIndex]['bc_velocity_normal'][0]
      state.boundaries_inc_ny_idx = state.BCDictList[state.selectedBoundaryIndex]['bc_velocity_normal'][1]
      state.boundaries_inc_nz_idx = state.BCDictList[state.selectedBoundaryIndex]['bc_velocity_normal'][2]

      # density 
      state.boundaries_inc_density_idx = state.BCDictList[state.selectedBoundaryIndex]['bc_density']

# at the moment, we can only set the usenormal globally
@state.change("boundary_inc_vel_usenormals_idx")
def update_material(boundary_inc_vel_usenormals_idx, **kwargs):
    #log("info", f"inlet boundary velocity use normal:  = {boundary_inc_vel_usenormals_idx}")
    #log("info", f"inlet boundary velocity use normal:  = {state.jsonData['INC_INLET_USENORMAL']}")
    state.jsonData['INC_INLET_USENORMAL'] = bool(boundary_inc_vel_usenormals_idx)
    #log("info", f"inlet boundary velocity use normal:  = {state.jsonData['INC_INLET_USENORMAL']}")

    #state.BCDictList[state.selectedBoundaryIndex]['bcType'] = "Inlet"
    #state.BCDictList[state.selectedBoundaryIndex]['bc_subtype'] = "Velocity inlet"
    #state.BCDictList[state.selectedBoundaryIndex]['bc_velocity_magnitude'] = boundaries_inc_vel_magnitude_idx
    #state.BCDictList[state.selectedBoundaryIndex]['json'] = "MARKER_INLET"
    #log("info", f"BCDictList = {state.BCDictList}")


@state.change("boundaries_inc_velocity_magnitude_idx")
def update_material(boundaries_inc_velocity_magnitude_idx, **kwargs):
    #log("info", f"boundaries inc velocity type index:  = {boundaries_inc_velocity_magnitude_idx}")
    #log("info", f"selected boundary name=  = {state.selectedBoundaryName}")
    #log("info", f"selected boundary index=  = {state.selectedBoundaryIndex}")
    state.BCDictList[state.selectedBoundaryIndex]['bcType'] = "Inlet"
    state.BCDictList[state.selectedBoundaryIndex]['bc_subtype'] = "Velocity inlet" if state.boundaries_inc_inlet_idx==0 else "Mass Flow" 
    state.BCDictList[state.selectedBoundaryIndex]['bc_velocity_magnitude'] = boundaries_inc_velocity_magnitude_idx
    #state.BCDictList[state.selectedBoundaryIndex]['json'] = "MARKER_INLET"
    #log("info", f"BCDictList =  = {state.BCDictList}")


#@state.change("boundaries_inc_temperature_idx")
#def update_material(boundaries_inc_temperature_idx, **kwargs):
#    log("info", f"boundaries temp type index:  = {boundaries_inc_temperature_idx}")
#    log("info", f"selected boundary name=  = {state.selectedBoundaryName}")
#    log("info", f"selected boundary index=  = {state.selectedBoundaryIndex}")
#    #state.BCDictList[state.selectedBoundaryIndex]['bcType'] = "Inlet"
#    #state.BCDictList[state.selectedBoundaryIndex]['bc_subtype'] = "Velocity inlet"
#    state.BCDictList[state.selectedBoundaryIndex]['bc_temperature'] = boundaries_inc_temperature_idx
#    #state.BCDictList[state.selectedBoundaryIndex]['json'] = "MARKER_INLET"
#    log("info", f"BCDictList =  = {state.BCDictList}")


@state.change("boundaries_inc_pressure_idx")
def update_material(boundaries_inc_pressure_idx, **kwargs):
    #log("info", f"boundaries pres type index:  = {boundaries_inc_pressure_idx}")
    #log("info", f"selected boundary name=  = {state.selectedBoundaryName}")
    #log("info", f"selected boundary index=  = {state.selectedBoundaryIndex}")
    state.BCDictList[state.selectedBoundaryIndex]['bcType'] = "Inlet"
    state.BCDictList[state.selectedBoundaryIndex]['bc_subtype'] = "Pressure inlet" if state.boundaries_inc_inlet_idx==1 else "Total Conditions"
    state.BCDictList[state.selectedBoundaryIndex]['bc_pressure'] = boundaries_inc_pressure_idx
    #state.BCDictList[state.selectedBoundaryIndex]['json'] = "MARKER_INLET"
    #log("info", f"BCDictList =  = {state.BCDictList}")


@state.change("boundaries_inc_density_idx")
def update_material(boundaries_inc_density_idx, **kwargs):
    #log("info", f"boundaries pres type index:  = {boundaries_inc_pressure_idx}")
    #log("info", f"selected boundary name=  = {state.selectedBoundaryName}")
    #log("info", f"selected boundary index=  = {state.selectedBoundaryIndex}")
    state.BCDictList[state.selectedBoundaryIndex]['bcType'] = "Inlet"
    state.BCDictList[state.selectedBoundaryIndex]['bc_subtype'] = "Mass Flow"
    state.BCDictList[state.selectedBoundaryIndex]['bc_density'] = boundaries_inc_density_idx
    #state.BCDictList[state.selectedBoundaryIndex]['json'] = "MARKER_INLET"
    #log("info", f"BCDictList =  = {state.BCDictList}")


@state.change("boundaries_inc_nx_idx")
def update_material(boundaries_inc_nx_idx, **kwargs):
    #log("info", f"boundaries nx type index:  = {boundaries_inc_nx_idx}")
    #log("info", f"selected boundary name=  = {state.selectedBoundaryName}")
    #log("info", f"selected boundary index=  = {state.selectedBoundaryIndex}")
    # state.BCDictList[state.selectedBoundaryIndex]['bcType'] = "Inlet"
    # state.BCDictList[state.selectedBoundaryIndex]['bc_subtype'] = "Velocity inlet"
    state.BCDictList[state.selectedBoundaryIndex]['bc_velocity_normal'][0] = boundaries_inc_nx_idx
    #state.BCDictList[state.selectedBoundaryIndex]['json'] = "MARKER_INLET"
    #log("info", f"BCDictList =  = {state.BCDictList}")

@state.change("boundaries_inc_ny_idx")
def update_material(boundaries_inc_ny_idx, **kwargs):
    #log("info", f"boundaries ny type index:  = {boundaries_inc_ny_idx}")
    #log("info", f"selected boundary name=  = {state.selectedBoundaryName}")
    #log("info", f"selected boundary index=  = {state.selectedBoundaryIndex}")
    # state.BCDictList[state.selectedBoundaryIndex]['bcType'] = "Inlet"
    # state.BCDictList[state.selectedBoundaryIndex]['bc_subtype'] = "Velocity inlet"
    state.BCDictList[state.selectedBoundaryIndex]['bc_velocity_normal'][1] = boundaries_inc_ny_idx
    #state.BCDictList[state.selectedBoundaryIndex]['json'] = "MARKER_INLET"
    #log("info", f"BCDictList =  = {state.BCDictList}")

@state.change("boundaries_inc_nz_idx")
def update_material(boundaries_inc_nz_idx, **kwargs):
    #log("info", f"boundaries nz type index:  = {boundaries_inc_nz_idx}")
    #log("info", f"selected boundary name=  = {state.selectedBoundaryName}")
    #log("info", f"selected boundary index=  = {state.selectedBoundaryIndex}")
    # state.BCDictList[state.selectedBoundaryIndex]['bcType'] = "Inlet"
    # state.BCDictList[state.selectedBoundaryIndex]['bc_subtype'] = "Velocity inlet"
    state.BCDictList[state.selectedBoundaryIndex]['bc_velocity_normal'][2] = boundaries_inc_nz_idx
    #state.BCDictList[state.selectedBoundaryIndex]['json'] = "MARKER_INLET"
    #log("info", f"BCDictList =  = {state.BCDictList}")



# #################################################################### #
# ############################## OUTLET ############################## #
# #################################################################### #

# Outlet type, pressure or target mass flow rate (for INC_OUTLET_TYPE)
@state.change("boundaries_inc_outlet_idx")
def update_material(boundaries_inc_outlet_idx, **kwargs):
    #log("info", f"boundaries wall type index:  = {boundaries_inc_outlet_idx}")
    # pressure outlet
    if boundaries_inc_outlet_idx==0:
      state.BCDictList[state.selectedBoundaryIndex]['bc_subtype'] = "Pressure outlet"
      # set the state, this will also call state.change
      state.boundaries_inc_outlet_P_idx = state.BCDictList[state.selectedBoundaryIndex]['bc_pressure']

    # target mass flow rate
    elif boundaries_inc_outlet_idx==1:
      state.BCDictList[state.selectedBoundaryIndex]['bc_subtype'] = "Target mass flow rate"
      state.boundaries_inc_outlet_m_idx = state.BCDictList[state.selectedBoundaryIndex]['bc_massflow']

@state.change("boundaries_inc_outlet_P_idx")
def update_material(boundaries_inc_outlet_P_idx, **kwargs):
    #log("info", f"boundaries P outlet type index:  = {boundaries_inc_outlet_P_idx}")
    #log("info", f"selected boundary name=  = {state.selectedBoundaryName}")
    #log("info", f"selected boundary index=  = {state.selectedBoundaryIndex}")
    state.BCDictList[state.selectedBoundaryIndex]['bcType'] = "Outlet"
    state.BCDictList[state.selectedBoundaryIndex]['bc_subtype'] = "Pressure outlet"
    state.BCDictList[state.selectedBoundaryIndex]['bc_pressure'] = boundaries_inc_outlet_P_idx
    #log("info", f"BCDictList =  = {state.BCDictList}")

@state.change("boundaries_inc_outlet_m_idx")
def update_material(boundaries_inc_outlet_m_idx, **kwargs):
    #log("info", f"boundaries m outlet type index:  = {boundaries_inc_outlet_m_idx}")
    #log("info", f"selected boundary name=  = {state.selectedBoundaryName}")
    #log("info", f"selected boundary index=  = {state.selectedBoundaryIndex}")
    state.BCDictList[state.selectedBoundaryIndex]['bcType'] = "Outlet"
    state.BCDictList[state.selectedBoundaryIndex]['bc_subtype'] = "Target mass flow rate"
    state.BCDictList[state.selectedBoundaryIndex]['bc_massflow'] = boundaries_inc_outlet_m_idx
    #log("info", f"BCDictList =  = {state.BCDictList}")


# #################################################################### #
# ############################## FARFIELD############################# #
# #################################################################### #

@state.change("boundaries_farfield_Vx_idx")
def update_material(boundaries_farfield_Vx_idx, **kwargs):
    #log("info", f"boundaries farfield type index:  = {boundaries_farfield_Vx_idx}")
    #log("info", f"selected boundary name=  = {state.selectedBoundaryName}")
    #log("info", f"selected boundary index=  = {state.selectedBoundaryIndex}")
    state.BCDictList[state.selectedBoundaryIndex]['bcType'] = "Far-field"
    state.BCDictList[state.selectedBoundaryIndex]['bc_velocity_normal'][0] = boundaries_farfield_Vx_idx
    #log("info", f"BCDictList =  = {state.BCDictList}")
    if 'FREESTREAM_VELOCITY' not in state.jsonData:
       state.jsonData['FREESTREAM_VELOCITY'] = [0,0,0]
    state.jsonData['FREESTREAM_VELOCITY'][0]=boundaries_farfield_Vx_idx

@state.change("boundaries_farfield_Vy_idx")
def update_material(boundaries_farfield_Vy_idx, **kwargs):
    #log("info", f"boundaries farfield type index:  = {boundaries_farfield_Vy_idx}")
    #log("info", f"selected boundary name=  = {state.selectedBoundaryName}")
    #log("info", f"selected boundary index=  = {state.selectedBoundaryIndex}")
    state.BCDictList[state.selectedBoundaryIndex]['bcType'] = "Far-field"
    state.BCDictList[state.selectedBoundaryIndex]['bc_velocity_normal'][1] = boundaries_farfield_Vy_idx
    #log("info", f"BCDictList =  = {state.BCDictList}")
    if 'FREESTREAM_VELOCITY' not in state.jsonData:
       state.jsonData['FREESTREAM_VELOCITY'] = [0,0,0]
    state.jsonData['FREESTREAM_VELOCITY'][1]=boundaries_farfield_Vy_idx

@state.change("boundaries_farfield_Vz_idx")
def update_material(boundaries_farfield_Vz_idx, **kwargs):
    #log("info", f"boundaries farfield type index:  = {boundaries_farfield_Vz_idx}")
    #log("info", f"selected boundary name=  = {state.selectedBoundaryName}")
    #log("info", f"selected boundary index=  = {state.selectedBoundaryIndex}")
    state.BCDictList[state.selectedBoundaryIndex]['bcType'] = "Far-field"
    state.BCDictList[state.selectedBoundaryIndex]['bc_velocity_normal'][0] = boundaries_farfield_Vz_idx
    #log("info", f"BCDictList =  = {state.BCDictList}")
    if 'FREESTREAM_VELOCITY' not in state.jsonData:
       state.jsonData['FREESTREAM_VELOCITY'] = [0,0,0]
    state.jsonData['FREESTREAM_VELOCITY'][2]=boundaries_farfield_Vz_idx

@state.change("boundaries_farfield_T_idx")
def update_material(boundaries_farfield_T_idx, **kwargs):
    #log("info", f"boundaries farfield type index:  = {boundaries_farfield_T_idx}")
    #log("info", f"selected boundary name=  = {state.selectedBoundaryName}")
    #log("info", f"selected boundary index=  = {state.selectedBoundaryIndex}")
    state.BCDictList[state.selectedBoundaryIndex]['bcType'] = "Far-field"
    state.BCDictList[state.selectedBoundaryIndex]['bc_temperature'] = boundaries_farfield_T_idx
    #log("info", f"BCDictList =  = {state.BCDictList}")
    state.jsonData['FREESTREAM_TEMPERATURE']=boundaries_farfield_T_idx

@state.change("boundaries_farfield_P_idx")
def update_material(boundaries_farfield_P_idx, **kwargs):
    #log("info", f"boundaries farfield type index:  = {boundaries_farfield_P_idx}")
    #log("info", f"selected boundary name=  = {state.selectedBoundaryName}")
    #log("info", f"selected boundary index=  = {state.selectedBoundaryIndex}")
    state.BCDictList[state.selectedBoundaryIndex]['bcType'] = "Far-field"
    state.BCDictList[state.selectedBoundaryIndex]['bc_pressure'] = boundaries_farfield_P_idx
    #log("info", f"BCDictList =  = {state.BCDictList}")
    state.jsonData['FREESTREAM_PRESSURE']=boundaries_farfield_P_idx

@state.change("boundaries_farfield_rho_idx")
def update_material(boundaries_farfield_rho_idx, **kwargs):
    #log("info", f"boundaries farfield type index:  = {boundaries_farfield_rho_idx}")
    #log("info", f"selected boundary name=  = {state.selectedBoundaryName}")
    #log("info", f"selected boundary index=  = {state.selectedBoundaryIndex}")
    state.BCDictList[state.selectedBoundaryIndex]['bcType'] = "Far-field"
    state.BCDictList[state.selectedBoundaryIndex]['bc_density'] = boundaries_farfield_rho_idx
    #log("info", f"BCDictList =  = {state.BCDictList}")
    state.jsonData['FREESTREAM_DENSITY']=boundaries_farfield_rho_idx



# #################################################################### #
# ########################## SUPERSONIC-INLET######################### #
# #################################################################### #

@state.change("boundaries_inc_spr_pressure_idx")
def update_material(boundaries_inc_spr_pressure_idx, **kwargs):
    state.BCDictList[state.selectedBoundaryIndex]['bc_pressure'] = boundaries_inc_spr_pressure_idx
    #state.BCDictList[state.selectedBoundaryIndex]['json'] = "MARKER_SUPERSONIC_INLET"
    #log("info", f"BCDictList =  = {state.BCDictList}")

@state.change("boundaries_inc_spr_temperature_idx")
def update_material(boundaries_inc_spr_temperature_idx, **kwargs):
    state.BCDictList[state.selectedBoundaryIndex]['bc_temperature'] = boundaries_inc_spr_temperature_idx
    #log("info", f"BCDictList =  = {state.BCDictList}")

@state.change("boundaries_spr_nx_idx")
def update_material(boundaries_spr_nx_idx, **kwargs):
    state.BCDictList[state.selectedBoundaryIndex]['bc_velocity_normal'][0] = boundaries_spr_nx_idx
    #log("info", f"BCDictList =  = {state.BCDictList}")

@state.change("boundaries_spr_ny_idx")
def update_material(boundaries_spr_ny_idx, **kwargs):
    state.BCDictList[state.selectedBoundaryIndex]['bc_velocity_normal'][1] = boundaries_spr_ny_idx
    #log("info", f"BCDictList =  = {state.BCDictList}")

@state.change("boundaries_spr_nz_idx")
def update_material(boundaries_spr_nz_idx, **kwargs):
    state.BCDictList[state.selectedBoundaryIndex]['bc_velocity_normal'][2] = boundaries_spr_nz_idx
    #log("info", f"BCDictList =  = {state.BCDictList}")

# #################################################################### #
# ########################## CUSTOM TEMPERATURE ######################### #
# #################################################################### #

@state.change("enable_custom_temperature")
def update_custom_temperature_enabled(enable_custom_temperature, **kwargs):
    """Update boundary conditions when custom temperature is enabled/disabled."""
    log("info", f"Custom temperature enabled: {enable_custom_temperature}")
    if hasattr(state, 'selectedBoundaryIndex') and state.selectedBoundaryIndex is not None:
        if enable_custom_temperature:
            # Mark this boundary as having custom temperature            state.BCDictList[state.selectedBoundaryIndex]['custom_temperature'] = True
            state.BCDictList[state.selectedBoundaryIndex]['temperature_function'] = getattr(
                state, 'custom_temperature_function', 
                "293.0 + 57.0*sin(2*pi*time)"
            )
        else:
            # Remove custom temperature settings
            if 'custom_temperature' in state.BCDictList[state.selectedBoundaryIndex]:
                del state.BCDictList[state.selectedBoundaryIndex]['custom_temperature']
            if 'temperature_function' in state.BCDictList[state.selectedBoundaryIndex]:
                del state.BCDictList[state.selectedBoundaryIndex]['temperature_function']

@state.change("custom_temperature_function")
def update_custom_temperature_function(custom_temperature_function, **kwargs):
    """Update the temperature function when it changes."""
    log("info", f"Custom temperature function: {custom_temperature_function}")
    if (hasattr(state, 'selectedBoundaryIndex') and state.selectedBoundaryIndex is not None and
        getattr(state, 'enable_custom_temperature', False)):
        state.BCDictList[state.selectedBoundaryIndex]['temperature_function'] = custom_temperature_function

@state.change("temperature_amplitude")
def update_temperature_amplitude(temperature_amplitude, **kwargs):
    """Update temperature amplitude parameter."""
    log("info", f"Temperature amplitude: {temperature_amplitude}")
    if (hasattr(state, 'selectedBoundaryIndex') and state.selectedBoundaryIndex is not None and
        getattr(state, 'enable_custom_temperature', False)):
        state.BCDictList[state.selectedBoundaryIndex]['temperature_amplitude'] = temperature_amplitude

@state.change("temperature_frequency")
def update_temperature_frequency(temperature_frequency, **kwargs):
    """Update temperature frequency parameter."""
    log("info", f"Temperature frequency: {temperature_frequency}")
    if (hasattr(state, 'selectedBoundaryIndex') and state.selectedBoundaryIndex is not None and
        getattr(state, 'enable_custom_temperature', False)):
        state.BCDictList[state.selectedBoundaryIndex]['temperature_frequency'] = temperature_frequency

# Test function to verify button clicks work
def test_button_click():
    log("info", "TEST BUTTON CLICKED SUCCESSFULLY!")
    generate_python_wrapper_with_dynamic_temp()
    print("Button click test successful!")

# Register the test function
ctrl.test_button_click = test_button_click

@state.change("wrapper_type")
def update_wrapper_type(wrapper_type, **kwargs):
    """Update default temperature formula when wrapper type changes."""
    log("info", f"Wrapper type changed to: {wrapper_type}")
    
    # Update default formula based on wrapper type
    if wrapper_type == "simple":
        # Position-based formula for simple wrapper - use the working formula
        default_formula = "560.0 - 260.0*sin(x*pi / 4)"
        state.custom_temperature_function = default_formula
        log("info", "Updated to position-based formula for simple wrapper")
    # else:
    #     # Time-based formula commented out - not supported
    #     default_formula = "a + b*sin(c*pi*time)"
    #     state.custom_temperature_function = default_formula
    #     log("info", "Updated to time-based formula for unsteady CHT wrapper")
    
    # Update the stored boundary settings
    if hasattr(state, 'selectedBoundaryIndex') and state.selectedBoundaryIndex is not None:
        state.BCDictList[state.selectedBoundaryIndex]['wrapper_type'] = wrapper_type
        state.BCDictList[state.selectedBoundaryIndex]['temperature_function'] = state.custom_temperature_function

# === Per-marker subtype array helpers ===
def _sync_inlet_type_arrays():
  """Ensure INC_INLET_TYPE / INLET_TYPE arrays match BCDictList order for Inlet markers."""
  try:
    inlet_markers = [bc for bc in state.BCDictList if bc.get('bcType') == 'Inlet']
    inc = 'INC' in str(state.jsonData.get('SOLVER', ''))
    if inc:
      types = state.jsonData.get('INC_INLET_TYPE', [])
      if isinstance(types, str):
        types = [types]
      mapping = {
        'Velocity inlet': 'VELOCITY_INLET',
        'Pressure inlet': 'PRESSURE_INLET',
        'Total Conditions': 'TOTAL_CONDITIONS',
        'Mass Flow': 'MASS_FLOW',
      }
      new_types = [mapping.get(bc.get('bc_subtype'), types[0] if types else 'VELOCITY_INLET') for bc in inlet_markers]
      state.jsonData['INC_INLET_TYPE'] = new_types
    else:
      types = state.jsonData.get('INLET_TYPE', [])
      if isinstance(types, str):
        types = [types]
      mapping = {
        'Total Conditions': 'TOTAL_CONDITIONS',
        'Mass Flow': 'MASS_FLOW',
      }
      default = types[0] if types else 'TOTAL_CONDITIONS'
      new_types = [mapping.get(bc.get('bc_subtype'), default) for bc in inlet_markers]
      state.jsonData['INLET_TYPE'] = new_types
    state.dirty('jsonData')
  except Exception as e:
    log('warn', f'Failed to sync inlet types: {e}')

def _sync_outlet_type_arrays():
  """Ensure INC_OUTLET_TYPE arrays match BCDictList order for Outlet markers."""
  try:
    outlet_markers = [bc for bc in state.BCDictList if bc.get('bcType') == 'Outlet']
    types = state.jsonData.get('INC_OUTLET_TYPE', [])
    if isinstance(types, str):
      types = [types]
    mapping = {
      'Pressure outlet': 'PRESSURE_OUTLET',
      'Target mass flow rate': 'MASS_FLOW_OUTLET',
    }
    default = types[0] if types else 'PRESSURE_OUTLET'
    new_types = [mapping.get(bc.get('bc_subtype'), default) for bc in outlet_markers]
    state.jsonData['INC_OUTLET_TYPE'] = new_types
    state.dirty('jsonData')
  except Exception as e:
    log('warn', f'Failed to sync outlet types: {e}')

def set_inlet_bc_subtype(bc_name, subtype):
  """Set inlet subtype for a specific marker name and sync arrays."""
  try:
    for bc in state.BCDictList:
      if bc.get('bcName') == bc_name and bc.get('bcType') == 'Inlet':
        bc['bc_subtype'] = subtype
        break
    _sync_inlet_type_arrays()
  except Exception as e:
    log('warn', f'Failed to set inlet subtype: {e}')

def set_outlet_bc_subtype(bc_name, subtype):
  """Set outlet subtype for a specific marker name and sync arrays."""
  try:
    for bc in state.BCDictList:
      if bc.get('bcName') == bc_name and bc.get('bcType') == 'Outlet':
        bc['bc_subtype'] = subtype
        break
    _sync_outlet_type_arrays()
  except Exception as e:
    log('warn', f'Failed to set outlet subtype: {e}')

# Register helpers on controller for UI buttons
ctrl.set_inlet_bc_subtype = set_inlet_bc_subtype
ctrl.set_outlet_bc_subtype = set_outlet_bc_subtype


