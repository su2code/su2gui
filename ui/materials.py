# materials gittree menu

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
from trame.widgets import markdown
from core.logger import log

state, ctrl = server.state, server.controller

# universal gas constant J/k.mol
UNIVERSAL_GAS_CONSTANT = 8.314

# for dialog cards:
#1. define a boolean to show//hide the dialog
#2. define dialog_card
#3. define an update for the boolean to show/hide the dialog
#4. initialize the dialog by calling it in the singlepagewithdrawerlayout
#5. couple to a button in the main ui dialog

# show the material dialog cards
state.show_materials_dialog_card_fluid = False
state.show_materials_dialog_card_viscosity = False
state.show_materials_dialog_card_heatcapacity = False
state.show_materials_dialog_card_conductivity = False

#label_1 = markdown.Markdown(classes="pa-0 ma-0",content=("var_name", "**formula1 =** $a \\cdot x^2$"))
#label_2 = markdown.Markdown(classes="pa-0 ma-0",content=("var_name", "**formula2 =** $b \\cdot x^2$"))
#content1=("varname","**f=** $a \\cdot x^2$")
# nijso TODO markdown text test #
#mdstring = """
#$a \cdot x^2
#"""
#widget1 = markdown.Markdown(classes="pa-0 ma-0",content=("var_name", "**f=** $a \\cdot x^2$"))
#
#widget2 = "blabla"
############################################################################
# Materials models - list options #
############################################################################

# List: materials model: Fluid model selection
LMaterialsFluidComp= [
  {"text": "Standard Air", "value": 0, "json": "STANDARD_AIR"},
  {"text": "Ideal Gas", "value": 1, "json": "IDEAL_GAS"},
]

LMaterialsFluidIncomp= [
  {"text": "Constant value", "value": 0, "json": "CONSTANT_DENSITY"},
  {"text": "Inc. Ideal Gas", "value": 1, "json": "INC_IDEAL_GAS"},
  {"text": "Polynomial Inc. Ideal Gas", "value": 2, "json": "INC_IDEAL_GAS_POLY"},
]

LMaterialsViscosityComp= [
  {"text": "Constant value", "value": 0, "json": "CONSTANT_VISCOSITY"},
]

LMaterialsViscosityIncomp= [
  {"text": "Constant value", "value": 0, "json": "CONSTANT_VISCOSITY"},
  {"text": "Sutherland", "value": 1, "json": "SUTHERLAND"},
  {"text": "Polynomial mu(T) ", "value": 2, "json": "POLYNOMIAL_VISCOSITY"},
]


# heat capacity has only one option
LMaterialsHeatCapacityConst= [
  {"text": "Constant value", "value": 0},
]

# heat capacity has only one option for cincidealgaspoly
LMaterialsHeatCapacityPoly= [
  {"text": "Polynomial Cp(T)", "value": 0},
]

LMaterialsConductivityIncomp= [
  {"text": "Constant Prandtl", "value": 0, "json": "CONSTANT_PRANDTL"},
  {"text": "Constant value", "value": 1, "json": "CONSTANT_CONDUCTIVITY"},
  {"text": "Polynomial k(T)", "value": 2, "json": "POLYNOMIAL_CONDUCTIVITY"},
]

LMaterialsConductivityComp= [
  {"text": "Constant value", "value": 0, "json": "CONSTANT_CONDUCTIVITY"},
]

# Initialize LMaterialsFluid based on the physics_comp_idx
# This will be properly set when physics is initialized
# LMaterialsFluid will be set based on the physics_comp_idx in the update_material function
# Initially we'll use the incompressible values
state.LMaterialsFluid = LMaterialsFluidIncomp.copy()

# set the state variables using the json data from the config file
def set_json_materials():
  # set density fluid model
  if state.physics_comp_idx:
    if 'FLUID_MODEL' in state.jsonData:
      state.materials_fluid_idx= GetJsonIndex(state.jsonData['FLUID_MODEL'],LMaterialsFluidComp)
    if 'VISCOSITY_MODEL' in state.jsonData:
      state.materials_viscosity_idx= GetJsonIndex(state.jsonData['VISCOSITY_MODEL'],LMaterialsViscosityComp)
    if 'CONDUCTIVITY_MODEL' in state.jsonData:
      state.materials_conductivity_idx= GetJsonIndex(state.jsonData['CONDUCTIVITY_MODEL'],LMaterialsConductivityComp)
  else:
    if 'FLUID_MODEL' in state.jsonData:
      state.materials_fluid_idx= GetJsonIndex(state.jsonData['FLUID_MODEL'],LMaterialsFluidIncomp)
    if 'VISCOSITY_MODEL' in state.jsonData:
      state.materials_viscosity_idx= GetJsonIndex(state.jsonData['VISCOSITY_MODEL'],LMaterialsViscosityIncomp)
    if 'CONDUCTIVITY_MODEL' in state.jsonData:
      state.materials_conductivity_idx= GetJsonIndex(state.jsonData['CONDUCTIVITY_MODEL'],LMaterialsConductivityIncomp)

  if 'INC_DENSITY_INIT' in state.jsonData:
    state.materials_inc_density_init_idx = state.jsonData['INC_DENSITY_INIT']
  if 'INC_TEMPERATURE_INIT' in state.jsonData:
    state.materials_inc_temperature_init_idx = state.jsonData['INC_TEMPERATURE_INIT']
  if 'MOLECULAR_WEIGHT' in state.jsonData:
    state.materials_molecular_weight_idx = state.jsonData['MOLECULAR_WEIGHT']

  # # set fluid viscosity
  if 'MU_CONSTANT' in state.jsonData:
    state.materials_constant_viscosity_idx = state.jsonData['MU_CONSTANT']
  if 'MU_REF' in state.jsonData:
    state.materials_sutherland_muref_idx = state.jsonData['MU_REF']
  if 'MU_T_REF' in state.jsonData:
    state.materials_sutherland_muTref_idx = state.jsonData['MU_T_REF']
  if 'SUTHERLAND_CONSTANT' in state.jsonData:
    state.materials_sutherland_S_idx = state.jsonData['SUTHERLAND_CONSTANT']

  if 'MU_POLYCOEFFS' not in state.jsonData:
      state.jsonData['MU_POLYCOEFFS'] = [0,0,0,0,0]
  state.materials_polynomial_viscosity_a0_idx = state.jsonData['MU_POLYCOEFFS'][0]
  state.materials_polynomial_viscosity_a1_idx = state.jsonData['MU_POLYCOEFFS'][1]
  state.materials_polynomial_viscosity_a2_idx = state.jsonData['MU_POLYCOEFFS'][2]
  state.materials_polynomial_viscosity_a3_idx = state.jsonData['MU_POLYCOEFFS'][3]
  state.materials_polynomial_viscosity_a4_idx = state.jsonData['MU_POLYCOEFFS'][4]

  # # set heat capacity
  if 'SPECIFIC_HEAT_CP' in state.jsonData:
    state.materials_constant_cp_idx = state.jsonData['SPECIFIC_HEAT_CP']

  if 'CP_POLYCOEFFS' in state.jsonData:
    state.materials_polynomial_cp_a0_idx = state.jsonData['CP_POLYCOEFFS'][0]
    state.materials_polynomial_cp_a1_idx = state.jsonData['CP_POLYCOEFFS'][1]
    state.materials_polynomial_cp_a2_idx = state.jsonData['CP_POLYCOEFFS'][2]
    state.materials_polynomial_cp_a3_idx = state.jsonData['CP_POLYCOEFFS'][3]
    state.materials_polynomial_cp_a4_idx = state.jsonData['CP_POLYCOEFFS'][4]

  # # set fluid conductivity
  if 'THERMAL_CONDUCTIVITY_CONSTANT' in state.jsonData:
    state.materials_constant_conductivity_idx = state.jsonData['THERMAL_CONDUCTIVITY_CONSTANT']
  
  if 'PRANDTL_LAM' in state.jsonData:
    state.materials_constant_prandtl_idx = state.jsonData['PRANDTL_LAM']
  
  if 'KT_POLYCOEFFS' in state.jsonData:
    state.materials_polynomial_kt_a0_idx = state.jsonData['KT_POLYCOEFFS'][0]
    state.materials_polynomial_kt_a1_idx = state.jsonData['KT_POLYCOEFFS'][1]
    state.materials_polynomial_kt_a2_idx = state.jsonData['KT_POLYCOEFFS'][2]
    state.materials_polynomial_kt_a3_idx = state.jsonData['KT_POLYCOEFFS'][3]
    state.materials_polynomial_kt_a4_idx = state.jsonData['KT_POLYCOEFFS'][4]

  if 'GAMMA_VALUE' in state.jsonData:
    state.materials_gamma_idx = state.jsonData['GAMMA_VALUE']
  if 'GAS_CONSTANT' in state.jsonData:
     state.materials_gas_constant_idx = state.jsonData['GAS_CONSTANT']

  state.dirty('materials_fluid_idx')
  state.dirty('materials_inc_density_init_idx')
  state.dirty('materials_inc_temperature_init_idx')
  state.dirty('materials_molecular_weight_idx')
  state.dirty('materials_viscosity_idx')
  state.dirty('materials_constant_viscosity_idx')
  state.dirty('materials_sutherland_muref_idx')
  state.dirty('materials_sutherland_muTref_idx')
  state.dirty('materials_sutherland_S_idx')
  state.dirty('materials_polynomial_viscosity_a0_idx')
  state.dirty('materials_polynomial_viscosity_a1_idx')
  state.dirty('materials_polynomial_viscosity_a2_idx')
  state.dirty('materials_polynomial_viscosity_a3_idx')
  state.dirty('materials_polynomial_viscosity_a4_idx')
  state.dirty('materials_constant_cp_idx')
  state.dirty('materials_polynomial_cp_a0_idx')
  state.dirty('materials_polynomial_cp_a1_idx')
  state.dirty('materials_polynomial_cp_a2_idx')
  state.dirty('materials_polynomial_cp_a3_idx')
  state.dirty('materials_polynomial_cp_a4_idx')
  state.dirty('materials_conductivity_idx')
  state.dirty('materials_constant_conductivity_idx')
  state.dirty('materials_constant_prandtl_idx')
  state.dirty('materials_polynomial_kt_a0_idx')
  state.dirty('materials_polynomial_kt_a1_idx')
  state.dirty('materials_polynomial_kt_a2_idx')
  state.dirty('materials_polynomial_kt_a3_idx')
  state.dirty('materials_polynomial_kt_a4_idx')

  state.dirty('materials_gamma_idx')
  state.dirty('materials_gas_constant_idx')
######################################################################
# popup window for fluid model
# for ideal gases, density is computed from P=rho*R*T, and we need the specific gas constant
def materials_dialog_card_fluid():
    with vuetify.VDialog(width=300,position='{X:10,Y:10}',transition="dialog-top-transition",v_model=("show_materials_dialog_card_fluid",False)):
      with vuetify.VCard():


        vuetify.VCardTitle("Fluid Model",
                           classes="grey lighten-1 py-1 grey--text text--darken-3")


        with vuetify.VContainer(fluid=True, v_if=("jsonData['FLUID_MODEL']=='CONSTANT_DENSITY' ")):
          # ####################################################### #
          with vuetify.VRow(classes="py-0 my-0"):
            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                # What to do when something is selected
                v_model=("materials_inc_density_init_idx", 1.2),
                # the name of the list box
                label="Inc. Density",
              )

        # note that for ideal gases, pressure comes from rho_infty*T_infty*R
        # and density comes from P=rho*R*T
        # with R = <R>/M the molecular weight M and universal gas constant <R>
        with vuetify.VContainer(fluid=True, v_if=("jsonData['FLUID_MODEL']=='INC_IDEAL_GAS' ")):
          # ####################################################### #
          with vuetify.VRow(classes="py-0 my-0"):
            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                # What to do when something is selected
                v_model=("materials_inc_density_init_idx", 1.2),
                # the name of the list box
                label="Density (initial)",
              )

          with vuetify.VRow(classes="py-0 my-0"):
            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                # What to do when something is selected
                v_model=("materials_inc_temperature_init_idx", 293.15),
                # the name of the list box
                label="Temperature (initial)",
              )

          with vuetify.VRow(classes="py-0 my-0"):
            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                # What to do when something is selected
                v_model=("materials_molecular_weight_idx", 287.015),
                # the name of the list box
                label="Molecular Weight [g/mol]",
              )

          with vuetify.VRow(classes="py-0 my-0"):
            with vuetify.VCol("Thermodynamic Pressure:",cols="8", classes="py-0 my-0 pr-0 mr-0"):
              vuetify.VTextField(
                # What to do when something is selected
                #v_model=("materials_thermodynamic_pressure_idx", 287.015),
                # the name of the list box
                label=("jsonData['THERMODYNAMIC_PRESSURE']",100000.0),
                disabled=True,
              )

        with vuetify.VContainer(fluid=True, v_if=("jsonData['FLUID_MODEL']=='INC_IDEAL_GAS_POLY' ")):
          # ####################################################### #
          with vuetify.VRow(classes="py-0 my-0"):
            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                # What to do when something is selected
                v_model=("materials_inc_density_init_idx", 1.2),
                # the name of the list box
                label="density (initial)",
              )

          with vuetify.VRow(classes="py-0 my-0"):
            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                # What to do when something is selected
                v_model=("materials_inc_temperature_init_idx", 293.15),
                # the name of the list box
                label="Temperature (initial)",
              )

          with vuetify.VRow(classes="py-0 my-0"):
            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                # What to do when something is selected
                v_model=("materials_molecular_weight_idx", 287.015),
                # the name of the list box
                label="Molecular Weight [g/mol]",
              )

          with vuetify.VRow(classes="py-0 my-0"):
            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                # What to do when something is selected
                #v_model=("materials_thermodynamic_pressure_idx", 287.015),
                # the name of the list box
                label=("jsonData['THERMODYNAMIC_PRESSURE']",100000.0),
                disabled=True,
              )

        # note that for ideal gases, pressure comes from rho_infty*T_infty*R
        # and density comes from P=rho*R*T
        # with R = <R>/M the molecular weight M and universal gas constant <R>
        with vuetify.VContainer(fluid=True, v_if=("jsonData['FLUID_MODEL']=='STANDARD_AIR' ")):
          # ####################################################### #
          with vuetify.VRow(classes="py-0 my-0"):
            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                # What to do when something is selected
                #v_model=("materials_inc_density_init_idx", 1.2),
                # the name of the list box
                label="Gas Constant: 287.058 [J/kg.K]",
              )

          with vuetify.VRow(classes="py-0 my-0"):
            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                # What to do when something is selected
                #v_model=("materials_inc_temperature_init_idx", 293.15),
                # the name of the list box
                label="Gamma: 1.4 [-]",
              )

        with vuetify.VContainer(fluid=True, v_if=("jsonData['FLUID_MODEL']=='IDEAL_GAS' ")):
          # ####################################################### #
          with vuetify.VRow(classes="py-0 my-0"):
            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                # What to do when something is selected
                v_model=("materials_gamma_idx", 1.4),
                # the name of the list box
                label="Gamma",
              )

          with vuetify.VRow(classes="py-0 my-0"):
            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                # What to do when something is selected
                v_model=("materials_gas_constant_idx", 287.15),
                # the name of the list box
                label="Specific gas constant [J/kg.K]",
              )

        with vuetify.VCardText():
          vuetify.VBtn("close", click=update_materials_dialog_card_fluid)


def update_materials_dialog_card_fluid():
    state.show_materials_dialog_card_fluid = not state.show_materials_dialog_card_fluid
    log("info", f"Fluid model dialog state changed to: {state.show_materials_dialog_card_fluid}")

#####################################################################
def materials_dialog_card_viscosity():
    with vuetify.VDialog(width=300,position='{X:10,Y:10}',transition="dialog-top-transition",v_model=("show_materials_dialog_card_viscosity",False)):
      with vuetify.VCard():
        # UI Component
        vuetify.VCardTitle("viscosity [N.s/m^2]",
                           classes="grey lighten-1 py-1 grey--text text--darken-3")


        with vuetify.VContainer(fluid=True,v_if=("jsonData['VISCOSITY_MODEL']=='CONSTANT_VISCOSITY' ")):
          # ####################################################### #
          with vuetify.VRow(classes="py-0 my-0"):

            # TODO: example markdown to be tested further
            #with vuetify.VCol(cols="12", classes="py-1 my-1 pr-0 mr-0"):
            #  vuetify.VTextField(
            #    label=(markdown.Markdown(content=content1))
            #  )

            with vuetify.VCol(cols="10", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                # What to do when something is selected
                v_model=("materials_constant_viscosity_idx", 1.18e-5),
                # the name of the list box
                label="viscosity",
                outlined=True,
              )


        # ### option Sutherland viscosity
        with vuetify.VContainer(fluid=True,v_if=("jsonData['VISCOSITY_MODEL']=='SUTHERLAND' "),):
          # ####################################################### #
          with vuetify.VRow(classes="py-0 my-0"):
            with vuetify.VCol(cols="12", classes="py-1 my-1 pr-0 mr-0"):

              vuetify.VTextField(
                 label=("jsonData['VISCOSITY_MODEL']","none"),
                 outlined=True,
                 )

            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0", ):
              vuetify.VTextField(
                v_model=("materials_sutherland_muref_idx", 1.18e-5),
                 label="Reference viscosity mu_ref [kg/m.s]",
                 outlined=True,
                 )

            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                v_model=("materials_sutherland_muTref_idx", 273.15),
                 label="Reference Temperature mu_T_ref [K]",
                 outlined=True,
                 )

            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                v_model=("materials_sutherland_S_idx", 110.4),
                 label="Sutherland constant [K]",
                 outlined=True,
                 )

        # ### option polynomial viscosity
        with vuetify.VContainer(fluid=True,v_if=("jsonData['VISCOSITY_MODEL']=='POLYNOMIAL_VISCOSITY' "),):
          # ####################################################### #
          with vuetify.VRow(classes="py-0 my-0"):
            with vuetify.VCol(cols="12", classes="py-1 my-1 pr-0 mr-0"):

              vuetify.VTextField(
                 label=("jsonData['VISCOSITY_MODEL']","none")
                 )

            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                v_model=("materials_polynomial_viscosity_a0_idx", 1.2e-5),
                 label="a0",
                 outlined=True,
                 )

            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                v_model=("materials_polynomial_viscosity_a1_idx", 0),
                 label="a1",
                 outlined=True,
                 )

            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                v_model=("materials_polynomial_viscosity_a2_idx", 0),
                 label="a2",
                 outlined=True,
                 )
            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                v_model=("materials_polynomial_viscosity_a3_idx", 0),
                 label="a3",
                 outlined=True,
                 )
            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                v_model=("materials_polynomial_viscosity_a4_idx", 0),
                 label="a4",
                 outlined=True,
                 )

        with vuetify.VCardText():
          vuetify.VBtn("close", click=update_materials_dialog_card_viscosity)


def update_materials_dialog_card_viscosity():
    state.show_materials_dialog_card_viscosity = not state.show_materials_dialog_card_viscosity
    log("info", f"Viscosity model dialog state changed to: {state.show_materials_dialog_card_viscosity}")



#####################################################################
def materials_dialog_card_cp():
    with vuetify.VDialog(width=300,position='{X:10,Y:10}',transition="dialog-top-transition",v_model=("show_materials_dialog_card_cp",False)):
      with vuetify.VCard():
        # UI Component
        vuetify.VCardTitle("heat capacity",
                           classes="grey lighten-1 py-1 grey--text text--darken-3")


        # ### option polynomial viscosity
        with vuetify.VContainer(fluid=True,v_if=("jsonData['FLUID_MODEL']=='INC_IDEAL_GAS_POLY' "),):
          # ####################################################### #
          with vuetify.VRow(classes="py-0 my-0"):
            with vuetify.VCol(cols="12", classes="py-1 my-1 pr-0 mr-0"):

              vuetify.VTextField(
                 label=("jsonData['VISCOSITY_MODEL']","none")
                 )

            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                v_model=("materials_polynomial_cp_a0_idx", 1.2e-5),
                 label="a0",
                 outlined=True,
                 )

            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                v_model=("materials_polynomial_cp_a1_idx", 0),
                 label="a1",
                 outlined=True,
                 )

            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                v_model=("materials_polynomial_cp_a2_idx", 0),
                 label="a2",
                 outlined=True,
                 )
            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                v_model=("materials_polynomial_cp_a3_idx", 0),
                 label="a3",
                 outlined=True,
                 )
            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                v_model=("materials_polynomial_cp_a4_idx", 0),
                 label="a4",
                 outlined=True,
                 )

        #with vuetify.VContainer(fluid=True,v_if=("jsonData['FLUID_MODEL']=='CONSTANT_DENSITY' ")):
        with vuetify.VContainer(fluid=True,v_else=True):
          # ####################################################### #
          with vuetify.VRow(classes="py-0 my-0"):

            with vuetify.VCol(cols="10", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                # What to do when something is selected
                v_model=("materials_constant_cp_idx", 1.18e-5),
                # the name of the list box
                label="cp",
                outlined=True,
              )
        with vuetify.VCardText():
          vuetify.VBtn("close", click=update_materials_dialog_card_cp)


def update_materials_dialog_card_cp():
    state.show_materials_dialog_card_cp = not state.show_materials_dialog_card_cp
    log("info", f"Heat capacity dialog state changed to: {state.show_materials_dialog_card_cp}")




#####################################################################
def materials_dialog_card_conductivity():
    with vuetify.VDialog(width=300,position='{X:10,Y:10}',transition="dialog-top-transition",v_model=("show_materials_dialog_card_conductivity",False)):

      with vuetify.VCard():
        vuetify.VCardTitle("thermal conductivity [W/m.K]",
                           classes="grey lighten-1 py-1 grey--text text--darken-3")

        with vuetify.VContainer(fluid=True,v_if=("jsonData['CONDUCTIVITY_MODEL']=='CONSTANT_CONDUCTIVITY'"),):
          # ####################################################### #
          with vuetify.VRow(classes="py-0 my-0"):
            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                # What to do when something is selected
                v_model=("materials_constant_conductivity_idx", 1005.0),
                # the name of the list box
                label="thermal conductivity",
              )

        with vuetify.VContainer(fluid=True,v_if=("jsonData['CONDUCTIVITY_MODEL']=='CONSTANT_PRANDTL'"),):
          # ####################################################### #
          with vuetify.VRow(classes="py-0 my-0"):
            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                # What to do when something is selected
                v_model=("materials_constant_prandtl_idx", 1.0),
                # the name of the list box
                label="Laminar Prandtl number",
              )

        with vuetify.VContainer(fluid=True,v_if=("jsonData['CONDUCTIVITY_MODEL']=='POLYNOMIAL_CONDUCTIVITY'"),):
          # ####################################################### #
          with vuetify.VRow(classes="py-0 my-0"):

            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                v_model=("materials_polynomial_kt_a0_idx", 1.2e-5),
                 label="a0",
                 outlined=True,
                 )

            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                v_model=("materials_polynomial_kt_a1_idx", 0),
                 label="a1",
                 outlined=True,
                 )

            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                v_model=("materials_polynomial_kt_a2_idx", 0),
                 label="a2",
                 outlined=True,
                 )
            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                v_model=("materials_polynomial_kt_a3_idx", 0),
                 label="a3",
                 outlined=True,
                 )
            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VTextField(
                v_model=("materials_polynomial_kt_a4_idx", 0),
                 label="a4",
                 outlined=True,
                 )

        with vuetify.VCardText():
          vuetify.VBtn("close", click=update_materials_dialog_card_conductivity)


def update_materials_dialog_card_conductivity():
    state.show_materials_dialog_card_conductivity = not state.show_materials_dialog_card_conductivity
    log("info", f"Thermal conductivity dialog state changed to: {state.show_materials_dialog_card_conductivity}")





###############################################################
# PIPELINE CARD : Materials
###############################################################
def materials_card():
    with ui_card(title="Materials", ui_name="Materials"):
        log("info", "## Materials Selection ##")

        # 1 row of option lists

        with vuetify.VContainer(fluid=True):
          # ####################################################### #
          with vuetify.VRow(classes="py-0 my-0"):
            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              # Then a list selection for turbulence submodels
              vuetify.VSelect(
                # What to do when something is selected
                v_model=("materials_fluid_idx", 0),
                # The items in the list
                items=("Object.values(LMaterialsFluid)",),
                # the name of the list box
                label="Fluid density",
                hide_details=True,
                dense=True,
                outlined=True,
                classes="py-0 my-0",
            )
            with vuetify.VCol(cols="4", classes="py-0 my-0"):
              with vuetify.VBtn(classes="mx-0 py-0 mt-2 mb-0",elevation=1,variant="text",color="white", click=update_materials_dialog_card_fluid, icon="mdi-dots-vertical"):
                vuetify.VIcon("mdi-dots-vertical",density="compact",color="green")


          # ####################################################### #
          with vuetify.VRow(classes="py-0 my-0"):
            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VSelect(
                # What to do when something is selected
                v_model=("materials_viscosity_idx", 0),
                # The items in the list
                items=("Object.values(LMaterialsViscosity)",),
                # the name of the list box
                label="Fluid viscosity",
                hide_details=True,
                dense=True,
                outlined=True,
                classes="py-0 my-0",
              )
            with vuetify.VCol(cols="4", classes="py-0 my-0"):
              with vuetify.VBtn(classes="mx-0 py-0 mt-2 mb-0",elevation=1,variant="text",color="white", click=update_materials_dialog_card_viscosity, icon="mdi-dots-vertical"):
                vuetify.VIcon("mdi-dots-vertical",density="compact",color="green")

          # ####################################################### #
          with vuetify.VRow(classes="py-0 my-0"):
            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VSelect(
                # What to do when something is selected
                v_model=("materials_heatcapacity_idx", 0),
                # The items in the list
                #items=("representations_heatcapacity",LMaterialsHeatCapacity),
                items=("Object.values(LMaterialsHeatCapacity)",),
                # the name of the list box
                label="Fluid heat capacity",
                hide_details=True,
                dense=True,
                outlined=True,
                classes="py-0 my-0",
              )
            with vuetify.VCol(cols="4", classes="py-0 my-0"):
              with vuetify.VBtn(classes="mx-0 py-0 mt-2 mb-0",elevation=1,variant="text",color="white", click=update_materials_dialog_card_cp, icon="mdi-dots-vertical"):
                vuetify.VIcon("mdi-dots-vertical",density="compact",color="green")

          # ####################################################### #
          with vuetify.VRow(classes="py-0 my-0"):
            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              # conductivity should be off when incompressible + energy=off
              vuetify.VSelect(
                # What to do when something is selected
                v_model=("materials_conductivity_idx", 0),
                # The items in the list
                #items=("representations_conductivity",LMaterialsConductivity),
                items=("Object.values(LMaterialsConductivity)",),
                # the name of the list box
                label="Fluid conductivity",
                # note that when jsonData changes, it needs to be updated using state.dirty
                disabled=("jsonData['INC_ENERGY_EQUATION']==0",0),
                hide_details=True,
                dense=True,
                outlined=True,
                # bottom margin larger
                classes="py-0 my-0",
              )
            with vuetify.VCol(cols="4", classes="py-0 my-0"):
              with vuetify.VBtn(classes="mx-0 py-0 mt-2 mb-0",
                                elevation=1,
                                variant="text",
                                color="white",
                                click=update_materials_dialog_card_conductivity,
                                disabled=("jsonData['INC_ENERGY_EQUATION']==0",0),
                                icon="mdi-dots-vertical"):
                vuetify.VIcon("mdi-dots-vertical",density="compact",color="green")

###############################################################
# Materials - fluid model options
###############################################################
@state.change("materials_fluid_idx")
def update_material(materials_fluid_idx, **kwargs):
    log("info", f"fluid model selection:  = {materials_fluid_idx}")
    log("info", f"parent ui =  = {state.active_ui}")

    # note that fluid model determines Cp
    # Cp is constant, except when fluid model is CIncIdealGasPoly
    # update config option value
    state.jsonData['FLUID_MODEL']= GetJsonName(materials_fluid_idx,state.LMaterialsFluid)
    if (state.jsonData['FLUID_MODEL'] == "INC_IDEAL_GAS_POLY"):
       state.LMaterialsHeatCapacity = LMaterialsHeatCapacityPoly
    else:
       state.LMaterialsHeatCapacity = LMaterialsHeatCapacityConst

    # for incompressible, constant density, we set the inc_density_model
    if (state.jsonData['FLUID_MODEL'] == "CONSTANT_DENSITY"):
      state.jsonData['INC_DENSITY_MODEL']= 'CONSTANT'
    elif (state.jsonData['FLUID_MODEL'] in ['INC_IDEAL_GAS','INC_IDEAL_GAS_POLY']):
      state.jsonData['INC_DENSITY_MODEL']= 'VARIABLE'

    state.dirty('jsonData')



@state.change("materials_heatcapacity_idx")
def update_material(materials_heatcapacity_idx, **kwargs):
    log("info", f"fluid heat capacity model selection:  = {materials_heatcapacity_idx}")
    # only set it if the parent is Materials

    # update config option value
    # <> no config option exists for heat capacity
    state.dirty('jsonData')


@state.change("materials_viscosity_idx")
def update_material(materials_viscosity_idx, **kwargs):
    log("info", f"fluid viscosity model selection:  = {materials_viscosity_idx}")
    # only set it if the parent is Materials
    #if state.active_ui=="Materials":
    #  state.active_sub_ui = "submaterials_viscosity"

    # update config option value
    state.jsonData['VISCOSITY_MODEL']= GetJsonName(materials_viscosity_idx,state.LMaterialsViscosity)
    log("info", f"state.jsonData= = {state.jsonData['VISCOSITY_MODEL']}")
    state.dirty('jsonData')


@state.change("materials_conductivity_idx")
def update_material(materials_conductivity_idx, **kwargs):
    log("info", f"fluid conductivity model selection:  = {materials_conductivity_idx}")
    # only set it if the parent is Materials
    #if state.active_ui=="Materials":
    #  state.active_sub_ui = "submaterials_conductivity"

    # update config option value
    state.jsonData['CONDUCTIVITY_MODEL']= GetJsonName(materials_conductivity_idx,state.LMaterialsConductivity)

    if ('FLUID_MODEL' in state.jsonData and state.jsonData['FLUID_MODEL'] in ('STANDARD_AIR', 'IDEAL_GAS')):
        state.jsonData['CONDUCTIVITY_MODEL'] = 'CONSTANT_PRANDTL'
        state.materials_conductivity_idx = 1
    state.dirty('jsonData')

###############################################################
# PIPELINE SUBCARD : MATERIALS
###############################################################

def computePressure():
  #update thermodynamic pressure for displaying in the dialog
  try:
    rho = float(state.jsonData['INC_DENSITY_INIT'])
    T = float(state.jsonData['INC_TEMPERATURE_INIT'])
    M = float(state.jsonData['MOLECULAR_WEIGHT'])
    R = float(UNIVERSAL_GAS_CONSTANT / (M/1000.0))

    state.jsonData['THERMODYNAMIC_PRESSURE']= round(rho*R*T,2)
  except Exception as e:
    log("warn",f'Unable to set THERMODYNAMIC_PRESSURE due to incorrect value for {e} in Materials Tab')

###############################################################
# Materials - fluid model options
###############################################################
# fluid_model = constant density model
# the density is set to the freestream density
# cp = cv = SPECIFIC_HEAT_CP
@state.change("materials_inc_density_init_idx")
def update_material(materials_inc_density_init_idx, **kwargs):
    log("info", f"fluid density model selection:  = {materials_inc_density_init_idx}")
    log("info", f"parent ui =  = {state.active_ui}")
    # only set it if the parent is Materials
    #if state.active_ui=="Materials":
    #  state.active_sub_ui = "submaterials_fluid"

    # update config option value, note that density comes from freestream density
    state.jsonData['INC_DENSITY_INIT']= materials_inc_density_init_idx

    computePressure()
    state.dirty('jsonData')


@state.change("materials_inc_temperature_init_idx")
def update_material(materials_inc_temperature_init_idx, **kwargs):
    log("info", f"fluid density model selection:  = {materials_inc_temperature_init_idx}")
    log("info", f"parent ui =  = {state.active_ui}")
    # only set it if the parent is Materials
    #if state.active_ui=="Materials":
    #  state.active_sub_ui = "submaterials_fluid"

    # update config option value, note that density comes from freestream density
    state.jsonData['INC_TEMPERATURE_INIT']= materials_inc_temperature_init_idx

    computePressure()
    state.dirty('jsonData')


@state.change("materials_molecular_weight_idx")
def update_material(materials_molecular_weight_idx, **kwargs):
    log("info", f"fluid density model selection:  = {materials_molecular_weight_idx}")
    log("info", f"parent ui =  = {state.active_ui}")
    # only set it if the parent is Materials

    # update config option value
    state.jsonData['MOLECULAR_WEIGHT']= materials_molecular_weight_idx

    computePressure()
    state.dirty('jsonData')


# constant viscosity model
@state.change("materials_constant_viscosity_idx")
def update_material(materials_constant_viscosity_idx, **kwargs):
    log("info", f"constant viscosity value:  = {materials_constant_viscosity_idx}")
    # update config option value
    state.jsonData['MU_CONSTANT']= materials_constant_viscosity_idx

# constant cp
@state.change("materials_constant_cp_idx")
def update_material(materials_constant_cp_idx, **kwargs):
    log("info", f"constant cp value:  = {materials_constant_cp_idx}")
    # update config option value
    state.jsonData['SPECIFIC_HEAT_CP']= materials_constant_cp_idx

# constant conductivity model
@state.change("materials_constant_conductivity_idx")
def update_material(materials_constant_conductivity_idx, **kwargs):
    log("info", f"constant conductivity value:  = {materials_constant_conductivity_idx}")
    # update config option value
    state.jsonData['THERMAL_CONDUCTIVITY_CONSTANT']= materials_constant_conductivity_idx

# Constant Prandtl conductivity model
@state.change("materials_constant_prandtl_idx")
def update_material(materials_constant_prandtl_idx, **kwargs):
    log("info", f"constant prandtl value:  = {materials_constant_prandtl_idx}")
    # update config option value
    state.jsonData['PRANDTL_LAM']= materials_constant_prandtl_idx

# Sutherland viscosity model
@state.change("materials_sutherland_muref_idx")
def update_material(materials_sutherland_muref_idx, **kwargs):
    log("info", f"Sutherland viscosity mu_ref value:  = {materials_sutherland_muref_idx}")
    # update config option value
    state.jsonData['MU_REF']= materials_sutherland_muref_idx

# Sutherland viscosity model
@state.change("materials_sutherland_muTref_idx")
def update_material(materials_sutherland_muTref_idx, **kwargs):
    log("info", f"Sutherland viscosity mu_T_ref value:  = {materials_sutherland_muTref_idx}")
    # update config option value
    state.jsonData['MU_T_REF']= materials_sutherland_muTref_idx

# Sutherland viscosity model
@state.change("materials_sutherland_S_idx")
def update_material(materials_sutherland_S_idx, **kwargs):
    log("info", f"Sutherland viscosity S value:  = {materials_sutherland_S_idx}")
    # update config option value
    state.jsonData['SUTHERLAND_CONSTANT']= materials_sutherland_S_idx

# Polynomial viscosity model
@state.change("materials_polynomial_viscosity_a0_idx")
def update_material(materials_polynomial_viscosity_a0_idx, **kwargs):
    log("info", f"Polynomial viscosity a0 value:  = {materials_polynomial_viscosity_a0_idx}")
    # update config option value
    
    if 'MU_POLYCOEFFS' not in state.jsonData:
      state.jsonData['MU_POLYCOEFFS'] = [0,0,0,0,0]
    state.jsonData['MU_POLYCOEFFS'][0]= materials_polynomial_viscosity_a0_idx

# Polynomial viscosity model
@state.change("materials_polynomial_viscosity_a1_idx")
def update_material(materials_polynomial_viscosity_a1_idx, **kwargs):
    log("info", f"Polynomial viscosity a1 value:  = {materials_polynomial_viscosity_a1_idx}")
    # update config option value
    
    if 'MU_POLYCOEFFS' not in state.jsonData:
      state.jsonData['MU_POLYCOEFFS'] = [0,0,0,0,0]
    state.jsonData['MU_POLYCOEFFS'][1]= materials_polynomial_viscosity_a1_idx

# Polynomial viscosity model
@state.change("materials_polynomial_viscosity_a2_idx")
def update_material(materials_polynomial_viscosity_a2_idx, **kwargs):
    log("info", f"Polynomial viscosity a2 value:  = {materials_polynomial_viscosity_a2_idx}")
    # update config option value
    
    if 'MU_POLYCOEFFS' not in state.jsonData:
      state.jsonData['MU_POLYCOEFFS'] = [0,0,0,0,0]
    state.jsonData['MU_POLYCOEFFS'][2]= materials_polynomial_viscosity_a2_idx

# Polynomial viscosity model
@state.change("materials_polynomial_viscosity_a3_idx")
def update_material(materials_polynomial_viscosity_a3_idx, **kwargs):
    log("info", f"Polynomial viscosity a3 value:  = {materials_polynomial_viscosity_a3_idx}")
    # update config option value
    
    if 'MU_POLYCOEFFS' not in state.jsonData:
      state.jsonData['MU_POLYCOEFFS'] = [0,0,0,0,0]
    state.jsonData['MU_POLYCOEFFS'][3]= materials_polynomial_viscosity_a3_idx

# Polynomial viscosity model
@state.change("materials_polynomial_viscosity_a4_idx")
def update_material(materials_polynomial_viscosity_a4_idx, **kwargs):
    log("info", f"Polynomial viscosity a4 value:  = {materials_polynomial_viscosity_a4_idx}")
    # update config option value
    
    if 'MU_POLYCOEFFS' not in state.jsonData:
      state.jsonData['MU_POLYCOEFFS'] = [0,0,0,0,0]
    state.jsonData['MU_POLYCOEFFS'][4]= materials_polynomial_viscosity_a4_idx


# Polynomial cp model
@state.change("materials_polynomial_cp_a0_idx")
def update_material(materials_polynomial_cp_a0_idx, **kwargs):
    log("info", f"Polynomial cp a0 value:  = {materials_polynomial_cp_a0_idx}")
    # update config option value
    
    if 'CP_POLYCOEFFS' not in state.jsonData:
      state.jsonData['CP_POLYCOEFFS'] = [0,0,0,0,0]
    state.jsonData['CP_POLYCOEFFS'][0]= materials_polynomial_cp_a0_idx

# Polynomial cp model
@state.change("materials_polynomial_cp_a1_idx")
def update_material(materials_polynomial_cp_a1_idx, **kwargs):
    log("info", f"Polynomial cp a1 value:  = {materials_polynomial_cp_a1_idx}")
    # update config option value
    
    if 'CP_POLYCOEFFS' not in state.jsonData:
      state.jsonData['CP_POLYCOEFFS'] = [0,0,0,0,0]
    state.jsonData['CP_POLYCOEFFS'][1]= materials_polynomial_cp_a1_idx

# Polynomial cp model
@state.change("materials_polynomial_cp_a2_idx")
def update_material(materials_polynomial_cp_a2_idx, **kwargs):
    log("info", f"Polynomial cp a2 value:  = {materials_polynomial_cp_a2_idx}")
    # update config option value
    
    if 'CP_POLYCOEFFS' not in state.jsonData:
      state.jsonData['CP_POLYCOEFFS'] = [0,0,0,0,0]
    state.jsonData['CP_POLYCOEFFS'][2]= materials_polynomial_cp_a2_idx

# Polynomial cp model
@state.change("materials_polynomial_cp_a3_idx")
def update_material(materials_polynomial_cp_a3_idx, **kwargs):
    log("info", f"Polynomial cp a3 value:  = {materials_polynomial_cp_a3_idx}")
    # update config option value
    
    if 'CP_POLYCOEFFS' not in state.jsonData:
      state.jsonData['CP_POLYCOEFFS'] = [0,0,0,0,0]
    state.jsonData['CP_POLYCOEFFS'][3]= materials_polynomial_cp_a3_idx

# Polynomial cp model
@state.change("materials_polynomial_cp_a4_idx")
def update_material(materials_polynomial_cp_a4_idx, **kwargs):
    log("info", f"Polynomial cp a4 value:  = {materials_polynomial_cp_a4_idx}")
    # update config option value
    
    if 'CP_POLYCOEFFS' not in state.jsonData:
      state.jsonData['CP_POLYCOEFFS'] = [0,0,0,0,0]
    state.jsonData['CP_POLYCOEFFS'][4]= materials_polynomial_cp_a4_idx



# Polynomial kt model
@state.change("materials_polynomial_kt_a0_idx")
def update_material(materials_polynomial_kt_a0_idx, **kwargs):
    log("info", f"Polynomial kt a0 value:  = {materials_polynomial_kt_a0_idx}")
    # update config option value
    if 'KT_POLYCOEFFS' not in state.jsonData:
      state.jsonData['KT_POLYCOEFFS'] = [0,0,0,0,0]
    state.jsonData['KT_POLYCOEFFS'][0]= materials_polynomial_kt_a0_idx

# Polynomial kt model
@state.change("materials_polynomial_kt_a1_idx")
def update_material(materials_polynomial_kt_a1_idx, **kwargs):
    log("info", f"Polynomial kt a1 value:  = {materials_polynomial_kt_a1_idx}")
    # update config option value
    
    if 'KT_POLYCOEFFS' not in state.jsonData:
      state.jsonData['KT_POLYCOEFFS'] = [0,0,0,0,0]
    state.jsonData['KT_POLYCOEFFS'][1]= materials_polynomial_kt_a1_idx

# Polynomial kt model
@state.change("materials_polynomial_kt_a2_idx")
def update_material(materials_polynomial_kt_a2_idx, **kwargs):
    log("info", f"Polynomial kt a2 value:  = {materials_polynomial_kt_a2_idx}")
    # update config option value
    
    if 'KT_POLYCOEFFS' not in state.jsonData:
      state.jsonData['KT_POLYCOEFFS'] = [0,0,0,0,0]
    state.jsonData['KT_POLYCOEFFS'][2]= materials_polynomial_kt_a2_idx

# Polynomial kt model
@state.change("materials_polynomial_kt_a3_idx")
def update_material(materials_polynomial_kt_a3_idx, **kwargs):
    log("info", f"Polynomial kt a3 value:  = {materials_polynomial_kt_a3_idx}")
    # update config option value
    
    if 'KT_POLYCOEFFS' not in state.jsonData:
      state.jsonData['KT_POLYCOEFFS'] = [0,0,0,0,0]
    state.jsonData['KT_POLYCOEFFS'][3]= materials_polynomial_kt_a3_idx

# Polynomial kt model
@state.change("materials_polynomial_kt_a4_idx")
def update_material(materials_polynomial_kt_a4_idx, **kwargs):
    log("info", f"Polynomial kt a4 value:  = {materials_polynomial_kt_a4_idx}")
    # update config option value
    
    if 'KT_POLYCOEFFS' not in state.jsonData:
      state.jsonData['KT_POLYCOEFFS'] = [0,0,0,0,0]
    state.jsonData['KT_POLYCOEFFS'][4]= materials_polynomial_kt_a4_idx

# compressible gamma
@state.change("materials_gamma_idx")
def update_material(materials_gamma_idx, **kwargs):
    log("info", f"gamma value:  = {materials_gamma_idx}")
    # update config option value
    state.jsonData['GAMMA_VALUE']= materials_gamma_idx

# compressible specific gas constant
@state.change("materials_gas_constant_idx")
def update_material(materials_gas_constant_idx, **kwargs):
    log("info", f"gamma value:  = {materials_gas_constant_idx}")
    # update config option value
    state.jsonData['GAS_CONSTANT']= materials_gas_constant_idx