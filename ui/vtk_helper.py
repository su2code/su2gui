# vtk_helper.py
# helper functions for vtk and rendering related actions

import sys
import os
from pathlib import Path

# Add parent directory to path to allow importing from sibling directories
parent_dir = str(Path(__file__).parent.parent.absolute())
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

import vtk
# vtm reader
#from paraview.vtk.vtkIOXML import vtkXMLMultiBlockDataReader
#from vtkmodules.web.utils import mesh as vtk_mesh
from vtkmodules.vtkCommonDataModel import vtkDataObject
#from vtkmodules.vtkFiltersCore import vtkContourFilter #noqa
from vtkmodules.vtkRenderingAnnotation import vtkAxesActor
from vtkmodules.vtkCommonTransforms import vtkTransform
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkCommonCore import vtkLookupTable
from vtkmodules.vtkRenderingAnnotation import vtkCubeAxesActor, vtkScalarBarActor
from vtkmodules.vtkInteractionWidgets import vtkOrientationMarkerWidget, vtkScalarBarWidget
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkDataSetMapper,
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkColorTransferFunction,
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

# mesh_mapper
from ui.mesh import *

# Logging function
from core.logger import log

# default visibility of the actors
state.cube_axes_visibility = True
state.coord_axes_visibility = True
state.color_bar_visibiliy = True

renderer = vtkRenderer()

renderWindow = vtkRenderWindow()
renderWindow.AddRenderer(renderer)
# offscreen rendering, no additional pop-up window
renderWindow.SetOffScreenRendering(1)

renderWindowInteractor = vtkRenderWindowInteractor()
renderWindowInteractor.SetRenderWindow(renderWindow)
renderWindowInteractor.GetInteractorStyle().SetCurrentStyleToTrackballCamera()

def MakeAxesActor():
    axes = vtkAxesActor()
    axes.SetObjectName("CoordAxes")
    axes.SetShaftTypeToCylinder()
    # text labels 
    axes.SetXAxisLabelText('X')
    axes.SetYAxisLabelText('Y')
    axes.SetZAxisLabelText('Z')
    axes.SetTotalLength(1.0, 1.0, 1.0)
    axes.SetCylinderRadius(0.5 * axes.GetCylinderRadius())
    axes.SetConeRadius(1.025 * axes.GetConeRadius())
    axes.SetSphereRadius(1.5 * axes.GetSphereRadius())
    return axes

def MakeOrientationMarkerWidget(axes):
    coordaxes = vtkOrientationMarkerWidget()
    coordaxes.SetOrientationMarker(axes)
    # Position lower left in the viewport.
    coordaxes.SetViewport(0, 0, 0.2, 0.2)
    coordaxes.SetInteractor(renderWindowInteractor)
    coordaxes.SetEnabled(True)
    coordaxes.InteractiveOn()
    return coordaxes

def MakeCubeAxesActor():
    cubeaxes = vtkCubeAxesActor()
    cubeaxes.SetObjectName("CubeAxes")
    # Cube Axes: Boundaries, camera, and styling
    # nijso TODO BUG? Which actor is used here???
    cubeaxes.SetBounds(mesh_actor.GetBounds())
    cubeaxes.SetCamera(renderer.GetActiveCamera())
    cubeaxes.SetXLabelFormat("%6.1f")
    cubeaxes.SetYLabelFormat("%6.1f")
    cubeaxes.SetZLabelFormat("%6.1f")
    #cube_axes.SetFlyModeToOuterEdges()
    #cube_axes.SetUseTextActor3D(1)
    cubeaxes.GetTitleTextProperty(0).SetColor(0.0, 0.0, 0.0)
    cubeaxes.GetTitleTextProperty(1).SetColor(0.0, 0.0, 0.0)
    cubeaxes.GetTitleTextProperty(2).SetColor(0.0, 0.0, 0.0)
    cubeaxes.GetLabelTextProperty(0).SetColor(0.0, 0.0, 0.0)
    cubeaxes.GetLabelTextProperty(1).SetColor(0.0, 0.0, 0.0)
    cubeaxes.GetLabelTextProperty(2).SetColor(0.0, 0.0, 0.0)
    cubeaxes.DrawXGridlinesOn()
    cubeaxes.DrawYGridlinesOn()
    cubeaxes.DrawZGridlinesOn()
    cubeaxes.GetXAxesLinesProperty().SetColor(0.0, 0.0, 0.0)
    cubeaxes.GetYAxesLinesProperty().SetColor(0.0, 0.0, 0.0)
    cubeaxes.GetZAxesLinesProperty().SetColor(0.0, 0.0, 0.0)
    cubeaxes.GetXAxesGridlinesProperty().SetColor(0.0, 0.0, 0.0)
    cubeaxes.GetYAxesGridlinesProperty().SetColor(0.0, 0.0, 0.0)
    cubeaxes.GetZAxesGridlinesProperty().SetColor(0.0, 0.0, 0.0)
    cubeaxes.XAxisMinorTickVisibilityOff()
    cubeaxes.YAxisMinorTickVisibilityOff()
    cubeaxes.ZAxisMinorTickVisibilityOff()
    cubeaxes.SetVisibility(False)
    state.cube_axes_visibility = False

    return cubeaxes



def get_diverging_lut():
    """
    See: [Diverging Color Maps for Scientific Visualization](https://www.kennethmoreland.com/color-maps/)
                       start point         midPoint            end point
     cool to warm:     0.230, 0.299, 0.754 0.865, 0.865, 0.865 0.706, 0.016, 0.150
     purple to orange: 0.436, 0.308, 0.631 0.865, 0.865, 0.865 0.759, 0.334, 0.046
     green to purple:  0.085, 0.532, 0.201 0.865, 0.865, 0.865 0.436, 0.308, 0.631
     blue to brown:    0.217, 0.525, 0.910 0.865, 0.865, 0.865 0.677, 0.492, 0.093
     green to red:     0.085, 0.532, 0.201 0.865, 0.865, 0.865 0.758, 0.214, 0.233

    :return:
    """
    ctf = vtkColorTransferFunction()
    ctf.SetColorSpaceToDiverging()
    # Cool to warm.
    ctf.AddRGBPoint(0.0, 0.230, 0.299, 0.754)
    ctf.AddRGBPoint(0.5, 0.865, 0.865, 0.865)
    ctf.AddRGBPoint(1.0, 0.706, 0.016, 0.150)

    table_size = 16
    lut = vtkLookupTable()
    lut.SetNumberOfTableValues(table_size)
    lut.Build()

    for i in range(0, table_size):
        rgba = list(ctf.GetColor(float(i) / table_size))
        rgba.append(1)
        lut.SetTableValue(i, rgba)

    return lut


def get_diverging_lut1():
    colors = vtkNamedColors()
    # Colour transfer function.
    ctf = vtkColorTransferFunction()
    ctf.SetColorSpaceToDiverging()
    p1 = [0.0] + list(colors.GetColor3d('MidnightBlue'))
    p2 = [0.5] + list(colors.GetColor3d('Gainsboro'))
    p3 = [1.0] + list(colors.GetColor3d('DarkOrange'))
    ctf.AddRGBPoint(*p1)
    ctf.AddRGBPoint(*p2)
    ctf.AddRGBPoint(*p3)

    table_size = 256
    lut = vtkLookupTable()
    lut.SetNumberOfTableValues(table_size)
    lut.Build()

    for i in range(0, table_size):
        rgba = list(ctf.GetColor(float(i) / table_size))
        rgba.append(1)
        lut.SetTableValue(i, rgba)

    return lut

def MakeScalarBarActor():
    # Create a scalar bar
    scalarbar = vtkScalarBarActor()
    scalarbar.SetObjectName("ScalarAxes")

    scalarbar.SetLookupTable(mesh_mapper.GetLookupTable())
    log("info", f"scalar_range = {mesh_mapper.GetLookupTable().GetTableRange()[0]}")
    #scalar_bar.SetTitle('scalar bar')
    scalarbar.UnconstrainedFontSizeOn()
    scalarbar.SetBarRatio(0.2)
    #scalar_bar.SetNumberOfLabels(5)
    scalarbar.SetMaximumWidthInPixels(100)
    scalarbar.SetMaximumHeightInPixels(600)
    return scalarbar

def MakeScalarBarWidget(scalarbar):
    # create the scalar_bar_widget
    scalarbarwidget = vtkScalarBarWidget()
    scalarbarwidget.SetInteractor(renderWindowInteractor)
    scalarbarwidget.SetScalarBarActor(scalarbar)
    scalarbarwidget.RepositionableOn()
    scalarbarwidget.On()
    return scalarbarwidget