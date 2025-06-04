r"""
The SU2 Graphical User Interface.
"""

import os
import argparse
from base64 import b64encode

from trame.app import get_server
from trame.app.file_upload import ClientFile
from trame.widgets import markdown

from trame.ui.vuetify import SinglePageWithDrawerLayout
#from trame.ui.vuetify import SinglePageLayout
from trame.widgets import vuetify, vtk as vtk_widgets
from trame.widgets import trame

#import itertools
from datetime import date

# Import json setup for writing the config file in json and cfg file format.
from core.su2_json import *
# Export su2 mesh file.
from core.su2_io import save_su2mesh, save_json_cfg_file
#
from ui.vtk_helper import *
# 
from ui.cases import update_manage_case_dialog_card, manage_case_dialog_card, case_name_dialog_card, case_args
#
# Definition of ui_card and the server.
from ui.uicard import ui_card, server

# Logging funtions
from core.logger import log, clear_logs, Error_dialog_card, Warn_dialog_card, logs_tab

# Config tab
from ui.config import *
# User configuration
from core.user_config import get_su2_path, set_su2_path, clear_config
import platform

import vtk
# vtm reader
#from paraview.vtk.vtkIOXML import vtkXMLMultiBlockDataReader
#from vtkmodules.web.utils import mesh as vtk_mesh
from vtkmodules.vtkCommonDataModel import vtkDataObject
#from vtkmodules.vtkFiltersCore import vtkContourFilter #noqa
from vtkmodules.vtkRenderingAnnotation import vtkAxesActor
from vtkmodules.vtkCommonTransforms import vtkTransform
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkRenderingAnnotation import vtkCubeAxesActor, vtkScalarBarActor
from vtkmodules.vtkInteractionWidgets import vtkOrientationMarkerWidget, vtkScalarBarWidget
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkDataSetMapper,
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
)

from vtkmodules.vtkCommonDataModel import (
    VTK_HEXAHEDRON,
    VTK_LINE,
    VTK_POLYGON,
    VTK_QUAD,
    VTK_TETRA,
    VTK_TRIANGLE,
    VTK_PYRAMID,
    VTK_WEDGE,
    VTK_TRIANGLE_STRIP,
    VTK_VERTEX,
    vtkUnstructuredGrid)

# Required for interactor initialization
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleSwitch  # noqa

# Required for rendering initialization, not necessary for
# local rendering, but doesn't hurt to include it
import vtkmodules.vtkRenderingOpenGL2  # noqa




#############################################################################
# Gittree menu                                                              #
# We have defined each of the tabs in its own module and we import it here. #
# We then call the card in the SinglePageWithDrawerLayout() function.       #
#############################################################################
# gittree menu : import mesh tab                                            #
from ui.mesh import *
# gittree menu : import physics tab                                         #
from ui.physics import *
# gittree menu : import materials tab                                       #
from ui.materials import *
# gittree menu : import numerics tab                                        #
from ui.numerics import *
# gittree menu : import boundaries tab                                      #
from ui.boundaries import *
# gittree menu : import solver tab                                          #
from core.solver import *
# gittree menu : import initialization tab                                  #
from ui.initialization import *
# gittree menu : import file I/O tab                                        #
from ui.fileio import *
#############################################################################


# -----------------------------------------------------------------------------
# Trame setup
# -----------------------------------------------------------------------------
state, ctrl = server.state, server.controller


from core.pipeline import PipelineManager
from pathlib import Path
BASE = Path(__file__).parent

from trame.assets.local import LocalFileManager

clear_logs()
log("info" , f"""
****************************************
Base path = {BASE}    
****************************************
"""
    )

state.filename_cfg_export = "config_new.cfg"
state.filename_json_export = "config_new.json"

# for server side, we need to use a file manager
local_file_manager = LocalFileManager(__file__)
local_file_manager.url("collapsed", BASE / "icons/chevron-up.svg")
local_file_manager.url("collapsible", BASE / "icons/chevron-down.svg")
local_file_manager.url("su2logo", BASE / "img/logoSU2small.png")
local_file_manager.url("favicon", BASE / "img/favicon.ico")

log("info", f"""
****************************************
local_file_manager = {local_file_manager}  
local_file_manager = {type(local_file_manager)}  
local_file_manager = {type(local_file_manager.assets)}  
local_file_manager = {dir(local_file_manager.assets.items())}  
local_file_manager = {local_file_manager.assets.keys()}  
****************************************
"""
    
    )


# matplotlib history
state.show_dialog = False

# TODO FIXME update from user input / cfg file
state.history_filename = 'history.csv'
state.fileio_restart_filename = 'restart'

state.monitorLinesVisibility = []
state.monitorLinesNames = []
state.monitorLinesRange = []

# -----------------------------------------------------------------------------

# keep updating the graph (real-time update with asynchronous io)
state.keep_updating = True
state.countdown = True

# -----------------------------------------------------------------------------
# SU2 setup
# -----------------------------------------------------------------------------

# global iteration number while running a case
#state.global_iter = -1

state.initialize=-1
# number of dimensions of the mesh (2 or 3)
state.nDim = 2

# which boundary is selected?
state.selectedBoundaryName="none"
state.selectedBoundaryIndex = 0

# Boundary Condition Dictionary List
# This is the internal list of dictionaries for the boundary conditions
# This will be converted and written as MARKER info to .json and .cfg files.
state.BCDictList = [{"bcName": "main_wall",
                     "bcType":"Wall",
                     "bc_subtype":"Temperature",
                     "json":"MARKER_ISOTHERMAL",
                     "bc_velocity_magnitude":0.0,
                     "bc_temperature":300.0,
                     "bc_pressure":0,
                     "bc_density":0.0,
                     "bc_massflow":1.0,
                     "bc_velocity_normal":[1,0,0],
                     "bc_heatflux":0.0,
                     "bc_heattransfer":[1000.0,300.0],
                     }]
# disable the export file button
state.export_disabled=True

# (solver.py) disable the solve button
state.su2_solve_disabled=False

# solver settings
# current solver icon
state.solver_icon = "mdi-play-circle"
# current running state
state.solver_running = False

# the imported mesh block and boundary blocks
# must be state or else it cannot be an argument to click
state.su2_meshfile="mesh_out.su2"

# list of all the mesh actors (boundaries)
state.selectedBoundary = 0
mesh_actor_list = [{"id":0,"name":"internal","mesh":mesh_actor}]

# vtk named colors
colors = vtkNamedColors()


mesh_actor.SetMapper(mesh_mapper)
mesh_actor.SetObjectName("initial_square")

# Mesh: Setup default representation to surface
mesh_actor.GetProperty().SetRepresentationToSurface()
mesh_actor.GetProperty().SetPointSize(1)
# show the edges
mesh_actor.GetProperty().EdgeVisibilityOn()
# color is based on field values
renderer.AddActor(mesh_actor)




###################################
# ##### gradient background ##### #
###################################
# bottom: white
renderer.SetBackground(1., 1., 1.)
# top: light blue
renderer.SetBackground2(0.6, 0.8, 1.0)
# activate gradient background
renderer.GradientBackgroundOn()
###################################


# Extract Array/Field information
datasetArrays = []
name = "Solid"
ArrayObject = vtk.vtkFloatArray()
ArrayObject.SetName(name)
# all components are scalars, no vectors for velocity
ArrayObject.SetNumberOfComponents(1)
# how many elements do we have?
nElems = 1
ArrayObject.SetNumberOfValues(nElems)
nPoints = 4
ArrayObject.SetNumberOfTuples(4)


# Nijso: TODO FIXME very slow!
# this is the color of the initial square
#for i in range(nElems):
for i in range(nPoints):
  #ArrayObject.SetValue(i,1.0)
  ArrayObject.SetValue(i,1.0)

grid.GetPointData().AddArray(ArrayObject)
# as soon as we add the array, it is being used for coloring.

datasetArrays.append(
    {
        "text": name,
        "value": 0,
        "range": [1.0,1.0],
        "type": vtkDataObject.FIELD_ASSOCIATION_POINTS,
    }
)
default_array = datasetArrays[0]
default_min, default_max = default_array.get("range")
state.dataset_arrays= datasetArrays
log("info", f"dataset_arrays = {state.dataset_arrays}")

mesh_mapper.SetInputData(grid)
mesh_mapper.SelectColorArray(default_array.get("text"))
mesh_mapper.GetLookupTable().SetRange(default_min, default_max)
mesh_mapper.SetScalarModeToUsePointFieldData()
mesh_mapper.SetScalarVisibility(True)
mesh_mapper.SetUseLookupTableScalarRange(True)

# cube axes (bounded with length scales)
cube_axes = MakeCubeAxesActor()
renderer.AddActor(cube_axes)

# scalar bar
scalar_bar = MakeScalarBarActor()
scalar_bar_widget =MakeScalarBarWidget(scalar_bar)

# coordinate axes
axes1 = MakeAxesActor()
coord_axes = MakeOrientationMarkerWidget(axes1)


renderer.ResetCamera()





# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

pipeline = PipelineManager(state, "git_tree")

# main menu, note that only these are collapsible
# These are head nodes. boundary for instance are all subnodes sharing one head node
# note that subui points to a submenu. We can set it to an existing submenu, or point to "none"
# 1
id_root       = pipeline.add_node(                      name="Mesh",
                                  subui="none", visible=1, color="#9C27B0", actions=["collapsible"])
# 2
id_physics    = pipeline.add_node(parent=id_root,       name="Physics",
                                  subui="none", visible=1, color="#42A5F5", actions=["collapsible"])
# 3
id_materials  = pipeline.add_node(parent=id_physics,    name="Materials",
                                  subui="none", visible=1, color="#42A5F5", actions=["collapsible"])
# 4
id_numerics   = pipeline.add_node(parent=id_materials,  name="Numerics",
                                  subui="none", visible=1, color="#42A5F5", actions=["collapsible"])
# 5
id_boundaries = pipeline.add_node(parent=id_numerics,   name="Boundaries",
                                  subui="none", visible=1, color="#42A5F5", actions=["collapsible"])
# 6
id_initial    = pipeline.add_node(parent=id_boundaries, name="Initialization",
                                  subui="none", visible=1, color="#42A5F5", actions=["collapsible"])
# 7
# id_monitor    = pipeline.add_node(parent=id_initial,    name="Monitor",
#                                   subui="none", visible=1, color="#42A5F5", actions=["collapsible"])
# 8
id_fileio     = pipeline.add_node(parent=id_initial,    name="File I/O",
                                  subui="none", visible=1, color="#42A5F5", actions=["collapsible"])
# 9
id_solver     = pipeline.add_node(parent=id_fileio,    name="Solver",
                                  subui="none", visible=1, color="#00ACC1", actions=["collapsible"])

# first node is active initially
state.selection=["1"]
# important for the interactive ui
state.setdefault("active_ui", "Mesh")
# for submesh
state.setdefault("active_subui", "submesh_none")
state.setdefault("active_parent_ui", "submesh_none")
state.setdefault("active_head_ui", "submesh_none")

pipeline.update()

# which node in the gittree is active
state.active_id=1
# which sub ui menu is active
state.active_sub_ui = "none"

# this counter is used for the gittree items that are added and removed to/from the gittree
state.counter = 0

# -----------------------------------------------------------------------------
# Callbacks
# -----------------------------------------------------------------------------


def actives_change(ids):
    log("info", f"actives_change::ids =  = {ids}")
    _id = ids[0]

    state.active_id = _id

    #state.boundaryText=_id
    log("info", f"actives_change::active id =  = {state.active_id}")
    # get boundary name belonging to ID
    _name = pipeline.get_node(_id)
    # get the headnode of this node
    _headnode = _name['headnode']
    log("info", f"headnode= = {_headnode}")
    log("info", f"active name = = {_name['name']}")


    # if the headnode = active_name, then we have selected the head node
    # if active_name != headnode, then we are a child of the headnode.
    if _headnode == _name['name']:
       log("info", f"   headnode = = {_headnode}")
       # we are at a headnode, so we do not have a parent id
       state.active_parent_ui = "none"
       state.active_head_ui = _headnode
    else:
       log("info", "   we are at child node")
       state.active_parent_ui = _headnode
       # so headnode is none
       state.active_head_ui = "none"


    # check if we need to show a submenu
    _subui = _name['subui']
    # whatever the value, we update the pipeline with it
    state.active_sub_ui = _subui
    log("info", f"subnode= = {_subui}")

    log("info", f"children: = {pipeline._children_map}")

    _name = _name['name']
    log("info", f"active name = = {_name}")
    selectedBoundary = next((item for item in mesh_actor_list if item["name"] == _name), None)
    log("info", f"mesh_actor_list =  = {mesh_actor_list}")
    if not selectedBoundary==None:
      state.selectedBoundaryName = selectedBoundary["name"]
    else:
      # for 2D, show internal as default when we have not selected anything
      if state.nDim == 2:
        state.selectedBoundaryName = "internal"
      else:
        state.selectedBoundaryName = "None"

    log("info", f"selected boundary name =  = {state.selectedBoundaryName}")

    state.dirty('selectedBoundaryName')

    # nijso: hardcode internal as selected mesh
    #state.selectedBoundaryName = "internal"

    # get list of all actors, loop and color the selected actor
    actorlist = vtk.vtkActorCollection()
    actorlist = renderer.GetActors()
    actorlist.InitTraversal()

    # only if we have selected a boundary
    if _headnode!="Boundaries":
      log("info", "************* headnode is not a boundary")
      for a in range(0, actorlist.GetNumberOfItems()):
        actor = actorlist.GetNextActor()
        log("info", f"actor name= = {actor.GetObjectName}")

        # ignore everything that is not a boundary, so CoordAxes and CubeAxes
        if ("Axes" in actor.GetObjectName()):
          continue

        # for 3D, no visualization of internal points
        if (state.nDim==3 and actor.GetObjectName()=="internal"):
          actor.VisibilityOff()
        else:
          # visualize everything
          # the color of the geometry when we are outside of the boundary gittree
          actor.VisibilityOn()
          actor.GetProperty().SetLineWidth(2)
          actor.GetProperty().RenderLinesAsTubesOn()
          actor.GetProperty().SetColor(colors.GetColor3d('floralwhite'))
    else:


      internal=False
      if state.selectedBoundaryName=="internal":
        log("info", "internal selected")
        internal=True

      # ##### show/highlight the actor based on selection ##### #
      # we loop over all actors and switch it on or off
      for a in range(0, actorlist.GetNumberOfItems()):
        actor = actorlist.GetNextActor()
        log("info", f"actor name= = {actor.GetObjectName}")

        if ("Axes" in actor.GetObjectName()):
           continue

        actor.GetProperty().SetRoughness(0.5)
        actor.GetProperty().SetDiffuse(0.5)
        actor.GetProperty().SetAmbient(0.5)
        actor.GetProperty().SetSpecular(0.1)
        actor.GetProperty().SetSpecularPower(10)
        #log("info", f"getnextactor: name = = {actor.GetObjectName(}"))
        #log("info", f"ambient= = {actor.GetProperty(}").GetAmbient())
        #log("info", f"diffuse= = {actor.GetProperty(}").GetDiffuse())
        #log("info", f"specular= = {actor.GetProperty(}").GetSpecular())
        #log("info", f"roughness= = {actor.GetProperty(}").GetRoughness())


        if (state.nDim==3 and actor.GetObjectName()=="internal"):
          actor.VisibilityOff()
        elif actor.GetObjectName() == state.selectedBoundaryName:
            # current actor is selected, we highlight it
            actor.VisibilityOn()
            actor.GetProperty().SetLineWidth(4)
            actor.GetProperty().RenderLinesAsTubesOn()
            actor.GetProperty().SetColor(colors.GetColor3d('yellow'))
        else:
            actor.VisibilityOn()
            if (state.nDim==3 and internal==True):
              actor.GetProperty().SetLineWidth(2)
              actor.GetProperty().RenderLinesAsTubesOn()
              actor.GetProperty().SetColor(colors.GetColor3d('yellow'))
            else:
              actor.GetProperty().SetLineWidth(2)
              actor.GetProperty().RenderLinesAsTubesOn()
              actor.GetProperty().SetColor(colors.GetColor3d('floralwhite'))



    ctrl.view_update()

    log("info", f"state= = {_id}")

    # active ui is the head node of the gittree
    state.active_ui = _headnode

    # check if we need to show a subui

# improvements required
def resetCamera():
    renderer.ResetCamera()
    ctrl.view_update()

###############################################################
# PIPELINE CARD : BOUNDARY
###############################################################
state.meshText="meshtext"
#state.boundaryText="boundtext"
#state.selectedBoundaryName = "internal"






# export su2 file (save on the server)
def save_file_su2(su2_filename):
    log("info", "********** save .su2 **********\n")
      # add the filename to the json database
    state.jsonData['MESH_FILENAME'] = su2_filename
    global root
    save_su2mesh(root,su2_filename)

# Color By Callbacks
def color_by_array(actor, array):
    log("info", "change color by array")

    _min, _max = array.get("range")
    mesh_mapper = actor.GetMapper()
    mesh_mapper.SelectColorArray(array.get("text"))
    mesh_mapper.GetLookupTable().SetRange(_min, _max)

    if array.get("type") == vtkDataObject.FIELD_ASSOCIATION_POINTS:
        mesh_mapper.SetScalarModeToUsePointFieldData()
    else:
        mesh_mapper.SetScalarModeToUseCellFieldData()
    mesh_mapper.SetScalarVisibility(True)
    mesh_mapper.SetUseLookupTableScalarRange(True)

    lut = get_diverging_lut()
    lut.SetTableRange(_min,_max)
    mesh_mapper.SetLookupTable(lut)
    mesh_mapper.GetLookupTable().SetRange(_min, _max)
    actor.SetMapper(mesh_mapper)

    global scalar_bar
    global scalar_bar_widget
    scalar_bar = MakeScalarBarActor()
    scalar_bar_widget =MakeScalarBarWidget(scalar_bar)
    log("info", f"scalarbarwidget= = {scalar_bar_widget}")

@state.change("mesh_color_array_idx")
def update_mesh_color_by_name(mesh_color_array_idx, **kwargs):
    log("info", "change mesh color by array")

    if mesh_color_array_idx < len(state.dataset_arrays):
        array = state.dataset_arrays[mesh_color_array_idx]  
    else:
        array =  {'text': 'Solid', 'value': 0, 'range': [1.0, 1.0], 'type': 0}

    if state.nDim == 2:
      # color the internal
      #color_by_array(mesh_actor, array)
      if(len(mesh_actor_list)> 0 ):
        actor = get_entry_from_name('internal','name',mesh_actor_list)
      else:
        actor = get_entry_from_name('internal','name',[{"id":0,"name":"internal","mesh":mesh_actor}])
      color_by_array(actor['mesh'], array)
    else:
      # color all boundaries (all mesh actors that are not internal)
      for actor in mesh_actor_list:
        log("info", f"3D actor= = {actor}")
        log("info", f"3D actor= = {actor['mesh']}")
        if actor['name'] != 'internal':
          log("info", "passing actor")
          color_by_array(actor['mesh'], array)

    ctrl.view_update()

# every time we change the main gittree ("ui"), we end up here
# we need to update the ui because it might have changed due to changes
# in other git nodes
#
@state.change("active_ui")
def update_active_ui(active_ui, **kwargs):
    # log("info", f"update_active_ui::  = {active_ui}")

    if not(state.active_id == 0):
      # get boundary name belonging to ID
      _name = pipeline.get_node(state.active_id)['name']
      # log("info", f"update_active_ui::name= = {_name}")

      if (_name=="Physics"):
        # log("info", "update node physics")
        #pipeline.update_node_value("Physics","subui",active_ui)
        pass
      elif (_name=="Initialization"):
        # log("info", "update node Initialization")
        # force update of initial_option_idx so we get the submenu
        state.dirty('initial_option_idx')
        #pipeline.update_node_value("Initialization","subui",active_ui)
        # update because it might be changed elsewhere
        #initialization_card()

      ctrl.view_update()

@state.change("active_parent_ui")
def update_active_ui(active_ui, **kwargs):
    log("info", f"update_active_ui::  = {active_ui}")
    if not(state.active_id == 0):
      # get boundary name belonging to ID
      #_name = pipeline.get_node(state.active_id)['name']
      #log("info", f"update_active_ui::name= = {_name}")

      #if (_name=="Physics"):
      #  log("info", "update node physics")
      #elif (_name=="Initialization"):
      #  log("info", "update node Initialization")
      #  # update because it might be changed elsewhere
      #  initialization_card()

      ctrl.view_update()

@state.change("active_head_ui")
def update_active_ui(active_ui, **kwargs):
    log("info", f"update_active_ui::  = {active_ui}")
    if not(state.active_id == 0):
      # get boundary name belonging to ID
      _name = pipeline.get_node(state.active_id)['name']
      #log("info", f"update_active_ui::name= = {_name}")

      if (_name=="Physics"):
        log("info", "*********** update ui: physics ************************")
        # call to update physics submenu visibility
        # this is important when setting all options from the config file
        state.dirty('physics_turb_idx')

      #elif (_name=="Initialization"):
      #  log("info", "update node Initialization")
      #  # update because it might be changed elsewhere
      #  initialization_card()

      ctrl.view_update()


#
# every time we change the main gittree ("ui"), we end up here
# we have to set the correct "subui" again from the last visit.
@state.change("active_sub_ui")
def update_active_sub_ui(active_sub_ui, **kwargs):
    log("info", f"update_active_sub_ui::  = {active_sub_ui}")

    if not(state.active_id == 0):
      _name = pipeline.get_node(state.active_id)['name']
      log("info", f"update_active_sub_ui::parent name= = {_name}")

    log("info", f"choice =  = {state.initial_option_idx}")

    if not(state.active_id == 0):
      # get boundary name belonging to ID
      _name = pipeline.get_node(state.active_id)['name']
      log("info", f"update_active_sub_ui::name= = {_name}")
      if (_name=="Physics"):
        log("info", "update node physics")
        pipeline.update_node_value("Physics","subui",active_sub_ui)

      elif (_name=="Initialization"):
        log("info", "update node Initialization")
        pipeline.update_node_value("Initialization","subui",active_sub_ui)
        # necessary?
        #initialization_subcard()

      ctrl.view_update()


# some default options

state.submodeltext = "none"


# initial value for the materials-fluidmodel list
state.LMaterialsFluid = LMaterialsFluidComp
state.LMaterialsViscosity = LMaterialsViscosityComp
state.LMaterialsConductivity = LMaterialsConductivityComp
state.LMaterialsHeatCapacity = LMaterialsHeatCapacityConst




###############################################################
# FILES
###############################################################

# load SU2 .su2 mesh file #
# currently loads a 2D or 3D .su2 file
@state.change("su2_file_upload")
def load_file_su2(su2_file_upload, **kwargs):
    global pipeline
    # remove the added boundary conditions in the pipeline
    pipeline.remove_right_subnode("Boundaries")

    del mesh_actor_list[:]

    if su2_file_upload is None:
        return

    # check if the case name is set
    if not checkCaseName():
        state.su2_file_upload = None
        return

    # log("info", f"name =  = {su2_file_upload.get("name"}"))
    # log("info", f"last modified =  = {su2_file_upload.get("lastModified"}"))
    # log("info", f"size =  = {su2_file_upload.get("size"}"))
    # log("info", f"type =  = {su2_file_upload.get("type"}"))

    # remove all actors
    renderer.RemoveAllViewProps()
    grid.Reset()


    # ### setup of the internal data structure ###
    branch_interior = vtkMultiBlockDataSet()
    branch_boundary = vtkMultiBlockDataSet()

    global root
    root.SetBlock(0, branch_interior)
    root.GetMetaData(0).Set(vtk.vtkCompositeDataSet.NAME(), 'Interior')
    root.SetBlock(1, branch_boundary)
    root.GetMetaData(1).Set(vtk.vtkCompositeDataSet.NAME(), 'Boundary')
    pts = vtk.vtkPoints()
    # ### ### #

    # mesh file format specific
    file = ClientFile(su2_file_upload)
    try:
        filecontent = file.content.decode('utf-8')
    except:
        filecontent = file.content

    f = filecontent.splitlines()

    index = [idx for idx, s in enumerate(f) if 'NDIME' in s][0]
    NDIME = int(f[index].split('=')[1])
    # number of dimensions of the su2 mesh (2D or 3D)
    state.nDim = NDIME
    # for the mesh info display
    #state.meshText += "Mesh Dimensions: " + str(NDIME) + "D \n"

    index = [idx for idx, s in enumerate(f) if 'NPOIN' in s][0]
    numPoints = int((f[index].split('=')[1]).split()[0])
    #state.meshText += "Number of points: " + str(numPoints) + "\n"

    # get all the points
    for point in range(numPoints):
           x = float()
           y = float()
           z = float()
           line = f[index+point+1].split()
           x = float(line[0])
           y = float(line[1])

           if (NDIME==2):
             # 2D is always x-y plane (z=0)
             z = float(0.0)
           else:
             z = float(line[2])
           pts.InsertNextPoint(x,y,z)

    grid.SetPoints(pts)

    # get the number of elements/cells
    index = [idx for idx, s in enumerate(f) if 'NELEM' in s][0]
    numCells = int(f[index].split('=')[1])
    state.mesh= ["Number of cells: " + str(numCells) + "\n"]

    for cell in range(numCells):
            data = f[index+cell+1].split()
            CellType = int(data[0])
            # quadrilaterals
            if(CellType==9):
              quaddata = [int(data[1]),int(data[2]),int(data[3]),int(data[4])]
              grid.InsertNextCell(VTK_QUAD,4,quaddata)
            # triangles
            elif(CellType==5):
              tridata = [int(data[1]),int(data[2]),int(data[3])]
              grid.InsertNextCell(VTK_TRIANGLE,3,tridata)
            # hexahedral
            elif(CellType==12):
              hexdata = [int(data[1]),int(data[2]),int(data[3]),int(data[4]),int(data[5]),int(data[6]),int(data[7]),int(data[8])]
              grid.InsertNextCell(VTK_HEXAHEDRON,8,hexdata)
            # tetrahedral (4 faces)
            elif(CellType==10):
              tetdata = [int(data[1]),int(data[2]),int(data[3]),int(data[4])]
              grid.InsertNextCell(VTK_TETRA,4,tetdata)
            # wedge
            elif(CellType==13):
              wedgedata = [int(data[1]),int(data[2]),int(data[3]),int(data[4]),int(data[5]),int(data[6])]
              grid.InsertNextCell(VTK_WEDGE,6,wedgedata)
            # pyramid
            elif(CellType==14):
              pyramiddata = [int(data[1]),int(data[2]),int(data[3]),int(data[4]),int(data[5])]
              grid.InsertNextCell(VTK_PYRAMID,5,pyramiddata)
            else:
              log("Error", f"cell type not suppported")


    branch_interior.SetBlock(0, grid)
    branch_interior.GetMetaData(0).Set(vtk.vtkCompositeDataSet.NAME(), 'Fluid-Zone-1')
    del branch_interior

    # ### read the markers ### #
    boundaryNames = []

    markerNames=[]
    index = [idx for idx, s in enumerate(f) if 'NMARK' in s][0]
    numMarkers = int(f[index].split('=')[1])

    global markergrid
    markergrid = [vtkUnstructuredGrid() for i in range(numMarkers)]

    # now loop over the markers
    counter=0
    for iMarker in range(numMarkers):
          # grid for the marker
          #markergrid = vtkUnstructuredGrid()
          # copy all the points into the markergrid (inefficient)
          markergrid[iMarker].SetPoints(pts)
          # next line: marker tag, marker_elem
          counter += 1
          # this is the name (string) of the boundary
          markertag = f[index+counter].split("=")[1].strip()

          # add name to the boundaryNames list of dicts
          boundaryNames.append(
            {
                "text": markertag,
                "value": iMarker,
            }
          )
          markerNames.append(markertag)
          # next line: marker tag, marker_elem
          counter+=1
          line = f[index+counter].split("=")
          numCells = int(line[1])
          #log("info", f"number of cells =  = {numCells}")

          # loop over all cells
          for cell in range(numCells):
            counter+=1
            data = f[index+counter].split()
            #log("info", f"data =  = {data}")
            CellType = int(data[0])
            # line
            if(CellType==3):
              linedata = [int(data[1]),int(data[2])]
              markergrid[iMarker].InsertNextCell(VTK_LINE,2,linedata)
            # triangles
            elif(CellType==5):
              tridata = [int(data[1]),int(data[2]),int(data[3])]
              markergrid[iMarker].InsertNextCell(VTK_TRIANGLE,3,tridata)
            # quadrilaterals
            elif(CellType==9):
              quaddata = [int(data[1]),int(data[2]),int(data[3]),int(data[4])]
              markergrid[iMarker].InsertNextCell(VTK_QUAD,4,quaddata)
            else:
              log("Error", f"marker cell type not suppported")
          # put boundary in multiblock structure
          branch_boundary.SetBlock(iMarker, markergrid[iMarker])
          branch_boundary.GetMetaData(iMarker).Set(vtk.vtkCompositeDataSet.NAME(), markertag)


    # end loop over lines

    #del markergrid
    #del pts

    # boundary meshes as unstructured grids
    ds_b = []
    for i in range(branch_boundary.GetNumberOfBlocks()):
        ds_b.append(vtk.vtkUnstructuredGrid.SafeDownCast(branch_boundary.GetBlock(i)))
    del branch_boundary

    # we also clear the arrays, if any
    for array in state.dataset_arrays:
        arrayName = array.get("text")
        log("info", f"removing array  = {arrayName}")
        grid.GetPointData().RemoveArray(arrayName)
        # nijso TODO BUG does not contain data yet
        #for iMarker in range(numMarkers):
        #  markergrid[iMarker].GetPointData().RemoveArray(arrayName)
       
    # and we only use the default array
    state.dataset_arrays = []

    # show the internal mesh in 2D
    if (NDIME==2):
      mesh_actor.VisibilityOn()
      mesh_actor.GetProperty().EdgeVisibilityOn()
    else:
      mesh_actor.VisibilityOff()
    # initial color of the geometry
    mesh_actor.GetProperty().SetColor(colors.GetColor3d('floralwhite'))
    # Mesh - add mesh to the renderer
    mesh_mapper.SetInputData(grid)

    mesh_actor.SetMapper(mesh_mapper)
    mesh_actor.SetObjectName("internal")

    renderer.AddActor(mesh_actor)

    # boundary actors
    boundary_id = 101
    i = 0
    log("info", f"length of ds_b= = {len(ds_b)}")
    for bcName in boundaryNames:
        log("info", f"bc name= = {bcName}")
        mesh_mapper_b1 = vtkDataSetMapper()
        mesh_mapper_b1.ScalarVisibilityOff()
        mesh_actor_b1 = vtkActor()
        # in 2D, we show the interior (2D surface) and in 3D, we show all boundaries
        if (NDIME==2):
          mesh_actor_b1.VisibilityOff()
        else:
          mesh_actor_b1.VisibilityOn()
          mesh_actor_b1.GetProperty().EdgeVisibilityOn()


        mesh_actor_b1.GetProperty().SetColor(colors.GetColor3d('Peacock'))

        mesh_mapper_b1.SetInputData(ds_b[i])
        i += 1
        mesh_actor_b1.SetMapper(mesh_mapper_b1)
        mesh_actor_b1.SetObjectName(bcName.get("text"))

        renderer.AddActor(mesh_actor_b1)

        mesh_actor_list.append({"id":boundary_id,"name":bcName.get("text"), "mesh":mesh_actor_b1})
        boundary_id += 1

    # add internal mesh as well.
    mesh_actor_list.append({"id":boundary_id,"name":"internal", "mesh":mesh_actor})
    # internal block is also a 'boundary'
    boundaryNames.append(
                            {
                        "text": "internal",
                        "value": numMarkers,
                    }
    )

    # now construct the actual boundary list for the GUI
    for bcName in boundaryNames:
       log("info", f"boundary name= = {bcName.get('text')}")
       # add the boundaries to the right tree and not the left tree
       id_aa = pipeline.append_node(parent_name="Boundaries", name=bcName.get("text"), left=False, subui="none", visible=1, color="#2962FF")

    state.BCDictList = []
    # fill the boundary conditions with initial boundary condition type
    for bcName in boundaryNames:
      log("info", f"*************** BCNAME ********** = {bcName}")
      # do not add internal boundaries to bcdictlist
      if bcName.get("text") != "internal":
        state.BCDictList.append({"bcName":bcName.get("text"),
                                 "bcType":"Wall",
                                 "bc_subtype":"Temperature",
                                 "json":"MARKER_ISOTHERMAL",
                                 "bc_velocity_magnitude":1.0,
                                 "bc_temperature":300.0,
                                 "bc_pressure":0.0,
                                 "bc_density":1.2,
                                 "bc_massflow":0.0,
                                 "bc_velocity_normal":[1.0, 0.0, 0.0],
                                 "bc_heatflux":0.0,
                                 "bc_heattransfer":[0.0, 300.0],
                                 },
                                 )
      else:
        state.BCDictList.append({"bcName":bcName.get("text"),
                                 "bcType":"Internal",
                                 "bc_subtype":"None",
                                 "json":"NONE",
                                 "bc_velocity_magnitude":0.0,
                                 "bc_temperature":0.0,
                                 "bc_pressure":0.0,
                                 "bc_density":0.0,
                                 "bc_massflow":0.0,
                                 "bc_velocity_normal":[0.0, 0.0, 0.0],
                                 "bc_heatflux":0.0,
                                 "bc_heattransfer":[0.0, 0.0],
                                 },
                                 )


    # We have loaded a mesh, so enable the exporting of files
    state.export_disabled = False

    # we have deleted all actors, so add the non-boundary actors again
    #  TODO: only delete the mesh related actors
    global cube_axes
    cube_axes = MakeCubeAxesActor()
    renderer.AddActor(cube_axes)

    global scalar_bar
    global scalar_bar_widget
    scalar_bar = MakeScalarBarActor()
    scalar_bar_widget =MakeScalarBarWidget(scalar_bar)

    #coordinate axes to show orientation
    global coord_axes
    axes1 = MakeAxesActor()
    coord_axes = MakeOrientationMarkerWidget(axes1)

    resetCamera()
    
    update_config_str()
    state.dirty('restartFile')


# load cofiguration .cfg file
@state.change("cfg_file_upload")
def load_cfg_file(cfg_file_upload, **kwargs):

    if cfg_file_upload is None:
        return

    # check if the case name is set
    if not checkCaseName():
        state.cfg_file_upload = None
        return

    file = ClientFile(cfg_file_upload)
    try:
        filecontent = file.content.decode('utf-8')
    except:
        filecontent = file.content

    # reading each line of configuration file
    f = filecontent.splitlines()
    cfglist = []
    f = [element for element in f if not (element.strip().startswith("%")) and len(element.strip())]
    for item in f:
       item = item.strip()
       if(item[0] == "%" or len(item)<1):
          continue   
       if(len(cfglist) and cfglist[-1][-1]=='\\'):
          cfglist[-1] = cfglist[-1][:-1]
          cfglist[-1] += item
       else:
          cfglist.append(item)
    
    cfg_dict = {}
    for item in cfglist:
        key, value = item.split('=', 1)
        key = key.strip()
        value = value.strip()
        
        # Convert value to appropriate type
        if (value.startswith('(') and value.endswith(')')) or ',' in value or ' ' in value:
            # Remove parentheses and split by comma
            if value[0]=='(' or value[-1]==')':
               value = value[1:-1]
            if ',' in value:
               value =  value.split(',')
            else:
               value = value.split()
            # Convert each item to an appropriate type
            value = [v.strip() for v in value]
            value = [int(v) if v.isdigit() else v for v in value]
        elif value.isdigit():
            value = int(value)
        elif value.upper() == 'YES' or value.upper() == 'TRUE':
            value = True
        elif value.upper() == 'NO' or value.upper() == 'FALSE':
            value = False   
        elif value.upper() == 'NONE':
            value = None
        else:
            try:
                value = float(value)
            except ValueError:
                pass # Keep as string if it cannot be converted to int or float
        
        cfg_dict[key] = value


    # checking if the value of state.jsonData['OUTPUT_WRT_FREQ'] is int
    # if yes set it to a list of 2 elements with same value for proper working
    if 'OUTPUT_WRT_FREQ' in cfg_dict and isinstance(cfg_dict['OUTPUT_WRT_FREQ'], int):
      cfg_dict['OUTPUT_WRT_FREQ']= [cfg_dict['OUTPUT_WRT_FREQ']] * 2

    # Write the dictionary to a JSON file
    # with open(BASE / "user" / state.filename_json_export, 'w') as f:
    #     json.dump(cfg_dict, f, indent=4)
    # assigning new values to jsonData

    cfg_dict.pop('SOLUTION_FILENAME', None)
    cfg_dict.pop('RESTART_SOL', None)
    state.jsonData = cfg_dict
    state.dirty('jsonData')

      
    # save the cfg file
    # save_json_cfg_file(state.filename_json_export,state.filename_cfg_export)

    updateBCDictListfromJSON()
    # set all physics states from the json file
    # this is reading the config file (done by read_json_data) and filling it into the GUI menu's
    set_json_physics()
    set_json_initialization()
    set_json_numerics()
    set_json_solver()
    set_json_fileio()
    set_json_materials()

    # set config file data in config_str
    update_config_str()


# -----------------------------------------------------------------------------
# GUI elements
# -----------------------------------------------------------------------------

# collapse or expand the gittree
def on_action(event):
    #log("info", f"on_action = {event}")
    _id = event.get("id")
    _action = event.get("action")
    if _action.startswith("collap"):
        log("info", pipeline.toggle_collapsed(_id))

def on_event(event):
    log("info", event)



# git tree in the left drawer
def pipeline_widget():
    trame.GitTree(
        sources = ("git_tree", pipeline),
        ### collabsable gittree: ###
        action_map=("icons", local_file_manager.assets),
        # size of the icon
        action_size=25,
        width=350,
        action=(on_action, "[$event]"),
        # default active is first node
        actives = ("selection",state.selection),
        actives_change=(actives_change, "[$event]"),
    )

###############################################################
# checnge edge visibility
###############################################################
@state.change("vtkEdgeVisibility")
def changevtkEdgeVisibility(vtkEdgeVisibility, **kwargs):

    log("info", f"edge:  = {vtkEdgeVisibility}")
    # can only be activated/deactivated for incompressible
    #state.energy = bool(state.physics_energy_idx)
    # get list of all actors, loop and color the selected actor
    actorlist = vtk.vtkActorCollection()
    actorlist = renderer.GetActors()
    actorlist.InitTraversal()
    for a in range(0, actorlist.GetNumberOfItems()):
        actor = actorlist.GetNextActor()
        if vtkEdgeVisibility==True:
          actor.GetProperty().EdgeVisibilityOn()
        else:
          actor.GetProperty().EdgeVisibilityOff()

    ctrl.view_update()

# visibility if the cube axes (bounding box) is on
@state.change("cube_axes_visibility")
def update_cube_axes_visibility(cube_axes_visibility, **kwargs):
    log("info", "change axes visibility")
    cube_axes.SetVisibility(cube_axes_visibility)
    ctrl.view_update()

# visibility if the coordinate axes is on
@state.change("coord_axes_visibility")
def update_coord_axes_visibility(coord_axes_visibility, **kwargs):
    log("info", "change coord axes visibility")
    coord_axes.SetEnabled(coord_axes_visibility)
    ctrl.view_update()

# visibility if the color bar is on
@state.change("color_bar_visibility")
def update_color_bar_visibility(color_bar_visibility, **kwargs):
    log("info", "change color bar visibility")
    scalar_bar_widget.SetEnabled(color_bar_visibility)
    ctrl.view_update()

# buttons in the top header
def standard_buttons():
    # button for opening dialog box for managing cases
    with vuetify.VBtn("Cases",click=(update_manage_case_dialog_card)):
       vuetify.VIcon("mdi-folder-multiple-outline", classes="ml-2")


# -----------------------------------------------------------------------------
# Web App setup
# -----------------------------------------------------------------------------

state.trame__title = "SU2 GUI"
state.trame__favicon = local_file_manager.assets['favicon']

with SinglePageWithDrawerLayout(server) as layout:

    # text inside the toolbar
    layout.title.set_text(" ")

    # matplotlib monitor: read the initial history file
    [state.x,state.ylist] = readHistory(BASE / "user" / state.case_name / state.history_filename)
    log("info", f"x= = {state.x}")
    log("info", f"y= = {state.ylist}")

    with layout.toolbar:

        #vuetify.VSpacer()
        with vuetify.VBtn():
          vuetify.VImg(
            src=local_file_manager.assets['su2logo'],
            contain=True,
            height=50,
            width=50,
          )

        # vertical spacer inside the toolbar
        vuetify.VSpacer()

        # vertical divider inside the toolbar (solid line)
        vuetify.VDivider(vertical=True, classes="mx-2")
        standard_buttons()
        vuetify.VDivider(vertical=True, classes="mx-2")

        ######################################################
        # scalar selection field inside the top toolbar
        vuetify.VSelect(
            # Color By
            label="Color by",
            v_model=("mesh_color_array_idx", 0),
            #items=("array_list", datasetArrays),
            items=("Object.values(dataset_arrays)",),
            hide_details=True,
            dense=True,
            outlined=True,
            classes="pt-1",
            #v_model=("field", "solid"),
            #items=("Object.values(fields)",),
            style="max-width: 300px;",
            #classes="mr-4",
        )
        ######################################################

        # file input inside the top toolbar
        # input .su2 file
        vuetify.VFileInput(
            # read more than one file
            multiple=False,
            background_color="white",
            # the icon in front of the file input
            prepend_icon="mdi-file",
            show_size=True,
            small_chips=True,
            truncate_length=25,
            v_model=("su2_file_upload", None),
            label="Load .SU2 Mesh File",
            dense=True,
            hide_details=True,
            style="max-width: 250px;",
            # only accepts paraview .vtm files
            accept=".su2",
            __properties=["accept"],
        )

        # input .cfg file
        vuetify.VFileInput(
            # read more than one file
            multiple=False,
            background_color="white",
            # the icon in front of the file input
            prepend_icon="mdi-file",
            show_size=True,
            small_chips=True,
            truncate_length=25,
            v_model=("cfg_file_upload", None),
            label="Load .CFG File (optional)",
            dense=True,
            hide_details=True,
            style="max-width: 250px;",
            accept=".cfg",
            __properties=["accept"],
        )


        # progress inside the toolbar
        vuetify.VProgressLinear(
            indeterminate=True, absolute=True, bottom=True, active=("trame__busy",)
        )


    # left side menu
    with layout.drawer as drawer:
        # drawer components
        drawer.width = 400
        # git pipeline widget (defined below)
        pipeline_widget()
        # simple divider
        vuetify.VDivider(classes="mb-2")
        #
        log("info", "initialize boundary card")
        # main head/parent node
        boundaries_card_parent()
        # children nodes (the actual boundaries)
        boundaries_card_children()
        #
        log("info", "initialize physics card")
        physics_card()
        physics_subcard()
        #
        log("info", "initialize materials card")
        materials_card()
        #materials_subcard()
        #
        log("info", "initialize numerics card")
        numerics_card()
        #
        log("info", "initialize initialization card")
        initialization_card()
        initialization_patch_subcard()
        initialization_file_subcard()
        initialization_uniform_subcard()
        #
        log("info", "initialize mesh card")
        mesh_card()
        mesh_subcard()
        #
        log("info", "initialize fileio card")
        fileio_card()
        #

        log("info", "initialize solver card")
        solver_card()
        #

        # dialog cards - these are predefined 'popup windows'
        # Output dialog
        manage_case_dialog_card()
        case_name_dialog_card()
        # Physics dialog
        wall_function_dialog_card()
        # material dialogs
        materials_dialog_card_fluid()
        materials_dialog_card_viscosity()
        materials_dialog_card_cp()
        materials_dialog_card_conductivity()
        # boundaries dialogs
        boundaries_dialog_card_inlet()
        boundaries_dialog_card_outlet()
        boundaries_dialog_card_wall()
        boundaries_dialog_card_farfield()
        boundaries_dialog_card_supersonic_inlet()
        # error/warn dialog
        Error_dialog_card()
        Warn_dialog_card()

        solver_dialog_card_convergence()
        # set all physics states from the json file
        # this is reading the config file (done by read_json_data) and filling it into the GUI menu's
        set_json_physics()
        set_json_materials()
        set_json_initialization()
        set_json_fileio()
        set_json_numerics()
        set_json_solver()

        # set config file data in config_str
        update_config_str()
        #this necessary here?
        #state.dirty('jsonData')

    log("info", "setting up layout content")
    with layout.content:

      # create the tabs
      with vuetify.VTabs(v_model=("active_tab", 0), right=True):
        vuetify.VTab("Geometry")
        vuetify.VTab("History")
        vuetify.VTab("Config")
        vuetify.VTab("Logs")

      with vuetify.VContainer(
            fluid=True,
            classes="pa-0 fill-height",
            style="position: relative;"
      ):
        # create the tabs
        with vuetify.VTabsItems(
            value=("active_tab",), style="width: 100%; height: 100%;"
        ):
            # first tab
            with vuetify.VTabItem(
                value=(0,), style="width: 100%; height: 100%;"
            ):
              # row containing everything
              with vuetify.VRow(dense=True, style="height: 100%;", classes="pa-0 ma-0"):
                # First column containing renderview buttons
                with vuetify.VCol(cols="1",classes="pa-0 ma-0"):

                  with vuetify.VRow(dense=True,classes="pa-0 ma-0"):
                    # reset the view
                    with vuetify.VBtn(icon=True, click=(resetCamera)):
                      vuetify.VIcon("mdi-crop-free")

                  with vuetify.VRow(dense=True,classes="pa-0 ma-0"):
                    # switch on/off edge visibility in the mesh
                    vuetify.VCheckbox(
                      v_model=("vtkEdgeVisibility", True),
                      on_icon="mdi-grid",
                      off_icon="mdi-grid-off",
                      #true_value="gridOff",
                      #false_value="gridOn",
                      classes="mx-1",
                      hide_details=True,
                      dense=True,
                    )

                  with vuetify.VRow(dense=True,classes="pa-0 ma-0"):
                    # switch on/off the bounding box visualisation
                    vuetify.VCheckbox(
                      v_model=("cube_axes_visibility", False),
                      on_icon="mdi-cube-outline",
                      off_icon="mdi-cube-off-outline",
                      classes="mx-1",
                      hide_details=True,
                      dense=True,
                  )
                  with vuetify.VRow(dense=True,classes="pa-0 ma-0"):
                    # switch on/off the coordinate axes visualisation
                    vuetify.VCheckbox(
                      v_model=("coord_axes_visibility", True),
                      on_icon="mdi-axis-arrow",
                      off_icon="mdi-square-outline",
                      classes="mx-1",
                      hide_details=True,
                      dense=True,
                  )
                  with vuetify.VRow(dense=True,classes="pa-0 ma-0"):
                    # switch on/off the coordinate axes visualisation
                    vuetify.VCheckbox(
                      v_model=("color_bar_visibility", True),
                      on_icon="mdi-water",
                      off_icon="mdi-water-off",
                      classes="mx-1",
                      hide_details=True,
                      dense=True,
                  )
                # second column containing the renderview (move window left by 12)
                with vuetify.VCol(cols="11", classes="pa-0 ml-n12 mr-0 my-0"):
                  view = vtk_widgets.VtkRemoteView(renderWindow)
                  ctrl.view_update = view.update
                  ctrl.view_reset_camera = view.reset_camera
                  ctrl.on_server_ready.add(view.update)

            # second tab
            with vuetify.VTabItem(
               value=(1,), style="width: 100%; height: 100%;"
            ):
             with vuetify.VRow(dense=True, style="height: 100%;", classes="pa-0 ma-0"):
                with vuetify.VBtn(classes="ml-2 mr-0 mt-16 mb-0 pa-0", elevation=1,variant="text",color="white",click=update_dialog, icon="mdi-dots-vertical"):
                  vuetify.VIcon("mdi-dots-vertical",density="compact",color="red")
                with vuetify.VCol(
                    classes="pa-0 ma-0",
                    #style="border-right: 1px solid #ccc; position: relative;",
                ):
                  with trame.SizeObserver("figure_size"):
                    html_figure = tramematplotlib.Figure(style="position: absolute")
                    ctrl.update_figure = html_figure.update

            # Third Tab
            config_tab()

            # Fourth Tab
            logs_tab()


    log("info", "finalizing drawer layout")

# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

def check_su2(path=None):
  """Check if SU2 is installed and accessible, prompt for path if not."""
  
  # First check if a path is provided as a parameter
  if path:
    executable = path
    if platform.system() == "Windows" and not executable.lower().endswith('.exe'):
      executable += ".exe"
    
    if os.path.isfile(executable):
      try:
        result = subprocess.run([executable, "--help"], 
                     stdout=subprocess.PIPE, 
                     stderr=subprocess.PIPE, 
                     text=True, 
                     timeout=5)
        if "SU2" in result.stdout or "SU2" in result.stderr:
          print(f"Using provided SU2_CFD from: {path}")
          set_su2_path(path)
          return path
        else:
          print("The provided file does not appear to be SU2_CFD. Falling back to other methods.")
      except (subprocess.SubprocessError, OSError):
        print("Could not execute the provided file. Falling back to other methods.")
  
  # Try to get the path from config
  su2_path = get_su2_path()
  
  # If path exists in config, check if it's valid
  if su2_path:
    executable = su2_path
    if platform.system() == "Windows" and not executable.lower().endswith('.exe'):
      executable += ".exe"
    
    if os.path.isfile(executable) and os.access(executable, os.X_OK):
      print(f"Using SU2_CFD from stored configuration: {su2_path}")
      return su2_path
  
  # Try to find SU2_CFD in PATH
  su2_command = shutil.which("SU2_CFD")
  
  if su2_command:
    print("SU2_GUI is able to access SU2_CFD from system PATH.")
    # Store this path for future use
    set_su2_path(su2_command)
    return su2_command
  
  print("\nSU2 is not found in PATH or stored configuration.")
  print("Please provide the path to the SU2_CFD executable.")
  print("Example: /opt/su2/bin/SU2_CFD or C:\\Program Files\\SU2\\bin\\SU2_CFD.exe")
  
  while True:
    # Get path from user
    user_path = input("SU2_CFD path: ").strip()
    
    if not user_path:
      response = input("Continue without SU2? (y/n): ").strip().lower()
      if response != 'y':
        print("Process aborted. Please install SU2 and try again.")
        exit(1)
      return None
    
    # Check if the path is valid
    executable = user_path
    if platform.system() == "Windows" and not executable.lower().endswith('.exe'):
      executable += ".exe"
    
    if os.path.isfile(executable):
      # Test if it's actually SU2_CFD by running it with --help
      try:
        result = subprocess.run([executable, "--help"], 
                     stdout=subprocess.PIPE, 
                     stderr=subprocess.PIPE, 
                     text=True, 
                     timeout=5)
        if "SU2" in result.stdout or "SU2" in result.stderr:
          print(f"SU2_CFD found at: {user_path}")
          # Store this path for future use
          set_su2_path(user_path)
          return user_path
        else:
          print("The file does not appear to be SU2_CFD. Please provide the correct path.")
      except (subprocess.SubprocessError, OSError):
        print("Could not execute the file. Please ensure it has execute permissions.")
    else:
      print("File not found. Please provide a valid path.")

def main():

    # Argument parsing
    parser = argparse.ArgumentParser(description='Start the SU2 GUI application.')
    parser.add_argument('-p', '--port', type=int, default=8080, help='Port to run the server.')
    parser.add_argument('-c', '--case', type=str, help='Name of case to start with.')
    parser.add_argument('-m', '--mesh', type=str, help='Path to the SU2 mesh file in .su2 format.')
    parser.add_argument('--config', type=str, help='Path to the configuration file.')
    parser.add_argument('--restart', type=str, help='Path to the restart file in .csv/.dat format.')
    parser.add_argument('--su2', type=str, help='Path to the SU2_CFD executable. Overrides stored path.')
    parser.add_argument('--clear-data', action='store_true', help='Clear all application data including saved configurations and cases.')
    parser.add_argument('-v', '--version', action='store_true', help='Print the version of SU2GUI and exit.')


    args = parser.parse_args()

    mesh_path = args.mesh
    config_path = args.config
    restart_path = args.restart
    case = args.case
    su2_path = args.su2
    clear_data = args.clear_data
    version = args.version

    if version:
        print(f"SU2GUI version 1.0.2")
        exit(0)

    if clear_data:
        clear_config()
        print("All application data cleared.")
        exit(0)

    # Check if SU2 is installed and get the path
    su2_path = check_su2(su2_path)
    
    # Store su2_path for use in solver.py
    state.su2_cfd_path = su2_path


    if case:
        case_args(case)

    if mesh_path and os.path.exists(mesh_path):
        log("info", f"Using SU2 mesh file {mesh_path}")
        with open(mesh_path, 'r') as f:
            content = f.read()
            state.su2_file_upload = {
                "name": os.path.basename(mesh_path),
                "size": os.stat(mesh_path).st_size,
                "content": content,
                "type": "text/plain",
            }
        state.dirty('su2_file_upload')
    elif mesh_path:
        log("error", f"The SU2 mesh file {mesh_path} does not exist, and was not loaded.")

    if config_path and os.path.exists(config_path):
        log("info", f"Using configuration file {config_path}")
        with open(config_path, 'r') as f:
            content = f.read()
            state.cfg_file_upload = {
                "name": os.path.basename(config_path),
                "size": os.stat(config_path).st_size,
                "content": content,
                "type": "text/plain",
            }
        state.dirty('cfg_file_upload')
    elif config_path:
        log("error", f"The configuration file {config_path} does not exist, and was not loaded.")

    if restart_path and os.path.exists(restart_path):
        if not mesh_path:
            log("error", "Cannot load restart file without SU2 mesh file.")
        else:
            log("info", f"Using restart file {restart_path}")
            content = None
            if restart_path.endswith(".dat"):
                with open(restart_path, 'rb') as f:
                    content = b64encode(f.read()).decode('utf-8')

            else:
                with open(restart_path, 'r') as f:
                    content = f.read()

            state.restartFile = {
                "name": os.path.basename(restart_path),
                "size": os.stat(restart_path).st_size,
                "content": content,
                "type": "text/plain" if not restart_path.endswith(".dat") else "application/octet-stream",
            }
            state.dirty('restartFile')
    elif restart_path:
        log("error", f"The restart file {restart_path} does not exist, and was not loaded.")

    # If --su2 argument is provided, update the stored path
    if args.su2:
        from core.user_config import set_su2_path
        set_su2_path(args.su2)
        state.su2_cfd_path = args.su2

    # Flush all states at once
    state.flush()

    log("info", f"Application Started - Initializing SU2GUI Server at port {args.port}")
    server.start(port=args.port)
    log("info", "SU2GUI Server Ended...")



if __name__=="__main__":
    main()