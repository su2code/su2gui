# initialization gittree menu

# note that in the main menu, we need to call/add the following:
# 1) from ui.initialization import *
# 2) call initialization_card() in SinglePageWithDrawerLayout
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

# import the grid from the mesh module
from ui.mesh import *
from ui.vtk_helper import *

import vtk
from vtkmodules.vtkCommonDataModel import vtkDataObject

state, ctrl = server.state, server.controller

state.init_pressure = 0.0
state.init_density = 1.0
state.init_velx = 1.0
state.init_vely = 1.0
state.init_velz = 1.0
state.init_temperature = 1.0
state.init_momx = 1.0
state.init_momy = 1.0
state.init_momz = 1.0
state.init_energy = 1.0
state.init_nut = 1.0
state.init_tke = 1.0
state.init_dissipation = 1.0

############################################################################
# Initialization models - list options #
############################################################################

# option: use restart file or initialize
# when a restart file is loaded, we automatically use it unless we overwrite it in the
# initial setup
# the solver cannot start unless we define an initial solution somehow


# option: initialization pull-down: {from file, uniform}
# option: patch: {cube, cylinder, sphere}
#         selection of variables{U,V,etc} + constant value


############################################################################
# Initialization models - list options #
############################################################################

# List: initialization model: options
# patch is enabled when uniform or restart has been used
state.LInitializationOption= [
  {"text": "Uniform", "value": 0},
  {"text": "From file (Restart)", "value": 1},
  {"text": "Patch", "value": 2},
]

LInitializationPatch= [
  {"text": "Plane", "value": 0},
  {"text": "Box", "value": 1},
  {"text": "Sphere", "value": 2},
]

LZones = [
  {"text": "Zone 1", "value": 0},
  {"text": "Zone 2", "value": 1},
]

PatchZoneDict = [
  {'zone':0, 'density':1.2, 'momentum':[1,1,1], 'energy': 1, 'nu_tidle':1.2, 'dissipation':100, 'temperature':300, 'velocity':[1,1,1], 'tke':1.2, 'pressure': 1},
  {'zone':1, 'density':1.2, 'momentum':[1,1,1], 'energy': 1, 'nu_tidle':1.2, 'dissipation':100, 'temperature':300, 'velocity':[1,1,1], 'tke':1.2, 'pressure': 1},
]

# set the state variables using the json configuration file data
def set_json_initialization():
  state.initial_option_idx = 0
  if 'RESTART_SOL' in state.jsonData and state.jsonData['RESTART_SOL']==True:
    log("info", "restarting solution from file")
    state.initial_option_idx = 1
  else:
    # note that we always restart from file, but in this case we create the file from uniform conditions
    log("info", "restarting from uniform initial conditions")
    state.initial_option_idx = 0
  state.dirty('initial_option_idx')

  if 'SOLVER' in state.jsonData and ("INC" in str(state.jsonData['SOLVER'])):
    compressible = False
  else:
    compressible = True

  # if incompressible, we check if temperature is on
  energy = False
  if (compressible == False):
    if 'INC_ENERGY_EQUATION' in state.jsonData and ('INC_ENERGY_EQUATION' in state.jsonData and state.jsonData['INC_ENERGY_EQUATION']==True):
       energy = True

  if (compressible==True):
    state.init_momx = 1.0
  elif 'INC_VELOCITY_INIT' in state.jsonData:
    state.init_velx = state.jsonData['INC_VELOCITY_INIT'][0]
    state.init_vely = state.jsonData['INC_VELOCITY_INIT'][1]
    state.init_velz = state.jsonData['INC_VELOCITY_INIT'][2]
    if 'INC_TEMPERATURE_INIT' in state.jsonData and (energy==True):
      state.init_temperature = state.jsonData['INC_TEMPERATURE_INIT']

###############################################################
# PIPELINE CARD : Initialization
###############################################################
def initialization_card():
    with ui_card(title="Initialization", ui_name="Initialization"):
      log("info", "def initialization_card ")
      with vuetify.VContainer(fluid=True):

         # 1 row of option lists
        with vuetify.VRow(classes="pt-2"):
          with vuetify.VCol(cols="10"):

            # Then a list selection for initialization submodels
            vuetify.VSelect(
                # What to do when something is selected
                v_model=("initial_option_idx", 0),
                # The items in the list
                #items=("representations_initial",state.LInitializationOption),
                items=("Object.values(LInitializationOption)",),
                # the name of the list box
                label="Initialize from:",
                hide_details=True,
                dense=True,
                outlined=True,
                classes="pt-1 mt-1",
            )


    # update the initial option to recompute based on upstream changes
    # this makes sure that the incompressible vs compressible subui
    # is changed when comp/incomp is changed in the physics solver

###############################################################
# Initialize - method
###############################################################
@state.change("initialization_state_idx")
def update_initial_option(initialization_state_idx, **kwargs):
    log("info", f"initialization state selection:  = {state.initialization_state_idx}")
    # but for compressible or incompressible?


@state.change("initial_option_idx")
def update_initial_option(initial_option_idx, **kwargs):
    log("info", f"initialization selection:  = {state.initial_option_idx}")
    log("info", f"restart_sol= {bool (state.initial_option_idx)}")

    # option=0 : uniform values
    # option=1 : restart from file
    # option=2 : patch
    if (state.initial_option_idx==0):
      # uniform (constant) initialization
      log("info", f"state.jsonData solve =  = {state.jsonData['SOLVER']}")
      if "INC" in (state.jsonData["SOLVER"]):
        log("info", "initialization for incompressible")
        if state.active_ui=="Initialization":
          state.active_sub_ui = "subinitialization_inc"
      else:
        log("info", "initialization for compressible")
        if state.active_ui=="Initialization":
          state.active_sub_ui = "subinitialization_comp"
    elif (state.initial_option_idx==1):
      log("info", "initialization from file")
      if state.active_ui=="Initialization":
        state.active_sub_ui = "subinitialization_file"
    else:
      # patch
      if state.active_ui=="Initialization":
        state.active_sub_ui = "subinitialization_patch"


@state.change("initial_patch_idx")
def update_initial_patch(initial_patch_idx, **kwargs):
    log("info", f"patch selection:  = {initial_patch_idx}")



#@state.change("initialize")
def initialize_uniform():

  log("info", "initialize solution")

  # construct the dataset_arrays
  datasetArrays = []
  counter=0

  FieldNames=[]
  FieldValues=[]
  if ("INC" in str(state.jsonData['SOLVER'])):
    compressible = False
  else:
    compressible = True

  # if incompressible, we check if temperature is on
  energy = False
  if (compressible == False):
    if ('INC_ENERGY_EQUATION' in state.jsonData and state.jsonData['INC_ENERGY_EQUATION']==True):
       energy = True

  if (compressible==True):
    log("info", "compressible")
    FieldNames.extend(["Density","Momentum_x","Momentum_y"])
    FieldValues.extend([state.init_density,state.init_momx,state.init_momy])
    if state.nDim==3:
        FieldNames.append("Momentum_z")
        FieldValues.append(state.init_momz)
    FieldNames.append("Energy")
    FieldValues.append(state.init_energy)
  else:
    log("info", "incompressible")
    log("info", f"pressure: = {state.init_pressure}")
    log("info", f"velocity: = {state.init_velx} {state.init_vely}")
    FieldNames.extend(["Pressure","Velocity_x","Velocity_y"])
    FieldValues.extend([state.init_pressure,state.init_velx,state.init_vely])
    if state.nDim==3:
        FieldNames.append("Velocity_z")
        FieldValues.append(state.init_velz)
    if energy==True:
      FieldNames.append("Temperature")
      FieldValues.append(state.init_temperature)

  turbmodelSA = False
  turbmodelSST = False
  turbulence = False
  if ("RANS" in str(state.jsonData['SOLVER'])):
    turbulence = True
    if state.jsonData['KIND_TURB_MODEL'] == "SA":
      turbmodelSA=True
    elif state.jsonData['KIND_TURB_MODEL'] == "SST":
      turbmodelSST = True

  if (turbmodelSA == True):
    FieldNames.append("Nu_Tilde")
    FieldValues.append(state.init_nut)
  elif (turbmodelSST == True):
    FieldNames.extend(["Tke","Dissipation"])
    FieldValues.extend([state.init_tke,state.init_dissipation])

  log("info", f"fieldnames= = {FieldNames}")

  nPoints = grid.GetPoints().GetNumberOfPoints()
  log("info", f"number of points =  = {nPoints}")


  for i in range(len(FieldNames)):
    name = FieldNames[i]
    try:
      value = float(FieldValues[i])
    except Exception as e:
      log("error", f"error in setting value for {name} in Initialization:  \n {e}")

    ArrayObject = vtk.vtkFloatArray()
    ArrayObject.SetName(name)
    # all components are scalars, no vectors for velocity
    ArrayObject.SetNumberOfComponents(1)
    # how many elements do we have?
    ArrayObject.SetNumberOfValues(nPoints)
    ArrayObject.SetNumberOfTuples(nPoints)

    log("info", f"name = {name} , value = {value}")

    # Nijso: TODO FIXME reported to be a slow process.
    for i in range(nPoints):
      ArrayObject.SetValue(i, value)

    grid.GetPointData().AddArray(ArrayObject)

    # note that range is equal because value is uniform
    datasetArrays.append(
            {
                "text": name,
                "value": counter,
                "range": [float(value),float(value)],
                "type": vtkDataObject.FIELD_ASSOCIATION_POINTS,
            }
    )
    counter += 1


  # we should now have the scalars available...
  defaultArray = datasetArrays[0]
  state.dataset_arrays = datasetArrays
  #log("info", f"dataset =  = {datasetArrays}")
  #log("info", f"dataset_0 =  = {datasetArrays[0]}")
  #log("info", f"dataset_0 =  = {datasetArrays[0].get('text'}"))

  mesh_mapper.SetInputData(grid)
  mesh_actor.SetMapper(mesh_mapper)
  renderer.AddActor(mesh_actor)

  mesh_mapper.SelectColorArray(defaultArray.get('text'))
  mesh_mapper.GetLookupTable().SetRange(defaultArray.get('range'))
  mesh_mapper.SetScalarVisibility(True)
  mesh_mapper.SetUseLookupTableScalarRange(True)

  # Mesh: Setup default representation to surface
  mesh_actor.GetProperty().SetRepresentationToSurface()
  mesh_actor.GetProperty().SetPointSize(1)
  #do not show the edges
  mesh_actor.GetProperty().EdgeVisibilityOff()

  # We have loaded a mesh, so enable the exporting of files
  state.export_disabled = False

  renderer.ResetCamera()
  ctrl.view_update()

  # save the restart file (should be a separate save/export button)
  # this routine should be in su2_io.py
  # note that we save the file in the solution file, and we always start from
  # the saved file
  if 'SOLUTION_FILENAME' not in state.jsonData:
    state.jsonData['SOLUTION_FILENAME'] = "solution_flow.csv"
  solution_filename = state.jsonData['SOLUTION_FILENAME']
  if not solution_filename.endswith('.csv'):
      solution_filename += '.csv'

  
  with open(BASE / "user" / state.case_name / solution_filename,'w') as f:
    fields = ["PointID","x","y"]
    if (state.nDim==3):
        fields.append("z")
    fields.extend(FieldNames)
    # convert to string, including double quotes
    stringfields = ', '.join(f'"{name}"' for name in fields) +"\n"
    f.write(stringfields)
    #log("info", grid.GetPointData().GetNumberOfArrays())
    #log("info", grid.GetPointData().GetArrayName(i))
    # now loop over points and get the coordinates

    # loop over all points
    for p in range(nPoints):
        # loop over all field names to be saved
        coord = grid.GetPoint(p)
        datalist = str(p) + "," + str(coord[0]) + "," + str(coord[1])
        if state.nDim==3:
            datalist = datalist + "," + str(coord[2])
        for name in FieldNames:
            datapoint =  grid.GetPointData().GetArray(name).GetValue(p)
            datalist = datalist + "," + str(datapoint)
        datalist = datalist+"\n"
        f.write(datalist)
        #log("info", p, " ",grid.GetPoint(p))
  f.close()
  state.jsonData['RESTART_SOL'] = True
  state.jsonData['READ_BINARY_RESTART'] = False
  


def initialize_patch():

  # construct the dataset_arrays
  datasetArrays = []
  counter=0

  FieldNames=[]
  FieldValues1=[]
  FieldValues2=[]
  if ("INC" in str(state.jsonData['SOLVER'])):
    compressible = False
  else:
    compressible = True

  # if incompressible, we check if temperature is on
  energy = False
  if (compressible == False):
    if ('INC_ENERGY_EQUATION' in state.jsonData and state.jsonData['INC_ENERGY_EQUATION']==True):
       energy = True

  if (compressible==True):
    log("info", "compressible")
    FieldNames.extend(["Density","Momentum_x","Momentum_y"])
    FieldValues1.extend([PatchZoneDict[0]['density'],PatchZoneDict[0]['momentum'][0], PatchZoneDict[0]['momentum'][1]])
    FieldValues2.extend([PatchZoneDict[1]['density'],PatchZoneDict[1]['momentum'][0], PatchZoneDict[1]['momentum'][1]])
    if state.nDim==3:
        FieldNames.append("Momentum_z")
        FieldValues1.append(PatchZoneDict[0]['momentum'][2])
        FieldValues2.append(PatchZoneDict[1]['momentum'][2])
    FieldNames.append("Energy")
    FieldValues1.append(PatchZoneDict[0]['energy'])
    FieldValues2.append(PatchZoneDict[1]['energy'])
  else:
    log("info", "incompressible")
    log("info", f"pressure: = {state.init_pressure}")
    log("info", f"velocity: = {state.init_velx} {state.init_vely}")
    FieldNames.extend(["Pressure","Velocity_x","Velocity_y"])
    FieldValues1.extend([PatchZoneDict[0]['pressure'],PatchZoneDict[0]['velocity'][0], PatchZoneDict[0]['velocity'][1]])
    FieldValues2.extend([PatchZoneDict[1]['pressure'],PatchZoneDict[1]['velocity'][0], PatchZoneDict[1]['velocity'][1]])

    if state.nDim==3:
        FieldNames.append("Velocity_z")
        FieldValues1.append(PatchZoneDict[0]['velocity'][2])
        FieldValues2.append(PatchZoneDict[1]['velocity'][2])
    if energy==True:
      FieldNames.append("Temperature")
      FieldValues1.append(PatchZoneDict[0]['temperature'])
      FieldValues2.append(PatchZoneDict[1]['temperature'])

  turbmodelSA = False
  turbmodelSST = False
  turbulence = False
  if ("RANS" in str(state.jsonData['SOLVER'])):
    turbulence = True
    if state.jsonData['KIND_TURB_MODEL'] == "SA":
      turbmodelSA=True
    elif state.jsonData['KIND_TURB_MODEL'] == "SST":
      turbmodelSST = True

  if (turbmodelSA == True):
    FieldNames.append("Nu_Tilde")
    FieldValues1.append(PatchZoneDict[0]['nu_tidle'])
    FieldValues2.append(PatchZoneDict[1]['nu_tidle'])
  elif (turbmodelSST == True):
    FieldNames.extend(["Tke","Dissipation"])
    FieldValues1.extend([PatchZoneDict[0]['tke'], PatchZoneDict[0]['dissipation']])
    FieldValues2.extend([PatchZoneDict[1]['tke'], PatchZoneDict[1]['dissipation']])

  log("info", f"fieldnames= = {FieldNames}")

  nPoints = grid.GetPoints().GetNumberOfPoints()
  log("info", f"number of points =  = {nPoints}")

  shape = None
    
  if state.initial_patch_idx == 0:
      try:
          origin = (float(state.plane_point_x), float(state.plane_point_y), float(state.plane_point_z))
          normal = (float(state.plane_vector_x), float(state.plane_vector_y), float(state.plane_vector_z))
      except Exception as e:
          log("error", f"Error in setting plane origin and normal:  \n {e}")
          return

      shape = vtk.vtkPlaneSource()
      shape.SetOrigin(origin)
      shape.SetNormal(normal)

  elif state.initial_patch_idx == 1:
      try:
        origin = (float(state.box_origin_x), float(state.box_origin_y), float(state.box_origin_z))
        dimensions = (float(state.box_len_x), float(state.box_len_y) ,float(state.box_len_z))
      except Exception as e:
          log("error", f"Error in setting box origin and dimensions:  \n {e}")  
          return
      
      shape = vtk.vtkCubeSource()
      shape.SetXLength(dimensions[0])
      shape.SetYLength(dimensions[1])
      shape.SetZLength(dimensions[2])
      shape.SetCenter(origin)
      
  elif state.initial_patch_idx == 2:
      try:
        origin = (float(state.sphere_origin_x), float(state.sphere_origin_y), float(state.sphere_origin_z))
        dimensions = (float(state.sphere_radius),)
      except Exception as e:
          log("error", f"Error in setting sphere origin and radius:  \n {e}")
          return

      shape = vtk.vtkSphereSource()
      shape.SetCenter(origin)
      shape.SetRadius(float(state.sphere_radius))

  if shape:
      shape.Update()

      datasetArrays = []
      counter = 0

      for i in range(len(FieldNames)):
          name = FieldNames[i]
          try:
              val1 = float(FieldValues1[i])
              val2 = float(FieldValues2[i])
          except Exception as e:
              log("error", f"Error in setting value for {name} in Initialization:  \n {e}")
              return

          ArrayObject = vtk.vtkFloatArray()
          ArrayObject.SetName(name)
          ArrayObject.SetNumberOfComponents(1)
          ArrayObject.SetNumberOfTuples(nPoints)

          for j in range(nPoints):
              p = grid.GetPoint(j)
              if state.initial_patch_idx == 0:
                  side = vtk.vtkPlane.Evaluate(normal, origin, p) >= 0

              elif state.initial_patch_idx == 1:
                  side = (origin[0] <= p[0] <= origin[0] + dimensions[0] and
                          origin[1] <= p[1] <= origin[1] + dimensions[1] and
                          origin[2] <= p[2] <= origin[2] + dimensions[2])
                  
              elif state.initial_patch_idx == 2:
                  side = vtk.vtkMath.Distance2BetweenPoints(origin, p) <= (dimensions[0] ** 2)
              
              ArrayObject.SetValue(j, val1 if side else val2)

          grid.GetPointData().AddArray(ArrayObject)
          datasetArrays.append(
              {
                  "text": name,
                  "value": counter,
                  "range": [min(val1, val2), max(val1, val2)],
                  "type": vtk.vtkDataObject.FIELD_ASSOCIATION_POINTS,
              }
          )
          counter += 1

      # Assuming mesh_mapper, mesh_actor, renderer, and ctrl are defined elsewhere
      defaultArray = datasetArrays[0]
      state.dataset_arrays = datasetArrays

      mesh_mapper.SetInputData(grid)
      mesh_actor.SetMapper(mesh_mapper)
      renderer.AddActor(mesh_actor)

      mesh_mapper.SelectColorArray(defaultArray.get('text'))
      mesh_mapper.GetLookupTable().SetRange(defaultArray.get('range'))
      mesh_mapper.SetScalarVisibility(True)
      mesh_mapper.SetUseLookupTableScalarRange(True)

      mesh_actor.GetProperty().SetRepresentationToSurface()
      mesh_actor.GetProperty().SetPointSize(1)
      mesh_actor.GetProperty().EdgeVisibilityOff()

      state.export_disabled = False

      renderer.ResetCamera()
      ctrl.view_update()


  # save the restart file (should be a separate save/export button)
  # this routine should be in su2_io.py
  # note that we save the file in the solution file, and we always start from
  # the saved file
  if 'SOLUTION_FILENAME' not in state.jsonData:
    state.jsonData['SOLUTION_FILENAME'] = "solution_flow.csv"
  solution_filename = state.jsonData['SOLUTION_FILENAME']
  if not solution_filename.endswith('.csv'):
      solution_filename += '.csv'

  with open(BASE / "user" / state.case_name / solution_filename,'w') as f:
    fields = ["PointID","x","y"]
    if (state.nDim==3):
        fields.append("z")
    fields.extend(FieldNames)
    # convert to string, including double quotes
    stringfields = ', '.join(f'"{name}"' for name in fields) +"\n"
    f.write(stringfields)
    #log("info", grid.GetPointData().GetNumberOfArrays())
    #log("info", grid.GetPointData().GetArrayName(i))
    # now loop over points and get the coordinates

    # loop over all points
    for p in range(nPoints):
        # loop over all field names to be saved
        coord = grid.GetPoint(p)
        datalist = str(p) + "," + str(coord[0]) + "," + str(coord[1])
        if state.nDim==3:
            datalist = datalist + "," + str(coord[2])
        for name in FieldNames:
            datapoint =  grid.GetPointData().GetArray(name).GetValue(p)
            datalist = datalist + "," + str(datapoint)
        datalist = datalist+"\n"
        f.write(datalist)
        #log("info", p, " ",grid.GetPoint(p))
  f.close()
  
  state.jsonData['RESTART_SOL'] = True
  state.jsonData['READ_BINARY_RESTART'] = False

def initialization_patch_subcard():
  log("info", "initialization_file_subcard:: set the ui_subcard")
  with ui_subcard(title="Patch Initialization", sub_ui_name="subinitialization_patch"):
    with vuetify.VContainer(fluid=True):
      # ####################################################### #
      with vuetify.VRow(classes="py-0 my-0"):
        with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
            vuetify.VSelect(
                # What to do when something is selected
                v_model=("initial_patch_idx", 0),
                # The items in the list
                items=("representations_init_patch",LInitializationPatch),
                # the name of the list box
                label="Patch:",
                hide_details=True,
                dense=True,
                outlined=True,
                classes="pt-1 mt-1",
                #disabled = True,
            )

      # plane
      with vuetify.VContainer( v_if= "initial_patch_idx==0"):
        
        # Co-ordinates of point
        with vuetify.VRow(classes="py-0 my-0"):
          with vuetify.VCol(cols="3", classes="py-1 px-0"):
            vuetify.VTextField(
                v_model=("plane_point_x", 0),
                label="Point X",
              )
          with vuetify.VCol(cols="3", classes="py-1 px-0"):
            vuetify.VTextField(
                v_model=("plane_point_y", 0),
                label="Point Y",
              )
          with vuetify.VCol(cols="3", classes="py-1 px-0", v_if=("nDim==3")):
            vuetify.VTextField(
                v_model=("plane_point_z", 0),
                label="Point Z",
              )
            
        # plane vector
        with vuetify.VRow(classes="py-0 my-0"):
          with vuetify.VCol(cols="3", classes="py-1 px-0"):
            vuetify.VTextField(
                v_model=("plane_vector_x", 1),
                label="Vector X",
              )
          with vuetify.VCol(cols="3", classes="py-1 px-0"):
            vuetify.VTextField(
                v_model=("plane_vector_y", 0),
                label="Vector Y",
              )
          with vuetify.VCol(cols="3", classes="py-1 px-0", v_if=("nDim==3")):
            vuetify.VTextField(
                v_model=("plane_vector_z", 0),
                label="Vector Z",
                
              )
            


      # box
      with vuetify.VContainer( v_if= "initial_patch_idx==1"):
        # Co-ordinates of origin
        with vuetify.VRow(classes="py-0 my-0"):
          with vuetify.VCol(cols="3", classes="py-1 px-0"):
            vuetify.VTextField(
                v_model=("box_origin_x", 0),
                label="Origin X",
              )
          with vuetify.VCol(cols="3", classes="py-1 px-0"):
            vuetify.VTextField(
                v_model=("box_origin_y", 0),
                label="Origin Y",
              )
          with vuetify.VCol(cols="3", classes="py-1 px-0", v_if=("nDim==3")):
            vuetify.VTextField(
                v_model=("box_origin_z", 0),
                label="Origin Z",
                
              )
            
        # Box dimensions
        with vuetify.VRow(classes="py-0 my-0"):
          with vuetify.VCol(cols="3", classes="py-1 px-0"):
            vuetify.VTextField(
                v_model=("box_len_x", 0),
                label="Length X",
              )
          with vuetify.VCol(cols="3", classes="py-1 px-0"):
            vuetify.VTextField(
                v_model=("box_len_y", 0),
                label="Length Y",
              )
          with vuetify.VCol(cols="3", classes="py-1 px-0", v_if=("nDim==3")):
            vuetify.VTextField(
                v_model=("box_len_z", 0),
                label="Length Z",
              )

      # sphere
      with vuetify.VContainer( v_if= "initial_patch_idx==2"):
        # Co-ordinates of origin
        with vuetify.VRow(classes="py-0 my-0"):
          with vuetify.VCol(cols="3", classes="py-1 px-0"):
            vuetify.VTextField(
                v_model=("sphere_origin_x", 0),
                label="Origin X",
              )
          with vuetify.VCol(cols="3", classes="py-1 px-0"):
            vuetify.VTextField(
                v_model=("sphere_origin_y", 0),
                label="Origin Y",
              )
          with vuetify.VCol(cols="3", classes="py-1 px-0", v_if=("nDim==3")):
            vuetify.VTextField(
                v_model=("sphere_origin_z", 0),
                label="Origin Z",
                
              )
            
        # Box dimensions
        with vuetify.VCol(cols="4", classes="py-1 px-0"):
          vuetify.VTextField(
              v_model=("sphere_radius", 0),
              label="Radius",
            )

      # Option to select the zone
      vuetify.VSelect(
              # What to do when something is selected
              v_model=("zone_idx", 0),
              # The items in the list
              items=("LZones", LZones[:2]),
              # the name of the list box
              label="Zone:",
              hide_details=True,
              dense=True,
              outlined=True,
              classes="pt-1 mt-1",
          )

      initialization_patch_property_subcard()


def initialization_patch_property_subcard():

      with vuetify.VContainer(fluid=True, v_if = "physics_comp_idx==0"):
          with vuetify.VContainer(fluid=True):
            # ####################################################### #
            with vuetify.VRow(classes="py-0 my-0"):
              with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
                vuetify.VTextField(
                  # What to do when something is selected
                  v_model=("init_patch_pressure", 1.0),
                  # the name of the list box
                  label="pressure",
                )
                vuetify.VTextField(
                  # What to do when something is selected
                  v_model=("init_patch_velx", 1.0),
                  # the name of the list box
                  label="Velocity X",
                )
                vuetify.VTextField(
                  # What to do when something is selected
                  v_model=("init_patch_vely", 1.0),
                  # the name of the list box
                  label="Velocity_Y",
                )
          with vuetify.VContainer(fluid=True, v_if=("nDim==3")):
            # ####################################################### #
            with vuetify.VRow(classes="py-0 my-0"):
              with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
                vuetify.VTextField(
                  # What to do when something is selected
                  v_model=("init_patch_velz", 1.0),
                  # the name of the list box
                  label="Velocity_Z",
                  #disabled=("nDim==2",0)
                )
          with vuetify.VContainer(fluid=True, v_if=("jsonData['INC_ENERGY_EQUATION']==1")):
            # ####################################################### #
            with vuetify.VRow(classes="py-0 my-0"):
              with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
                vuetify.VTextField(
                  # What to do when something is selected
                  v_model=("init_patch_temperature", 300.0),
                  # the name of the list box
                  label="temperature",
                  # is temperature disabled?
                  #disabled= ("jsonData['INC_ENERGY_EQUATION']==0",0)
                )
          # turbulence quantities (nijso TODO: add turbulence intensity and turb ratio and computed results for k,w)
          with vuetify.VContainer(fluid=True, v_if=("jsonData['KIND_TURB_MODEL']=='SA' ")):
            # ####################################################### #
            with vuetify.VRow(classes="py-0 my-0"):
              with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
                vuetify.VTextField(
                  # What to do when something is selected
                  v_model=("init_patch_nu_tilde_idx", 1.2),
                  # the name of the list box
                  label="nu_tilde",
                )
          # turbulence quantities
          with vuetify.VContainer(fluid=True, v_if=("jsonData['KIND_TURB_MODEL']=='SST' ")):
            # ####################################################### #
            with vuetify.VRow(classes="py-0 my-0"):
              with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
                vuetify.VTextField(
                  # What to do when something is selected
                  v_model=("init_patch_sst_k_idx", 1.2),
                  # the name of the list box
                  label="tke",
                )
            with vuetify.VRow(classes="py-0 my-0"):
              with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
                vuetify.VTextField(
                  # What to do when something is selected
                  v_model=("init_patch_sst_w_idx", 100),
                  # the name of the list box
                  label="dissipation",
                )

          with vuetify.VContainer(fluid=True):
            # ####################################################### #
            with vuetify.VRow(classes="py-0 my-0"):
              with vuetify.VCol(cols="12"):
                with vuetify.VBtn("Initialize",click=initialize_patch):
                  vuetify.VIcon("{{solver_icon}}",color="purple")



      with vuetify.VContainer(fluid=True, v_if = "physics_comp_idx==1"):
            # ####################################################### #
            with vuetify.VRow(classes="py-0 my-0"):
              with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
                vuetify.VTextField(
                  # What to do when something is selected
                  v_model=("init_patch_density", 1.2),
                  # the name of the list box
                  label="density",
                )
                vuetify.VTextField(
                  # What to do when something is selected
                  v_model=("init_patch_momx", 1.0),
                  # the name of the list box
                  label="Momentum X",
                )
                vuetify.VTextField(
                  # What to do when something is selected
                  v_model=("init_patch_momy", 1.0),
                  # the name of the list box
                  label="Momentum Y",
                )

              # ####################################################### #
            with vuetify.VRow(classes="py-0 my-0", v_if=("nDim==3")):
              with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
                vuetify.VTextField(
                  # What to do when something is selected
                  v_model=("init_patch_momz", 1.0),
                  # the name of the list box
                  label="Momentum Z",
                )

            with vuetify.VContainer(fluid=True):
              # ####################################################### #
              with vuetify.VRow(classes="py-0 my-0"):
                with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
                  vuetify.VTextField(
                    # What to do when something is selected
                    v_model=("init_patch_energy", 1.0),
                    # the name of the list box
                    label="energy",
                  )

            # turbulence quantities (nijso TODO: add turbulence intensity and turb ratio and computed results for k,w)
            with vuetify.VContainer(fluid=True, v_if=("jsonData['KIND_TURB_MODEL']=='SA' ")):
              # ####################################################### #
              with vuetify.VRow(classes="py-0 my-0"):
                with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
                  vuetify.VTextField(
                    # What to do when something is selected
                    v_model=("init_patch_nu_tilde_idx", 1.2),
                    # the name of the list box
                    label="nu_tilde",
                  )
            # turbulence quantities
            with vuetify.VContainer(fluid=True, v_if=("jsonData['KIND_TURB_MODEL']=='SST' ")):
              # ####################################################### #
              with vuetify.VRow(classes="py-0 my-0"):
                with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
                  vuetify.VTextField(
                    # What to do when something is selected
                    v_model=("init_patch_sst_k_idx", 1.2),
                    # the name of the list box
                    label="tke",
                  )
              with vuetify.VRow(classes="py-0 my-0"):
                with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
                  vuetify.VTextField(
                    # What to do when something is selected
                    v_model=("init_patch_sst_w_idx", 100),
                    # the name of the list box
                    label="dissipation",
                  )

            with vuetify.VContainer(fluid=True):
              # ####################################################### #
              with vuetify.VRow(classes="py-0 my-0"):
                with vuetify.VCol(cols="12"):
                  with vuetify.VBtn("Initialize",click=initialize_patch):
                    vuetify.VIcon("{{solver_icon}}",color="purple")


def initialization_file_subcard():
  log("info", "initialization_file_subcard:: set the ui_subcard")
  with ui_subcard(title="initialization from file", sub_ui_name="subinitialization_file"):
    with vuetify.VContainer(fluid=True):
      # ####################################################### #
      with vuetify.VRow(classes="py-0 my-0"):
        with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):    # restart file input inside the toolbar
          # note that this should be moved elsewhere
          vuetify.VFileInput(
            # single file only
            multiple=False,
            background_color="white",
            # the icon in front of the file input
            prepend_icon="mdi-file",
            show_size=True,
            small_chips=True,
            truncate_length=25,
            v_model=("restartFile", None),
            label="Load Restart File",
            dense=True,
            hide_details=True,
            style="max-width: 300px;",
            accept=".dat, .csv",
            __properties=["accept"],
          )


###############################################################
# PIPELINE SUBCARD : INITIALIZATION
###############################################################
# secondary card
def initialization_uniform_subcard():

    log("info", "initialization_uniform_subcard:: set the ui_subcard")
    #with vuetify.VContainer(fluid=True):
    # 1 row of option lists
    energy = bool(state.jsonData['INC_ENERGY_EQUATION'])
    log("info", f"energy equation= = {energy}")
    # for the card to be visible, we have to set state.active_sub_ui = subinitialization_inc
    with ui_subcard(title="initialization (incompressible)", sub_ui_name="subinitialization_inc"):
      with vuetify.VContainer(fluid=True):
        # ####################################################### #
        with vuetify.VRow(classes="py-0 my-0"):
          with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
            vuetify.VTextField(
              # What to do when something is selected
              v_model=("init_pressure", 1.0),
              # the name of the list box
              label="pressure",
            )
            vuetify.VTextField(
              # What to do when something is selected
              v_model=("init_velx", 1.0),
              # the name of the list box
              label="Velocity X",
            )
            vuetify.VTextField(
              # What to do when something is selected
              v_model=("init_vely", 1.0),
              # the name of the list box
              label="Velocity_Y",
            )
      with vuetify.VContainer(fluid=True, v_if=("nDim==3")):
        # ####################################################### #
        with vuetify.VRow(classes="py-0 my-0"):
          with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
            vuetify.VTextField(
              # What to do when something is selected
              v_model=("init_velz", 1.0),
              # the name of the list box
              label="Velocity_Z",
              #disabled=("nDim==2",0)
            )
      with vuetify.VContainer(fluid=True, v_if=("jsonData['INC_ENERGY_EQUATION']==1")):
        # ####################################################### #
        with vuetify.VRow(classes="py-0 my-0"):
          with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
            vuetify.VTextField(
              # What to do when something is selected
              v_model=("init_temperature", 300.0),
              # the name of the list box
              label="temperature",
              # is temperature disabled?
              #disabled= ("jsonData['INC_ENERGY_EQUATION']==0",0)
            )
      # turbulence quantities (nijso TODO: add turbulence intensity and turb ratio and computed results for k,w)
      with vuetify.VContainer(fluid=True, v_if=("jsonData['KIND_TURB_MODEL']=='SA' ")):
        # ####################################################### #
        with vuetify.VRow(classes="py-0 my-0"):
          with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
            vuetify.VTextField(
              # What to do when something is selected
              v_model=("init_nu_tilde_idx", 1.2),
              # the name of the list box
              label="nu_tilde",
            )
      # turbulence quantities
      with vuetify.VContainer(fluid=True, v_if=("jsonData['KIND_TURB_MODEL']=='SST' ")):
        # ####################################################### #
        with vuetify.VRow(classes="py-0 my-0"):
          with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
            vuetify.VTextField(
              # What to do when something is selected
              v_model=("init_sst_k_idx", 1.2),
              # the name of the list box
              label="tke",
            )
        with vuetify.VRow(classes="py-0 my-0"):
          with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
            vuetify.VTextField(
              # What to do when something is selected
              v_model=("init_sst_w_idx", 100),
              # the name of the list box
              label="dissipation",
            )

      with vuetify.VContainer(fluid=True):
        # ####################################################### #
        with vuetify.VRow(classes="py-0 my-0"):
          with vuetify.VCol(cols="12"):
            with vuetify.VBtn("Initialize",click=initialize_uniform):
              vuetify.VIcon("{{solver_icon}}",color="purple")

    # use a vcontainer if you want to have a border around everything
    #with vuetify.VContainer(fluid=True):
    # 1 row of option lists
    # for the card to be visible, we have to set state.active_sub_ui = subinitialization
    with ui_subcard(title="initialization (compressible)", sub_ui_name="subinitialization_comp"):
      with vuetify.VContainer(fluid=True):
        # ####################################################### #
        with vuetify.VRow(classes="py-0 my-0"):
          with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
            vuetify.VTextField(
              # What to do when something is selected
              v_model=("init_density", 1.2),
              # the name of the list box
              label="density",
            )
            vuetify.VTextField(
              # What to do when something is selected
              v_model=("init_momx", 1.0),
              # the name of the list box
              label="Momentum X",
            )
            vuetify.VTextField(
              # What to do when something is selected
              v_model=("init_momy", 1.0),
              # the name of the list box
              label="Momentum Y",
            )

      with vuetify.VContainer(fluid=True, v_if=("nDim==3")):
        # ####################################################### #
        with vuetify.VRow(classes="py-0 my-0"):
          with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
            vuetify.VTextField(
              # What to do when something is selected
              v_model=("init_momz", 1.0),
              # the name of the list box
              label="Momentum Z",
            )

      with vuetify.VContainer(fluid=True):
        # ####################################################### #
        with vuetify.VRow(classes="py-0 my-0"):
          with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
            vuetify.VTextField(
              # What to do when something is selected
              v_model=("init_energy", 1.0),
              # the name of the list box
              label="energy",
            )

          # turbulence quantities (nijso TODO: add turbulence intensity and turb ratio and computed results for k,w)
          with vuetify.VContainer(fluid=True, v_if=("jsonData['KIND_TURB_MODEL']=='SA' ")):
            # ####################################################### #
            with vuetify.VRow(classes="py-0 my-0"):
              with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
                vuetify.VTextField(
                  # What to do when something is selected
                  v_model=("init_nu_tilde_idx", 1.2),
                  # the name of the list box
                  label="nu_tilde",
                )
          # turbulence quantities
          with vuetify.VContainer(fluid=True, v_if=("jsonData['KIND_TURB_MODEL']=='SST' ")):
            # ####################################################### #
            with vuetify.VRow(classes="py-0 my-0"):
              with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
                vuetify.VTextField(
                  # What to do when something is selected
                  v_model=("init_sst_k_idx", 1.2),
                  # the name of the list box
                  label="tke",
                )
            with vuetify.VRow(classes="py-0 my-0"):
              with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
                vuetify.VTextField(
                  # What to do when something is selected
                  v_model=("init_sst_w_idx", 100),
                  # the name of the list box
                  label="dissipation",
                )

          with vuetify.VContainer(fluid=True):
            # ####################################################### #
            with vuetify.VRow(classes="py-0 my-0"):
              with vuetify.VCol(cols="12"):
                with vuetify.VBtn("Initialize",click=initialize_uniform):
                  vuetify.VIcon("{{solver_icon}}",color="purple")




    # for the card to be visible, we have to set state.active_sub_ui = "subinitialization_none"
    with ui_subcard(title="no subinitialization", sub_ui_name="subinitialization_none"):
       vuetify.VTextarea(
                label="no subinitialization:",
                rows="5",
                v_model=("subinitializationtext", state.subinitializationtext),
        )



###############################################################
# UI value update #
###############################################################
@state.change('zone_idx')
def update_zone_properties(zone_idx, **kwargs):
  log("info", f"ZONE selected is {zone_idx} {PatchZoneDict}")
  # incompressible
  state.init_patch_pressure = PatchZoneDict[zone_idx]['pressure']
  state.init_patch_velx = PatchZoneDict[zone_idx]['velocity'][0]
  state.init_patch_vely = PatchZoneDict[zone_idx]['velocity'][1]
  state.init_patch_velz = PatchZoneDict[zone_idx]['velocity'][2]
  state.init_patch_temperature = PatchZoneDict[zone_idx]['temperature']
  state.init_patch_nu_tilde_idx = PatchZoneDict[zone_idx]['nu_tidle']
  state.init_patch_sst_k_idx = PatchZoneDict[zone_idx]['tke']
  state.init_patch_sst_w_idx = PatchZoneDict[zone_idx]['dissipation']

  # compressible
  state.init_patch_density = PatchZoneDict[zone_idx]['density']
  state.init_patch_momx = PatchZoneDict[zone_idx]['momentum'][0]
  state.init_patch_momy = PatchZoneDict[zone_idx]['momentum'][1]
  state.init_patch_init_patch_energyx = PatchZoneDict[zone_idx]['momentum'][2]
  state.init_patch_energy = PatchZoneDict[zone_idx]['energy']
  # nu_tidle, tke, dissipation got updated in incompressible

@state.change('init_patch_pressure')
def update_property(init_patch_pressure, **kwargs):
  PatchZoneDict[state.zone_idx]['pressure'] = init_patch_pressure

@state.change('init_patch_velx')
def update_property(init_patch_velx, **kwargs):
  PatchZoneDict[state.zone_idx]['velocity'][0] = init_patch_velx

@state.change('init_patch_vely')
def update_property(init_patch_vely, **kwargs):
  PatchZoneDict[state.zone_idx]['velocity'][1] = init_patch_vely

@state.change('init_patch_velz')
def update_property(init_patch_velz, **kwargs):
  PatchZoneDict[state.zone_idx]['velocity'][2] = init_patch_velz

@state.change('init_patch_momx')
def update_property(init_patch_momx, **kwargs):
  PatchZoneDict[state.zone_idx]['momentum'][0] = init_patch_momx

@state.change('init_patch_momy')
def update_property(init_patch_momy, **kwargs):
  PatchZoneDict[state.zone_idx]['momentum'][1] = init_patch_momy

@state.change('init_patch_momz')
def update_property(init_patch_momz, **kwargs):
  PatchZoneDict[state.zone_idx]['momentum'][2] = init_patch_momz

@state.change('init_patch_temperature')
def update_property(init_patch_temperature, **kwargs):
  PatchZoneDict[state.zone_idx]['temperature'] = init_patch_temperature

@state.change('init_patch_nu_tilde_idx')
def update_property(init_patch_nu_tilde_idx, **kwargs):
  PatchZoneDict[state.zone_idx]['nu_tidle'] = init_patch_nu_tilde_idx

@state.change('init_patch_sst_k_idx')
def update_property(init_patch_sst_k_idx, **kwargs):
  PatchZoneDict[state.zone_idx]['tke'] = init_patch_sst_k_idx

@state.change('init_patch_sst_w_idx')
def update_property(init_patch_sst_w_idx, **kwargs):
  PatchZoneDict[state.zone_idx]['dissipation'] = init_patch_sst_w_idx

@state.change('init_patch_density')
def update_property(init_patch_density, **kwargs):
  PatchZoneDict[state.zone_idx]['density'] = init_patch_density

@state.change('init_patch_energy')
def update_property(init_patch_energy, **kwargs):
  PatchZoneDict[state.zone_idx]['energy'] = init_patch_energy
