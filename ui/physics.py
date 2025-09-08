# physics gittree menu


# note that in the main menu, we need to call add the following:
# 1) from ui.fileio import *
# 2) call fileio_card() in SinglePageWithDrawerLayout
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
from ui.materials import *
state, ctrl = server.state, server.controller

# show the material dialog cards
state.show_wall_function_dialog_card = False


############################################################################
# Physics models - list options #
############################################################################

# List: physics model: {compressible, incompressible} selection
LPhysicsComp= [
  {"text": "Incompressible", "value": 0},
  {"text": "Compressible", "value": 1},
]

# List: physics model: Turbulence: {SA, SST} selection
LPhysicsTurbModel= [
  {"text": "Inviscid (Euler)", "value": 0},
  {"text": "Laminar (Navier-Stokes)", "value": 1},
  {"text": "Spalart-Allmaras (RANS)", "value": 2},
  {"text": "k-omega SST (RANS)", "value": 3},
]

# List: physics model: Spalart-Allmaras options: selection
LPhysicsTurbSAOptions= [
        {"text": "Default", "value": 0, "json":"NONE"},
        {"text": "Negative", "value": 1,"json":"NEGATIVE"},
        {"text": "Edwards", "value": 2,"json":"EDWARDS"},
        ]


# List: physics model: SST options
LPhysicsTurbSSTOptions= [
        {"text": "V1994m", "value": 0, "json":"V1994m"},
        {"text": "V2003m", "value": 1, "json":"V2003m"},
        ]



# set the state variables using the json data from the config file
def set_json_physics():
  """Set physics based on JSON configuration with proper error handling"""
  
  # ABSOLUTE SAFETY: Force ensure state.jsonData exists and has SOLVER
  if not hasattr(state, 'jsonData') or not isinstance(state.jsonData, dict) or state.jsonData is None:
    state.jsonData = {'SOLVER': 'NAVIER_STOKES', 'KIND_TURB_MODEL': 'SA'}
  if 'SOLVER' not in state.jsonData:
    state.jsonData['SOLVER'] = 'NAVIER_STOKES'
  
  try:
    # Absolutely ensure jsonData exists and has SOLVER key
    if not hasattr(state, 'jsonData') or state.jsonData is None:
      state.jsonData = {'SOLVER': 'NAVIER_STOKES', 'KIND_TURB_MODEL': 'SA'}
      log("warning", "jsonData was None, initialized with defaults")
    
    # Absolutely ensure SOLVER key exists
    if 'SOLVER' not in state.jsonData:
      state.jsonData['SOLVER'] = 'NAVIER_STOKES'
      log("warning", "SOLVER key missing, added default")
      
    # Safely get the solver value with default fallback
    solver = state.jsonData.get('SOLVER', 'NAVIER_STOKES').upper()
    
    # energy equation on/off
    if 'INC_ENERGY_EQUATION' in state.jsonData:
      state.physics_energy_idx = bool(state.jsonData['INC_ENERGY_EQUATION']==True)
      log("debug", f"       ################# energy equation =  = {state.physics_energy_idx}")

    # compressible or incompressible
    state.physics_comp_idx = 0 if "INC" in solver else 1
    log("debug", f"       ################# compressible=  = {state.physics_comp_idx}")

    # energy equation can be deactivated only for inc_rans and inc_navier-stokes?
    state.physics_energy_always_on = 0 if (solver=='INC_NAVIER_STOKES' or solver=='INC_RANS') else 1
    log("debug", f"energy always on =  = {state.physics_energy_always_on}")

    # the SA options
    state.SAOptions={"NONE":True,
                     "QCR2000":False,
                     "WITHFT2":False,
                     "COMPRESSIBILITY":False,
                     "EDWARDS":False,
                     "ROTATION":False,
                     "BCM":False,
                     "NEGATIVE":False,
                     "EXPERIMENTAL":True
                    }

    # turbulence model
    state.physics_turb_idx = 0
    state.physics_turb_sst_idx = 0
    state.physics_turb_sa_idx = 0
    state.physics_turb_sa_ft2_idx = 0
    state.physics_turb_sa_qcr2000_idx = 0
    state.physics_turb_sa_compressibility_idx = 0
    state.physics_turb_sa_rotation_idx = 0
    state.physics_turb_sa_bcm_idx = 0    # Set physics based on solver type with safe checking
    log("debug", f"About to check solver type: '{solver}'")
    if "EULER" in solver:
       log("info", "EULER solver")
       state.physics_turb_idx = 0
    elif "NAVIER_STOKES" in solver:
       log("info", "NAVIER-STOKES solver")
       state.physics_turb_idx = 1
    elif "RANS" in solver:
      log("info", "RANS solver")
      turb_model = state.jsonData.get('KIND_TURB_MODEL', 'SA')
      if turb_model == "SA":
        log("info", "SA model")
        # must be SA
        state.physics_turb_idx = 2
        # activate sub_ui        #state.active_sub_ui = "subphysics_sa"
        #pipeline.update_node_value("Physics","subui",active_sub_ui)
        
        if 'SA_OPTIONS' in state.jsonData:
          if "NEGATIVE" in state.jsonData['SA_OPTIONS']:
              state.physics_turb_sa_idx = 1
          elif "EDWARDS" in state.jsonData['SA_OPTIONS']:
              state.physics_turb_sa_idx = 2

          # SA submodels
          state.physics_turb_sa_ft2_idx= bool("WITHFT2" in state.jsonData['SA_OPTIONS'])
          state.physics_turb_sa_qcr2000_idx= bool("QCR200" in state.jsonData['SA_OPTIONS'])
          state.physics_turb_sa_compressibility_idx= bool("COMPRESSIBILITY" in state.jsonData['SA_OPTIONS'])
          state.physics_turb_sa_rotation_idx= bool("ROTATION" in state.jsonData['SA_OPTIONS'])
          state.physics_turb_sa_bcm_idx= bool("BCM" in state.jsonData['SA_OPTIONS'])
      else:
        log("info", "SST model")
        state.physics_turb_idx = 3
        # activate sub_ui
        #state.active_sub_ui = "subphysics_sst"
        if 'SST_OPTIONS' in state.jsonData:
          state.physics_turb_sst_idx= GetJsonIndex(state.jsonData['SST_OPTIONS'],LPhysicsTurbSSTOptions)
    else:
       log("info", "No RANS solver, using default turbulence settings")

    # settings for wall functions
    if ('WALLMODEL_KAPPA' in state.jsonData):
        state.wallmodel_kappa_idx = state.jsonData['WALLMODEL_KAPPA']
    if ('WALLMODEL_B' in state.jsonData):   
        state.wallmodel_b_idx = state.jsonData['WALLMODEL_B']
    if ('WALLMODEL_MINYPLUS' in state.jsonData):   
        state.wallmodel_miny_idx = state.jsonData['WALLMODEL_MINYPLUS']
    if ('WALLMODEL_MAXITER' in state.jsonData):  
        state.wallmodel_maxiter_idx = state.jsonData['WALLMODEL_MAXITER'] 
    if ('WALLMODEL_RELFAC' in state.jsonData):  
        state.wallmodel_relax_factor_idx = state.jsonData['WALLMODEL_RELFAC']
    if ('MARKER_WALL_FUNCTIONS' in state.jsonData):
        state.wall_function = True
    else:
        state.wall_function = False

  except Exception as e:
    log("error", f"Error setting physics from JSON: {str(e)}")
    # Set safe defaults
    state.physics_turb_idx = 0
    state.physics_comp_idx = 1
    state.physics_energy_always_on = 1
    state.wall_function = False

  # Always update state variables
  state.dirty('physics_energy_idx')
  state.dirty('physics_comp_idx')
  state.dirty('physics_energy_always_on')

  state.dirty('physics_turb_idx')
  state.dirty('physics_turb_sa_ft2_idx')
  state.dirty('physics_turb_sa_qcr2000_idx')
  state.dirty('physics_turb_sa_compressibility_idx')
  state.dirty('physics_turb_sa_rotation_idx')
  state.dirty('physics_turb_sa_bcm_idx')
  state.dirty('physics_turb_sst_idx')

  update_physics_comp(state.physics_comp_idx)

  # call sub_ui to update if we need to show the subui or not

###############################################################
# PIPELINE CARD : PHYSICS
###############################################################
def physics_card():
    with ui_card(title="Physics", ui_name="Physics"):
        log("info", "     ## Physics Selection ##")

        # todo: viscous flow on/off (Euler vs Navier-Stokes)

        # 2 columns, left containing compressible/incompressible
        # right containing energy on/off (for incompressible only)
        with vuetify.VRow(classes="pt-2"):
            with vuetify.VCol(cols="6"):
                # first a list selection for compressible/incompressible
                vuetify.VSelect(
                    # What to do when something is selected
                    v_model=("physics_comp_idx", 0),
                    # The items in the list
                    items=("representations_comp",LPhysicsComp),
                    # the name of the list box
                    label="Solver",
                    hide_details=True,
                    dense=True,
                    outlined=True,
                    classes="mt-0 pt-0",
                )
            with vuetify.VCol(cols="6"):
                # checkbox for energy (can only be deselected for incompressible)
                vuetify.VCheckbox(
                    v_model=("physics_energy_idx", True),
                    label="Energy equation",
                    # activate or deactivate/disable the checkbox
                    # only active for incompressible flow
                    # else, default is on
                    disabled=("physics_energy_always_on",0),
                    classes="mt-1 pt-1",
                    hide_details=True,
                    dense=True,
                )

        # Then a list selection for turbulence submodels
        vuetify.VSelect(
            # What to do when something is selected
            # the value is the default
            v_model=("physics_turb_idx", 0),
            # The items in the list
            items=("representations_turb",LPhysicsTurbModel),
            # the name of the list box
            label="Turbulence model",
            hide_details=True,
            dense=True,
            outlined=True,
            classes="pt-1 mt-1",
        )
        
        with vuetify.VRow(classes="pt-2"):
            with vuetify.VCol(cols="6"):
                vuetify.VCheckbox(
                    v_model=("wall_function", False),
                    label="Wall Function",
                    classes="mt-1 pt-1",
                    # use wall function only if the turbulence model is RANS or INC_RANS
                    disabled=("physics_turb_idx < 2",0),
                    hide_details=True,
                    dense=True,
                )
            with vuetify.VCol(cols="4"):
              with vuetify.VBtn(
                                elevation=1,
                                variant="text",
                                color="white",
                                click=update_wall_function_dialog_card,
                                disabled=("!wall_function",0),
                                icon="mdi-dots-vertical"):
                vuetify.VIcon("mdi-dots-vertical",density="compact",color="green")


###############################################################


# WALL FUNCTION Dialog box
# Marker_wall is built by su2_io->createjsonMarkers
# and not stored in BCDictList
def wall_function_dialog_card():
    with vuetify.VDialog(width=300,position='{X:10,Y:10}',transition="dialog-top-transition",v_model=("show_wall_function_dialog_card",False)):
      with vuetify.VCard():

        vuetify.VCardTitle("Wall Functions",
                           classes="grey lighten-1 py-1 grey--text text--darken-3")
        
        with vuetify.VContainer(fluid=True, classes="pl-4"):
          # ####################################################### #
          with vuetify.VRow(classes="py-0 my-0"):
            with vuetify.VCol(cols="8"):
              vuetify.VTextField(
                v_model=("wallmodel_kappa_idx", 0.41),
                label="Von Karman Constant",
              )
          with vuetify.VRow(classes="py-0 my-0"):
            with vuetify.VCol(cols="8"):
              vuetify.VTextField(
                v_model=("wallmodel_b_idx", 5.0),
                label="Model Constant B",
              )
          with vuetify.VRow(classes="py-0 my-0"):
            with vuetify.VCol(cols="8"):
              vuetify.VTextField(
                v_model=("wallmodel_miny_idx", 5.5),
                label="Minimum Y+ value",
              )
          with vuetify.VRow(classes="py-0 my-0"):
            with vuetify.VCol(cols="8"):
              vuetify.VTextField(
                v_model=("wallmodel_maxiter_idx", 200),
                label="Max Newton iterations",
              )
          with vuetify.VRow(classes="py-0 my-0"):
            with vuetify.VCol(cols="8"):
              vuetify.VTextField(
                v_model=("wallmodel_relax_factor_idx", 0.5),
                label="Relaxation factor",
              )
        
        with vuetify.VCardText():
          vuetify.VBtn("close", click=update_wall_function_dialog_card)


###############################################################
# Wall Functions 
###############################################################

def update_wall_function_dialog_card():
    state.show_wall_function_dialog_card = not state.show_wall_function_dialog_card

@state.change("wall_function")
def update_wall_function(wall_function, **kwargs):
    log("info", f"     wall function selection:  = {wall_function}")
    if wall_function==False:
        keys_to_remove = [
            "MARKER_WALL_FUNCTIONS",
            # "WALLMODEL_KAPPA",
            # "WALLMODEL_B",
            # "WALLMODEL_MINYPLUS",
            # "WALLMODEL_MAXITER",
            # "WALLMODEL_RELFAC"
            ]   

        for key in keys_to_remove:
            state.jsonData.pop(key, None)
    # else:
    #     state.jsonData['WALLMODEL_KAPPA'] = state.wallmodel_kappa_idx
    #     state.jsonData['WALLMODEL_B'] = state.wallmodel_b_idx
    #     state.jsonData['WALLMODEL_MINYPLUS'] = state.wallmodel_miny_idx
    #     state.jsonData['WALLMODEL_MAXITER'] = state.wallmodel_maxiter_idx
    #     state.jsonData['WALLMODEL_RELFAC'] = state.wallmodel_relax_factor_idx
    
    state.dirty('jsonData')

@state.change("wallmodel_kappa_idx")
def update_wallmodel_kappa(wallmodel_kappa_idx, **kwargs):
    if state.wall_function:
      try:
          state.jsonData['WALLMODEL_KAPPA'] = float(wallmodel_kappa_idx)
      except Exception as e:
          log("error", f"Error in setting wallmodel_kappa_idx:  \n {e}")

@state.change("wallmodel_b_idx")
def update_wallmodel_b(wallmodel_b_idx, **kwargs):
    if state.wall_function:
      try:
          state.jsonData['WALLMODEL_B'] = float(wallmodel_b_idx)
      except Exception as e:  
          log("error", f"Error in setting wallmodel_b_idx:  \n {e}")

@state.change("wallmodel_miny_idx")
def update_wallmodel_miny(wallmodel_miny_idx, **kwargs):
    if state.wall_function:
      try:
        state.jsonData['WALLMODEL_MINYPLUS'] = float(wallmodel_miny_idx)
      except Exception as e:
        log("error", f"Error in setting wallmodel_miny_idx:  \n {e}")

@state.change("wallmodel_maxiter_idx")
def update_wallmodel_maxiter(wallmodel_maxiter_idx, **kwargs):
    if state.wall_function:
      try:
        state.jsonData['WALLMODEL_MAXITER'] = float(wallmodel_maxiter_idx)
      except Exception as e:
        log("error", f"Error in setting wallmodel_maxiter_idx:  \n {e}")

@state.change("wallmodel_relax_factor_idx")
def update_wallmodel_relax_factor(wallmodel_relax_factor_idx, **kwargs):
    if state.wall_function:
      try:
        state.jsonData['WALLMODEL_RELFAC'] = float(wallmodel_relax_factor_idx)
      except Exception as e:
        log("error", f"Error in setting wallmodel_relax_factor_idx:  \n {e}")



###############################################################
# turbulence - SST - model options
###############################################################
@state.change("physics_turb_sst_idx")
def update_physics_turb_sst(physics_turb_sst_idx, **kwargs):
    log("info", f"     turbulence model selection:  = {physics_turb_sst_idx}")
    state.jsonData['SST_OPTIONS']= GetJsonName(physics_turb_sst_idx,LPhysicsTurbSSTOptions)

###############################################################
# turbulence - SA - model options
###############################################################
@state.change("physics_turb_sa_idx")
def update_physics_turb_sa(physics_turb_sa_idx, **kwargs):
    log("info", f"     turbulence model selection:  = {physics_turb_sa_idx}")
    #NONE should be false
    state.SAOptions['NONE'] = False
    state.SAOptions['NEGATIVE'] = False
    state.SAOptions['EDWARDS'] = False
    state.SAOptions[GetJsonName(physics_turb_sa_idx,LPhysicsTurbSAOptions)] = True
    log("info", f"     SA options= = {state.SAOptions}")
    optionstring=""
    for key in state.SAOptions:
      value=state.SAOptions[key]
      if value==True:
          optionstring += str(key) + " "
    state.jsonData['SA_OPTIONS']= optionstring

@state.change("physics_turb_sa_ft2_idx")
def update_physics_turb_sa(physics_turb_sa_ft2_idx, **kwargs):
    log("info", f"     turbulence model selection:  = {physics_turb_sa_ft2_idx}")
    state.SAOptions['NONE'] = False
    state.SAOptions['WITHFT2'] = physics_turb_sa_ft2_idx
    log("info", f"     SA options= = {state.SAOptions}")
    optionstring=""
    for key in state.SAOptions:
      value=state.SAOptions[key]
      if (value==True):
          log("info", f"           key= = {key} val= {value}")
          optionstring += str(key) + " "
    state.jsonData['SA_OPTIONS']= optionstring

@state.change("physics_turb_sa_qcr2000_idx")
def update_physics_turb_sa(physics_turb_sa_qcr2000_idx, **kwargs):
    log("info", f"     turbulence model selection:  = {physics_turb_sa_qcr2000_idx}")
    state.SAOptions['NONE'] = False
    state.SAOptions['QCR2000'] = physics_turb_sa_qcr2000_idx
    log("info", f"     SA options= = {state.SAOptions}")
    optionstring=""
    for key in state.SAOptions:
      value=state.SAOptions[key]
      if (value==True):
          log("info", f"           key= = {key} val= {value}")
          optionstring += str(key) + " "
    state.jsonData['SA_OPTIONS']= optionstring

@state.change("physics_turb_sa_compressibility_idx")
def update_physics_turb_sa(physics_turb_sa_compressibility_idx, **kwargs):
    log("info", f"     turbulence model selection:  = {physics_turb_sa_compressibility_idx}")
    state.SAOptions['NONE'] = False
    state.SAOptions['COMPRESSIBILITY'] = physics_turb_sa_compressibility_idx
    optionstring=""
    for key in state.SAOptions:
      value=state.SAOptions[key]
      if (value==True):
          log("info", f"           key= = {key} val= {value}")
          optionstring += str(key) + " "
    state.jsonData['SA_OPTIONS']= optionstring

@state.change("physics_turb_sa_rotation_idx")
def update_physics_turb_sa(physics_turb_sa_rotation_idx, **kwargs):
    log("info", f"     turbulence model selection:  = {physics_turb_sa_rotation_idx}")
    state.SAOptions['NONE'] = False
    state.SAOptions['ROTATION'] = physics_turb_sa_rotation_idx
    optionstring=""
    for key in state.SAOptions:
      value=state.SAOptions[key]
      if (value==True):
          log("info", f"           key = {key} val = {value}")
          optionstring += str(key) + " "
    state.jsonData['SA_OPTIONS']= optionstring

@state.change("physics_turb_sa_bcm_idx")
def update_physics_turb_sa(physics_turb_sa_bcm_idx, **kwargs):
    log("info", f"     turbulence model selection:  = {physics_turb_sa_bcm_idx}")
    state.SAOptions['NONE'] = False
    state.SAOptions['BCM'] = physics_turb_sa_bcm_idx
    optionstring=""
    for key in state.SAOptions:
      value=state.SAOptions[key]
      if (value==True):
          log("info", f"           key = {key} val = {value}")
          optionstring += str(key) + " "
    state.jsonData['SA_OPTIONS']= optionstring

###############################################################
# physics - energy equation
###############################################################
@state.change("physics_energy_idx")
def update_physics_energy(physics_energy_idx, **kwargs):

    log("info", f"     energy selection:  = {physics_energy_idx}")
    # can only be activated/deactivated for incompressible
    #state.energy = bool(state.physics_energy_idx)

    if 'INC_DENSITY_MODEL' in state.jsonData and state.jsonData['INC_DENSITY_MODEL']!='CONSTANT':
        state.jsonData['INC_ENERGY_EQUATION']= bool(physics_energy_idx)

    # update jsonData
    state.dirty("jsonData")



############################################################################
# UI value update: Physics properties #
############################################################################
@state.change("physics_comp_idx")
def update_physics_comp(physics_comp_idx, **kwargs):
    log("info", f"     compressible selection:  = {physics_comp_idx}")
    # compressible selected means we have either NAVIER_STOKES or RANS or EULER
    # incompressible selected means we have either INC_RANS or INC_NAVIER_STOKES or INC_EULER
    # This option goes together with the turbulence option

    compressible = bool(physics_comp_idx)
    log("info", f"compressible =  = {compressible}")

    # update the turbulence models from compressible to incompressible or vice versa
    update_physics_turb(state.physics_turb_idx)

    # select compressible or incompressible options for:
    # - fluid materials (density)
    # - fluid materials (viscosity)
    # - boundary conditions
    if (compressible==True):
      log("info", "       selecting compressible for material fluids")
      state.LMaterialsFluid = LMaterialsFluidComp
      #state.field_state_name = "Density"
      state.LMaterialsViscosity = LMaterialsViscosityComp
      state.LMaterialsConductivity = LMaterialsConductivityComp
      log("info", "       selecting compressible boundary type ")
      state.LBoundariesMain = state.LBoundariesMain[:5]
      state.LBoundariesInlet= [
        {"text": "Total Conditions", "value": 2},
        {"text": "Mass flow", "value": 3},
        ]
      state.LBoundariesOutlet = [
        {"text": "Pressure outlet", "value": 0},
        ]

      
    else:
      log("info", "       selecting incompressible for material fluids")
      state.LMaterialsFluid = LMaterialsFluidIncomp
      #state.field_state_name = "Pressure"
      state.LMaterialsViscosity = LMaterialsViscosityIncomp
      state.LMaterialsConductivity = LMaterialsConductivityIncomp
      log("info", "       selecting incompressible boundary type ")
      
      state.LBoundariesMain+= [{"text": "Supersonic Inlet", "value": 5},{"text": "Supersonic Outlet", "value": 6}]
      state.LBoundariesInlet= [
        {"text": "Velocity inlet", "value": 0},
        {"text": "Pressure inlet", "value": 1},
        ]
      state.LBoundariesOutlet = [
        {"text": "Pressure outlet", "value": 0},
        {"text": "Target mass flow rate", "value": 1},
        ]

    # communicate to update all options when loading json config file
    state.dirty('LBoundariesMain')
    state.dirty('LBoundariesInlet')
    state.dirty('LMaterialsFluid')
    state.dirty('LMaterialsViscosity')
    state.dirty('LMaterialsConductivity')
    #state.dirty('field_state_name')s


###############################################################
# UI value update: turbulence model selection #
###############################################################
@state.change("physics_turb_idx")
def update_physics_turb(physics_turb_idx, **kwargs):
    log("info", f"     turbulence selection:  = {physics_turb_idx}")
    # if turbulence is selected, we also need to select a default turbulence model
    # if turbulence is deselected, we put turbulence model to "NONE"

    compressible = bool(state.physics_comp_idx)

    # physics_turb_idx=0 = Euler
    if (physics_turb_idx==0):
        if (compressible==True):
            state.jsonData['SOLVER']="EULER"
            state.jsonData['KIND_TURB_MODEL']="NONE"
        else:
            state.jsonData['SOLVER']="INC_EULER"
            state.jsonData['KIND_TURB_MODEL']="NONE"
            state.physics_energy_idx = 1
            state.dirty('physics_energy_idx')
    # 1 = laminar
    elif (physics_turb_idx==1):
        if (compressible==True):
            state.jsonData['SOLVER']="NAVIER_STOKES"
            state.jsonData['KIND_TURB_MODEL']="NONE"
        else:
            state.jsonData['SOLVER']="INC_NAVIER_STOKES"
            state.jsonData['KIND_TURB_MODEL']="NONE"
    # 2 = turbulent - SA
    elif (physics_turb_idx==2):
        if (compressible==True):
            state.jsonData['SOLVER']="RANS"
            state.jsonData['KIND_TURB_MODEL']="SA"
        else:
            state.jsonData['SOLVER']="INC_RANS"
            state.jsonData['KIND_TURB_MODEL']="SA"
    # 3 = turbulent - SST
    elif (physics_turb_idx==3):
        if (compressible==True):
            state.jsonData['SOLVER']="RANS"
            state.jsonData['KIND_TURB_MODEL']="SST"
        else:
            state.jsonData['SOLVER']="INC_RANS"
            state.jsonData['KIND_TURB_MODEL']="SST"

    if (physics_turb_idx == 2):
        log("info", "     SA turbulence model activated")
        if state.active_ui=="Physics":
          state.active_sub_ui = "subphysics_sa"
        state.submodeltext = "SA text"
    elif (physics_turb_idx == 3):
        log("info", "     SST turbulence model activated")
        if state.active_ui=="Physics":
          state.active_sub_ui = "subphysics_sst"
        state.submodeltext = "SST text"
    else:
        log("info", "     SST turbulence model deactivated")
        if state.active_ui=="Physics":
          state.active_sub_ui = "subphysics_none"
        state.submodeltext = "no model"    # energy equation can be deactivated only for inc_rans and inc_navier-stokes?
    solver = state.jsonData.get('SOLVER', 'NAVIER_STOKES').upper()
    log("info", f"solver =  = {solver}")
    if (solver=='INC_NAVIER_STOKES' or solver=='INC_RANS'):
      state.physics_energy_always_on = 0
    else:
      state.physics_energy_always_on = 1

    state.dirty('physics_energy_always_on')
    log("debug", f"Is energy always on?  = {state.physics_energy_always_on}")
    state.dirty('jsonData')



###############################################################
# PIPELINE SUBCARD : PHYSICS
###############################################################
# secondary card
def physics_subcard():
    # also visible when physics is selected

    # for the card to be visible, we have to set state.active_sub_ui = "subphysics_sst"
    with ui_subcard(title="SST submodels", sub_ui_name="subphysics_sst"):
        # Then a list selection for SST turbulence submodels
        vuetify.VSelect(
            # What to do when something is selected
            v_model=("physics_turb_sst_idx", 0),
            # The items in the list
            items=("representations_sst",LPhysicsTurbSSTOptions),
            # the name of the list box
            label="SST model",
            # ### disables the entire selection ###
            #disabled=("noSST",0),
            ### ### ### ### ### ### ### ### ### ###
            hide_details=True,
            dense=True,
            outlined=True,
            classes="pt-1 mt-1",
        )

    # for the card to be visible, we have to set state.active_sub_ui = "subphysics_sa"
    with ui_subcard(title="SA submodels", sub_ui_name="subphysics_sa"):
        # Then a list selection for SST turbulence submodels
        vuetify.VSelect(
            # What to do when something is selected
            v_model=("physics_turb_sa_idx", 0),
            # The items in the list
            items=("representations_sa",LPhysicsTurbSAOptions),
            # the name of the list box
            label="SA model",
            # ### disables the entire selection ###
            #disabled=("noSA",0),
            ### ### ### ### ### ### ### ### ### ###
            hide_details=True,
            dense=True,
            outlined=True,
            classes="pt-1 mt-1",
        )
        with vuetify.VCol(cols="6"):
            vuetify.VCheckbox(
                v_model=("physics_turb_sa_ft2_idx", False),
                label="ft2",
                classes="mt-1 pt-1",
                hide_details=True,
                dense=True,
            )
            vuetify.VCheckbox(
                v_model=("physics_turb_sa_qcr2000_idx", False),
                label="qcr2000",
                classes="mt-1 pt-1",
                hide_details=True,
                dense=True,
            )
            vuetify.VCheckbox(
                v_model=("physics_turb_sa_compressibility_idx", False),
                label="compressibility",
                classes="mt-1 pt-1",
                hide_details=True,
                dense=True,
            )
            vuetify.VCheckbox(
                v_model=("physics_turb_sa_rotation_idx", False),
                label="rotation",
                classes="mt-1 pt-1",
                hide_details=True,
                dense=True,
            )
            vuetify.VCheckbox(
                v_model=("physics_turb_sa_bcm_idx", False),
                label="BCM",
                classes="mt-1 pt-1",
                hide_details=True,
                dense=True,
            )

    # for the card to be visible, we have to set state.active_sub_ui = "subphysics_none"
    with ui_subcard(title="no submodels", sub_ui_name="subphysics_none"):
       vuetify.VTextarea(
                label="no submodels:",
                rows="5",
                v_model=("submodeltext", state.submodeltext),
        )
