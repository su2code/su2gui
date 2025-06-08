# mesh gittree menu

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
#from ui.vtk_helper import *

import vtk

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

from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet

from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkDataSetMapper,
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
)
from vtkmodules.vtkCommonCore import vtkLookupTable

state, ctrl = server.state, server.controller

############################################################################
# Mesh models - global mesh variables #
############################################################################
# define initial square (counterclockwise)
x = [[0.0, 0.0, 0.0],[1.0, 0.0, 0.0],[1.0, 1.0, 0.0],[0.0, 1.0, 0.0]]
pts=[[0,1,2,3]]
points = vtk.vtkPoints()
for i in range(0, len(x)):
        points.InsertPoint(i, x[i])

# We need this global structure
grid = vtkUnstructuredGrid()

# all the markers
markergrid = []
root = vtkMultiBlockDataSet()

# initial mesh
grid.SetPoints(points)
grid.InsertNextCell(VTK_QUAD,4,pts[0])

# Mesh
mesh_mapper = vtkDataSetMapper()

mesh_mapper.SetScalarVisibility(True)
mesh_mapper.SetUseLookupTableScalarRange(True)
lut = vtkLookupTable()
lut.Build()
mesh_mapper.SetLookupTable(lut)

mesh_actor = vtkActor()


############################################################################
# Mesh models - list options #
############################################################################
 #


###############################################################
# PIPELINE CARD : MESH
###############################################################

def mesh_card():
    with ui_card(title="Mesh", ui_name="Mesh"):
        log("info", "## Mesh Selection ##")
        vuetify.VTextarea(
                label="mesh info:",
                rows="5",
                v_model=("meshText", "blablabla"),
        )

###############################################################
# PIPELINE SUBCARD : MESH
###############################################################
# secondary card
def mesh_subcard():

    # for the card to be visible, we have to set state.active_sub_ui = "submesh_none"
    with ui_subcard(title="no mesh submodels", sub_ui_name="submesh_none"):
       vuetify.VTextarea(
                label="no mesh submodels:",
                rows="5",
                v_model=("submodeltext", "no mesh submodel"),
        )
