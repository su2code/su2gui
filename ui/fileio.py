# fileio gittree menu

# note that in the main menu, we need to call add the following:
# 1) from ui.fileio import *
# 2) call fileio_card() in SinglePageWithDrawerLayout
# 3) define a node in the gittree (pipeline), note that name in gittree node should be
#    the same as name in ui_card() in fileio_card definition
# 4) define any global state variables that might be needed

# 5) to initialize all fields from the config file, createfunction set_json_fileio()
#    and set all state variables using the json file
# 6) call set_json_fileio() from the main su2gui

# 7) write the results to file in su2_ui.py. Here, we need to construct any 'special' config options
#    that are not simply the output of the json options.

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

# [SOLUTION_FILENAME - text string]
# RESTART_FILENAME - text string
# VOLUME_FILENAME - text string
# [READ_BINARY_RESTART -boolean]
# OUTPUT_WRT_FREQ - integer
# VOLUME_OUTPUT - list of strings
# OUTPUT_FILES - list of strings
# HISTORY_OUTPUT - text string
# HISTORY_WRT_FREQ_INNER integer
# CONV_FILENAME - text string
#
# CONV_FIELD - string
# CONV_RESIDUAL_MINVAL - negative integer
# CONV_STARTITER - integer

# ### READ CONFIG FILE ### #
# set the state variables using the json data from the config file
def set_json_fileio():
  try:
    state.restart_filename = state.jsonData['RESTART_FILENAME']
    # if state.restart_filename.endswith(".dat") or state.restart_filename.endswith(".csv"):
    #    state.restart_filename = state.restart_filename[:-4]
    state.fileio_restart_frequency = state.jsonData['OUTPUT_WRT_FREQ'][0]
    state.fileio_restart_binary = bool('OUTPUT_FILES' in state.jsonData and not "RESTART_ASCII" in  state.jsonData['OUTPUT_FILES'])
    state.fileio_restart_overwrite = bool(state.jsonData['WRT_RESTART_OVERWRITE'])
  except KeyError as e:
    log("warn", f"Key '{e.args[0]}' not found in state.jsonData")
    
  try:
    state.fileio_volume_name = state.jsonData['VOLUME_FILENAME']
    state.fileio_volume_frequency = state.jsonData['OUTPUT_WRT_FREQ'][1]
    state.fileio_volume_overwrite = bool(state.jsonData['WRT_VOLUME_OVERWRITE'])
  except KeyError as e:
    log("warn", f"Key '{e.args[0]}' not found in state.jsonData")
    
  try:
    state.fileio_history_name = state.jsonData['CONV_FILENAME']
    state.fileio_history_frequency = state.jsonData['HISTORY_WRT_FREQ_INNER']
  except KeyError as e:
    log("warn", f"Key '{e.args[0]}' not found in state.jsonData")
    

  state.dirty('restart_filename')
  state.dirty('fileio_restart_frequency')
  state.dirty('fileio_restart_binary')
  state.dirty('fileio_restart_overwrite')
  state.dirty('fileio_volume_name')
  state.dirty('fileio_volume_frequency')
  state.dirty('fileio_volume_overwrite')
  state.dirty('fileio_history_name')
  state.dirty('fileio_history_frequency')

# for the main card, we need to define variables in the UI elements and then create
# a state.change for them
#
###############################################################
# PIPELINE CARD : PHYSICS
###############################################################
def fileio_card():
    with ui_card(title="File I/O", ui_name="File I/O"):
        log("info", "     ## File I/O Selection ##")

        with vuetify.VContainer(fluid=True, classes="pa-1 ma-1"):
          # ####################################################### #
          with vuetify.VRow():
            with vuetify.VCol(cols="4", classes="py-1 pl-0 pr-1"):
               vuetify.VSheet("filename",classes="grey pl-1",rounded=True)
            with vuetify.VCol(cols="3", classes="py-1 px-0"):
               vuetify.VSheet("frequency",classes="grey pl-1",rounded=True)
            with vuetify.VCol(cols="2", classes="py-1 pl-3 pr-1"):
               vuetify.VSheet("binary", classes="grey pl-1",rounded=True)
            with vuetify.VCol(cols="2", classes="py-1 pl-0 pr-0"):
               vuetify.VSheet("overwrite",classes="grey pl-1",rounded=True)

          with vuetify.VRow():
            with vuetify.VCol(cols="4", classes="py-1 pl-0 pr-1"):
              vuetify.VTextField(
                label="Restart",
                v_model=("restart_filename", state.restart_filename),
                outlined=True,
                dense=True,
                hide_details=True,
              )
            with vuetify.VCol(cols="3",classes="py-1 px-0"):
              vuetify.VTextField(
                v_model=("fileio_restart_frequency", 200),
                label="Frequency",
                outlined=True,
                dense=True,
                hide_details=True,
              )
            with vuetify.VCol(cols="2",classes="py-1 pl-4 pr-0"):
              vuetify.VCheckbox(
                v_model=("fileio_restart_binary", False),
                #label="binary",
                outlined=True,
                hide_details=True,
                dense=True,
            )
            with vuetify.VCol(cols="2",classes="py-1 pl-4 pr-0"):
              vuetify.VCheckbox(
                v_model=("fileio_restart_overwrite", False),
                #label="overwrite",
                outlined=True,
                hide_details=True,
                dense=True,
            )


          with vuetify.VRow():
            with vuetify.VCol(cols="4",classes="py-1 pl-0 pr-1"):
              vuetify.VTextField(
                v_model=("fileio_volume_name", "flow"),
                label="Volume output",
                outlined=True,
                dense=True,
                hide_details=True,
              )
            with vuetify.VCol(cols="3",classes="py-1 px-0"):
              vuetify.VTextField(
                v_model=("fileio_volume_frequency", 100),
                label="Frequency",
                outlined=True,
                dense=True,
                hide_details=True,
              )
            #with vuetify.VCol(cols="2",classes="py-1 pl-4 pr-0"):
            #  vuetify.VCheckbox(
            #    v_model=("fileio_volume_binary_idx", False),
            #    #label="binary",
            #    outlined=True,
            #    hide_details=True,
            #    dense=True,
            #)
            with vuetify.VCol(cols="2",offset="2",classes="py-1 pl-4 pr-0"):
              vuetify.VCheckbox(
                v_model=("fileio_volume_overwrite", False),
                #label="overwrite",
                outlined=True,
                hide_details=True,
                dense=True,
            )

          with vuetify.VRow():
            with vuetify.VCol(cols="4",classes="py-1 pl-0 pr-1"):
              vuetify.VTextField(
                v_model=("fileio_history_name", "history"),
                label="History",
                outlined=True,
                dense=True,
                hide_details=True,
              )
            with vuetify.VCol(cols="3",classes="py-1 px-0"):
              vuetify.VTextField(
                v_model=("fileio_history_frequency", 1),
                label="Frequency",
                outlined=True,
                dense=True,
                hide_details=True,
              )
#
@state.change("restart_filename")
def update_material(restart_filename, **kwargs):
    state.jsonData['RESTART_FILENAME']= restart_filename
    state.dirty('fileio_restart_binary')
    state.dirty('jsonData')

# note that we currently support exactly 2 entries in OUTPUT_FILES, restart and paraview
@state.change("fileio_restart_frequency")
def update_material(fileio_restart_frequency, **kwargs):
    if 'OUTPUT_WRT_FREQ' not in state.jsonData:
       state.jsonData['OUTPUT_WRT_FREQ'] = [100, 100]
    try:
      state.jsonData['OUTPUT_WRT_FREQ'][0]= int(fileio_restart_frequency)
      state.dirty('jsonData')
    except Exception as e:
      log("error", f"An error occurred in FileIO Tab: \n {str(e)}")

# if binary, change the file type
@state.change("fileio_restart_binary")
def update_material(fileio_restart_binary, **kwargs):
    if 'OUTPUT_FILES' not in state.jsonData:
       state.jsonData['OUTPUT_FILES'] = ['PARAVIEW', 'SURFACE_PARAVIEW']

    if bool(fileio_restart_binary)==True:
      # change extension to .dat
      state.restart_filename = state.restart_filename.split('.',1)[0]+".dat"

      # changes in config file
      try:
        restart_index = state.jsonData['OUTPUT_FILES'].index("RESTART_ASCII")
        state.jsonData['OUTPUT_FILES'][restart_index]= "RESTART"
      except:
          if "RESTART" not in state.jsonData['OUTPUT_FILES']:
            state.jsonData['OUTPUT_FILES'] += ["RESTART"]
    else:
      # change extension to .csv
      state.restart_filename = state.restart_filename.split('.',1)[0]+".csv"

      # changes is config file
      try:
        restart_index = state.jsonData['OUTPUT_FILES'].index("RESTART")
        state.jsonData['OUTPUT_FILES'][restart_index]= "RESTART_ASCII"
      except:
         if "RESTART_ASCII" not in state.jsonData['OUTPUT_FILES']:
          state.jsonData['OUTPUT_FILES'] += ["RESTART_ASCII"]
    state.dirty('jsonData')

@state.change("fileio_restart_overwrite")
def update_material(fileio_restart_overwrite, **kwargs):
    try:
        state.jsonData['WRT_RESTART_OVERWRITE']= bool(fileio_restart_overwrite)
        state.dirty('jsonData')
    except Exception as e:
      log("error", f"An error occurred in FileIO Tab: \n {str(e)}")

#
@state.change("fileio_volume_name")
def update_material(fileio_volume_name, **kwargs):
    state.jsonData['VOLUME_FILENAME']= fileio_volume_name
    state.dirty('jsonData')

@state.change("fileio_volume_frequency")
def update_material(fileio_volume_frequency, **kwargs):
    try:
        state.jsonData['OUTPUT_WRT_FREQ'][1]= int(fileio_volume_frequency)
        state.dirty('jsonData')
    except Exception as e:
      log("error", f"An error occurred in FileIO Tab: \n {str(e)}")

@state.change("fileio_volume_overwrite")
def update_material(fileio_volume_overwrite, **kwargs):
    try:
        state.jsonData['WRT_VOLUME_OVERWRITE']= bool(fileio_volume_overwrite)
        state.dirty('jsonData')
    except Exception as e:
      log("error", f"An error occurred in FileIO Tab: \n {str(e)}")
# if binary, change the file type
#@state.change("fileio_volume_binary")
#def update_material(fileio_restart_binary, **kwargs):
#    if bool(fileio_restart_binary)==True:
#      state.jsonData['OUTPUT_FILES'][0]= "RESTART"
#    else:
#      state.jsonData['OUTPUT_FILES'][0]= "RESTART_ASCII"
#    state.dirty('jsonData')


#
@state.change("fileio_history_name")
def update_material(fileio_history_name, **kwargs):
    state.jsonData['CONV_FILENAME']= fileio_history_name
    state.dirty('jsonData')

@state.change("fileio_history_frequency")
def update_material(fileio_history_frequency, **kwargs):
    try:
        state.jsonData['HISTORY_WRT_FREQ_INNER']= int(fileio_history_frequency) 
        state.dirty('jsonData')
    except Exception as e:
      log("error", f"An error occurred in FileIO Tab: \n{str(e)}")

