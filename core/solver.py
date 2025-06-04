# solver gittree menu

# note that in the main menu, we need to call add the following:
# 1) from core.solver import *
# 2) call solver_card() in SinglePageWithDrawerLayout
# 3) define a node in the gittree (pipeline)
# 4) define any global state variables that might be needed

import sys
import os
import shutil
from pathlib import Path

# Add parent directory to path to allow importing from sibling directories
parent_dir = str(Path(__file__).parent.parent.absolute())
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from ui.uicard import ui_card, ui_subcard, server
from trame.widgets import vuetify
from core.su2_json import *
from core.su2_io import save_su2mesh, save_json_cfg_file

# check if a file is opened by another process
#import psutil

import pandas as pd
from base64 import b64decode
import subprocess, io, struct, os

# real-time update, asynchronous io
import asyncio
from trame.app import get_server, asynchronous

from trame.app.file_upload import ClientFile

import vtk
from vtkmodules.vtkCommonDataModel import vtkDataObject

# import the grid from the mesh module
from ui.mesh import *
from ui.vtk_helper import *

# Logging function
from core.logger import log, update_su2_logs

# matplotlib
import matplotlib
matplotlib.use("agg")
import matplotlib.pyplot as plt
from trame.widgets import matplotlib as tramematplotlib

# line 'i' has fixed color so the color does not change if a line is deselected
mplColorList=['blue','orange','red','green','purple','brown','pink','gray','olive','cyan',
              'black','gold','yellow','springgreen','thistle','beige','coral','navy','salmon','lightsteelblue']



state, ctrl = server.state, server.controller
############################################################################
# Solver models - list options #
############################################################################

# the main su2 solver process
proc_SU2 = None

# list of fields that we could check for convergence
state.convergence_fields=[]
state.convergence_fields_range=[]
# list of booleans stating which of the fields need to be
# included in the convergence criteria
state.convergence_fields_visibility=[]

# global iteration number while running a case
state.global_iter = -1

# initialize from json file
def set_json_solver():
    if 'ITER' in state.jsonData:
        state.iter_idx = state.jsonData['ITER']
        state.dirty('iter_idx')
    if 'CONV_RESIDUAL_MINVAL' in state.jsonData:
        state.convergence_val = state.jsonData['CONV_RESIDUAL_MINVAL']
        state.dirty('convergence_val')
    if 'CONV_FIELD' in state.jsonData:
        state.convergence_fields = state.jsonData['CONV_FIELD']
        log("info", f"state convergence fields =  = {state.convergence_fields} {type(state.convergence_fields)}")


# matplotlib
state.active_figure="mpl_plot_history"
state.graph_update=True
@state.change("active_figure", "figure_size", "countdown","monitorLinesVisibility")
def update_chart(active_figure, **kwargs):
    log("info", "updating figure 1")
    ctrl.update_figure(globals()[active_figure]())
    #ctrl.update_figure2(globals()[active_figure]())

#matplotlib
def update_visibility(index, visibility):
    log("info", f"monitorLinesVisibility =  = {state.monitorLinesVisibility}")
    state.monitorLinesVisibility[index] = visibility
    log("info", f"monitorLinesVisibility =  = {state.monitorLinesVisibility}")
    state.dirty("monitorLinesVisibility")
    log("info", f"Toggle {index} to {visibility}")
    log("info", f"monitorLinesVisibility =  = {state.monitorLinesVisibility}")

#matplotlib
def dialog_card():
    log("info", f"dialog card, lines= = {state.monitorLinesNames}")
    # show_dialog2 determines if the entire dialog is shown or not
    with vuetify.VDialog(width=200,position='{X:10,Y:10}',transition="dialog-top-transition",v_model=("show_dialog",False)):
      #with vuetify.VCard(color="light-gray"):
      with vuetify.VCard():
        vuetify.VCardTitle("Line visibility", classes="grey lighten-1 grey--text text--darken-3")

        #with vuetify.VListGroup(value=("true",), sub_group=True):
        #    with vuetify.Template(v_slot_activator=True):
        #            vuetify.VListItemTitle("Bars")
        #    with vuetify.VListItemContent():
        #            #with vuetify.VListItem(v_for="id in monitorLinesRange", key="id"):
        vuetify.VCheckbox(
                              # loop over list monitorLinesRange
                              v_for="id in monitorLinesRange",
                              key="id",
                              # checkbox changes the state of monitorLinesVisibility[id]
                              v_model=("monitorLinesVisibility[id]",),
                              # name of the checkbox
                              label=("`label= ${ monitorLinesNames[id] }`",),
                              # on each change, immediately go to update_visibility
                              change=(update_visibility,"[id, $event]"),
                              classes="mt-1 pt-1",
                              hide_details=True,
                              dense=True,
        )


        # close dialog window button
        # right-align the button
        with vuetify.VCol(classes="text-right"):
          vuetify.VBtn("Close", classes="mt-5",click=update_dialog)


# real-time update every xx seconds
@asynchronous.task
async def start_countdown(result):
    global proc_SU2

    while state.keep_updating:
        with state:
            await asyncio.sleep(2.0)
            log("debug", f"iteration =  = {state.global_iter, type(state.global_iter)}")
            wrt_freq = state.jsonData['OUTPUT_WRT_FREQ'][1]
            log("debug", f"wrt_freq =  = {wrt_freq, type(wrt_freq)}")
            log("info", f"iteration save =  = {state.global_iter % wrt_freq}")
            log("debug", f"keep updating =  = {state.keep_updating}")
            # update the history from file
            readHistory(BASE / "user" / state.case_name / state.history_filename)
            # update the restart from file, do not reset the active scalar value
            # do not update when we are about to write to the file
            readRestart(BASE / "user" / state.case_name / state.restart_filename, False)

            # we flip-flop the true-false state to keep triggering the state and read the history file
            state.countdown = not state.countdown
            # check that the job is still running
            log("debug", f"poll =  = {proc_SU2.poll()}")
            if proc_SU2.poll() != None:
              log("info", "job has stopped")
              # stop updating the graphs
              state.keep_updating = False
              # set the running state to false
              state.solver_running = False
              state.solver_icon="mdi-play-circle"
            update_su2_logs()


###############################################################
# PIPELINE CARD : Solver
###############################################################
def solver_card():
    with ui_card(title="Solver", ui_name="Solver"):
        log("debug", "## Solver Selection ##")
      # 1 row of option lists
        with vuetify.VRow(classes="pt-2"):
          with vuetify.VCol(cols="8"):

            vuetify.VTextField(
                # What to do when something is selected
                v_model=("convergence_val", -12),
                # the name of the list box
                label="Residual convergence value",
            )
          with vuetify.VCol(cols="4", classes="py-0 my-0"):
            with vuetify.VBtn(classes="mx-0 py-0 mt-2 mb-0",elevation=1,variant="text",color="white", click=update_solver_dialog_card_convergence, icon="mdi-dots-vertical"):
              vuetify.VIcon("mdi-dots-vertical",density="compact",color="green")

        # 1 row of option lists
        with vuetify.VRow(classes="pt-2"):
          with vuetify.VCol(cols="10"):

            vuetify.VTextField(
                # What to do when something is selected
                v_model=("iter_idx", 100),
                # the name of the list box
                label="Iterations",
            )

        with vuetify.VBtn("Solve",click=su2_play):
            vuetify.VIcon("{{solver_icon}}",color="purple")

########################################################################################
# Checks/Corrects some json entries before starting the Solver
########################################################################################
# def checkjsonData():
#    if 'RESTART_FILENAME' in state.jsonData:
#        state.jsonData['RESTART_FILENAME' ] = 'restart'
#        state.restart_filename = 'restart'
#    if 'SOLUTION_FILENAME' in state.jsonData:
#        state.jsonData['SOLUTION_FILENAME' ] = 'solution_flow'

def checkCaseName():
    if state.case_name is None or state.case_name == "":
        log("error", "Case name is empty, create a new case.  \n Otherwise your data will not be saved!")
        return False
    return True

###############################################################
# Solver - state changes
###############################################################
@state.change("iter_idx")
def update_material(iter_idx, **kwargs):
    #
    log("debug", f"ITER value:  = {state.iter_idx}")
    #
    # we want to call a submenu
    #state.active_sub_ui = "submaterials_fluid"
    #
    # update config option value
    try:
      state.jsonData['ITER'] = int(state.iter_idx)
    except ValueError:
      log("error", "Invalid value for ITER")

@state.change("convergence_val")
def update_material(convergence_val, **kwargs):
    #
    # update config option value
    try:
      state.jsonData['CONV_RESIDUAL_MINVAL'] = int(state.convergence_val)
    except ValueError:
      log("error", "Invalid value for CONV_RESIDUAL_MINVAL in solver")


# start SU2 solver
def su2_play():
    global proc_SU2

    # Use stored SU2_CFD path or fallback to "SU2_CFD" if not set
    su2_cfd_path = getattr(state, "su2_cfd_path", None)
    if not su2_cfd_path:
        # Try to get from config as fallback
        from user_config import get_su2_path
        import base64
        su2_cfd_path = get_su2_path()
        if not su2_cfd_path:
            log("error", "SU2_CFD path not configured. Please restart SU2GUI to configure the path.")
            return

    # every time we press the button we switch the state
    state.solver_running = not state.solver_running
    if state.solver_running:
        log("info", f"### SU2 solver started using {su2_cfd_path}!")
        # change the solver button icon
        state.solver_icon="mdi-stop-circle"

        # reset monitorLinesNames for the history plot
        state.monitorLinesNames = []

        # check if the case name is set
        if not checkCaseName():
            return

        # save the cfg file
        save_json_cfg_file(state.filename_json_export,state.filename_cfg_export)
        # save the mesh file
        global root
        save_su2mesh(root,state.jsonData['MESH_FILENAME'])

        # clear old su2 log and set new one
        state.last_modified_su2_log_len = 0
        state.su2_logs = ""

        # run SU2_CFD with config.cfg
        with open(BASE / "user" / state.case_name / "su2.out", "w") as outfile:
          with open(BASE / "user" / state.case_name / "su2.err", "w") as errfile:
            proc_SU2 = subprocess.Popen([su2_cfd_path, state.filename_cfg_export],
                                cwd= BASE / "user" / state.case_name,
                                text=True,
                                stdout=outfile,
                                stderr=errfile
                                )
        # at this point we have started the simulation
        # we can now start updating the real-time plots
        state.keep_updating = True
        log("debug", f"start polling, poll =  = {proc_SU2.poll()}")

        # Wait until process terminates
        #while result.poll() is None:
        #  time.sleep(1.0)
        log("debug", f"result =  = {proc_SU2}")
        log("debug", f"result poll=  = {proc_SU2.poll()}")

        # periodic update of the monitor and volume result
        start_countdown(proc_SU2)


        log("debug", f"result =  = {proc_SU2}")
        # save mesh
        # save config
        # save restart file
        # call su2_cfd
    else:
        state.solver_icon="mdi-play-circle"
        log("info", "### SU2 solver stopped!"),
        # we need to terminate or kill the result process here if stop is pressed
        log("debug", f"process= = {type(proc_SU2)}")
        proc_SU2.terminate()

# matplotlib history
def update_convergence_fields_visibility(index, visibility):
    log("debug", f"index= = {index}")
    log("debug", f"visible= = {state.convergence_fields_visibility}")
    state.convergence_fields_visibility[index] = visibility
    log("debug", f"visible= = {state.convergence_fields_visibility}")
    state.dirty("convergence_fields_visibility")
    log("debug", f"Toggle {index} to {visibility}")


# matplotlib history
# select which variables to use for convergence. Currently: only residual values of the solver
def solver_dialog_card_convergence():
    with vuetify.VDialog(width=300,position='{X:10,Y:10}',transition="dialog-top-transition",v_model=("show_solver_dialog_card_convergence",False)):
      with vuetify.VCard():


        vuetify.VCardTitle("Convergence Criteria",
                           classes="grey lighten-1 py-1 grey--text text--darken-3")
        with vuetify.VContainer(fluid=True):

          # ####################################################### #
          with vuetify.VRow(classes="py-0 my-0"):
            with vuetify.VCol(cols="8", classes="py-1 my-1 pr-0 mr-0"):
              vuetify.VCheckbox(
                              # loop over list of convergence fields
                              v_for="id in convergence_fields_range",
                              key="id",
                              # checkbox changes the state of monitorLinesVisibility[id]
                              v_model=("convergence_fields_visibility[id]",),
                              # name of the checkbox
                              label=("`${ convergence_fields[id] }`",),
                              # on each change, immediately go to update_convergence_fields_visibility
                              change=(update_convergence_fields_visibility,"[id, $event]"),
                              classes="mt-1 pt-1",
                              hide_details=True,
                              dense=True,
              )

        with vuetify.VCardText():
          vuetify.VBtn("close", click=update_solver_dialog_card_convergence)



###############################################################################
def update_solver_dialog_card_convergence():
    log("debug", f"changing state of solver_dialog_Card_convergence to: = {state.show_solver_dialog_card_convergence}")
    state.show_solver_dialog_card_convergence = not state.show_solver_dialog_card_convergence    # if we show the card, then also update the fields that we need to show
    if state.show_solver_dialog_card_convergence==True:
      log("debug", "updating list of fields")
      # note that Euler and inc_euler can be treated as compressible / incompressible as well
      log("debug", state.jsonData.get('SOLVER', 'EULER'))
      
      # Safely check if INC_ENERGY_EQUATION exists in the state
      inc_energy = state.jsonData.get('INC_ENERGY_EQUATION', False)
      log("debug", f"INC_ENERGY_EQUATION: {inc_energy}")

      if ("INC" in str(state.jsonData.get('SOLVER', ''))):
        compressible = False
      else:
        compressible = True

      # if incompressible, we check if temperature is on
      if (compressible==False):
        if (inc_energy==True):
           energy=True
        else:
           energy=False

        # INC_RANS: [PRESSURE VELOCITY-X VELOCITY-Y] [VELOCITY-Z] [TEMPERATURE]
        # SA: [NU_TILDE]
        # SST: [TKE, DISSIPATION]
        # RANS: [DENSITY MOMENTUM-X MOMENTUM-Y] [ENERGY] [MOMENTUM-Z]

      if (compressible==True):
        state.convergence_fields=["RMS_DENSITY","RMS_MOMENTUM-X","RMS_MOMENTUM-Y"]
        if (state.nDim==3):
          state.convergence_fields.append("RMS_MOMENTUM-Z")
        state.convergence_fields.append("RMS_ENERGY")
      else:
        state.convergence_fields=["RMS_PRESSURE","RMS_VELOCITY-X","RMS_VELOCITY-Y"]
        if (state.nDim==3):
          state.convergence_fields.append("RMS_VELOCITY-Z")
        if (energy==True):
          state.convergence_fields.append("RMS_TEMPERATURE")

      state.convergence_fields_range=list(range(0,len(state.convergence_fields)))

      # get the checkbox states from the jsondata
      state.convergence_fields_visibility = [False for i in state.convergence_fields]
      for field in state.jsonData['CONV_FIELD']:
         log("debug", f"field= = {field}")
         for i in range(len(state.convergence_fields)):
            log("debug", f"i= = {i} {state.convergence_fields[i]}")
            if (field==state.convergence_fields[i]):
               log("debug", "field found")
               state.convergence_fields_visibility[i] = True

      log("debug", f"convergence fields: = {state.convergence_fields}")
      state.dirty('convergence_fields')
      state.dirty('convergence_fields_range')
    else:

       # the dialog is closed again: we update the state of CONV_FIELD in jsonData
         state.jsonData['CONV_FIELD']=[]
         for i in range(len(state.convergence_fields_visibility)):
            if (state.convergence_fields_visibility[i]==True):
               state.jsonData['CONV_FIELD'].append(state.convergence_fields[i])






###############################################################################
# matplotlib
def update_dialog():
    state.show_dialog = not state.show_dialog
    state.dirty('monitorLinesVisibility')
    state.dirty('monitorLinesNames')
    state.dirty('monitorLinesRange')



###############################################################################
# Read the history file
# set the names and visibility
def readHistory(filename):
    log("debug", f"read_history, filename= = {filename}")
    skipNrRows=[]
    # read the history file
    dataframe = pd.read_csv(filename,skiprows=skipNrRows)
    # get rid of quotation marks in the column names
    dataframe.columns = dataframe.columns.str.replace('"','')
    # get rid of spaces in the column names
    dataframe.columns = dataframe.columns.str.replace(' ','')

    # limit the columns to the ones containing the strings rms and Res
    dfrms = dataframe.filter(regex='rms|Res')

    # only set the initial state the first time
    if state.monitorLinesNames==[]:
       state.monitorLinesNames = list(dfrms)
       state.monitorLinesRange = list(range(0,len(state.monitorLinesNames)))
       state.monitorLinesVisibility = [True for i in dfrms]
       state.dirty('monitorLinesNames')
       state.dirty('monitorLinesVisibility')
       state.dirty('monitorLinesRange')

    state.x = [i for i in range(len(dfrms.index))]
    # number of global iterations, assuming we start from 0 and every line is an iteration.
    # actually, we should look at Inner_Iter
    state.global_iter = len(dfrms.index)
    #log("info", f"x =  = {state.x}")
    state.ylist=[]
    for c in range(len(dfrms.columns)):
        state.ylist.append(dfrms.iloc[:,c].tolist())

    dialog_card()
    return [state.x,state.ylist]


###############################################################################
# read restart file (binary or ASCII)
def Read_SU2_Restart_Binary(val_filename):
    val_filename = str(val_filename)
    fname = val_filename
    nRestart_Vars = 5
    Restart_Vars = [0] * nRestart_Vars
    fields = []
    
    try:
        # Always try ASCII format first since we have issues with binary
        log("info", "Reading restart file in ASCII format")
        try:
            # Try loading as CSV first (simplest case)
            df = pd.read_csv(fname)
            log("info", f"Successfully loaded restart file as CSV with {len(df)} rows")
            return df
        except Exception as e:
            log("info", f"Could not read as CSV, trying custom ASCII parsing: {e}")
            
            try:
                with open(fname, "r", errors='replace') as f:
                    try:
                        # Simple parsing of ASCII restart file
                        lines = f.readlines()
                        if len(lines) > 0:
                            header = lines[0].strip().split()
                            if len(header) >= 3:
                                # Extract nFields and nPointFile from header
                                try:
                                    nFields = int(header[1])
                                    nPointFile = int(header[2])
                                    Restart_Vars[1] = nFields
                                    Restart_Vars[2] = nPointFile
                                except ValueError:
                                    log("error", "Failed to parse ASCII restart file header")
                                    raise
                        
                        # Get field names from the second line
                        if len(lines) > 1:
                            field_names = lines[1].strip().split()
                            fields = field_names
                            
                        # Parse data lines
                        data = []
                        for i in range(2, len(lines)):
                            try:
                                values = [float(val) for val in lines[i].strip().split()]
                                if len(values) == len(fields):
                                    data.append(values)
                            except:
                                pass
                        
                        df = pd.DataFrame(data, columns=fields)
                        log("info", f"Successfully parsed ASCII restart file with {len(df)} rows")
                        return df
                    except Exception as e:
                        log("error", f"Error parsing ASCII restart file: {e}")
            except UnicodeDecodeError:
                log("info", "File appears to be binary. Attempting binary read.")
                # Here we would handle binary format, but currently just returning empty DataFrame
                # For binary formats, you would need specific binary parsing logic
                return pd.DataFrame()
    except Exception as e:
        log("error", f"Failed to read restart file: {e}")
    
    log("info", "Unable to read restart file")
    return pd.DataFrame()


# # ##### upload ascii restart file #####
@state.change("restartFile")
def uploadRestart(restartFile, **kwargs):
  log("debug", "Updating restart.csv file")
  if restartFile is None:
    state.jsonData["RESTART_SOL"] = False
    state.jsonData["READ_BINARY_RESTART"] = False
    log("debug", "removed file")
    return

  # check if the case name is set
  if not checkCaseName():
    state.restartFile = None
    return
    
  # Set READ_BINARY_RESTART to false to ensure we can read different types of restart files
  state.jsonData["READ_BINARY_RESTART"] = False

  filename = restartFile['name']
  file = ClientFile(restartFile)

  base_path = Path("e:/gsoc/su2gui/user") / state.case_name
  base_path.mkdir(parents=True, exist_ok=True)  # Create directories if they do not exist
      # for .csv
  if filename.endswith(".csv"):
    try:
        # Only try to decode if it's bytes, otherwise use as is
        filecontent = file.content.decode('utf-8') if isinstance(file.content, bytes) else file.content
    except UnicodeDecodeError:
        log("warning", "Could not decode file content as UTF-8, treating as raw content")
        filecontent = file.content

    # Only split into lines if we have text content
    if isinstance(filecontent, str):
        f = filecontent.splitlines()

    with open(BASE / "user" / state.case_name / filename, 'w') as restartFile:
      restartFile.write(filecontent)

    state.jsonData["SOLUTION_FILENAME"] = filename
    state.jsonData["RESTART_SOL"] = True
    state.jsonData["READ_BINARY_RESTART"] = False
    
    # we reset the active field because we read or upload the restart from file as a user action
    readRestart(BASE / "user" / state.case_name / filename, True, initialization='.csv')
  # for .dat binary restart file
  elif filename.endswith(".dat"):    # Use safe_b64decode to handle missing padding
    def safe_b64decode(data):
      if isinstance(data, str):
        try:
            data = b64decode(data)
        except Exception as e:
            log("error", f"Error decoding base64 data: {e}")
      return data

    # Get binary content
    filecontent = safe_b64decode(file.content)
    
    # Write binary content to file
    with open(BASE / "user" / state.case_name / filename, 'wb') as restartFile:
      restartFile.write(filecontent)
    
    state.jsonData["SOLUTION_FILENAME"] = filename
    state.jsonData["RESTART_SOL"] = True
    state.jsonData["READ_BINARY_RESTART"] = True

    
    # we reset the active field because we read or upload the restart from file as a user action
    readRestart(BASE / "user" / state.case_name / filename, True, initialization='.dat')
      
  log("info", "Restart loaded ")


# check if a file has a handle on it
#def has_handle(fpath):
#    for proc in psutil.process_iter():
#        try:
#            for item in proc.open_files():
#                log("info", f"item= = {item}")
#                if fpath == item.path:
#                    return True
#        except Exception:
#            pass
#
#    return False

# read the restart file
# reset_active_field is used to show the active field
def readRestart(restartFile, reset_active_field, **kwargs):

  # check and add extension if needed
  restartFile = str(restartFile)
  log("debug", f"read_restart, filename= = {restartFile}")    # kwargs is used to pass the initialization of the restart file
    # check if function is called by restart initialization 
  if 'initialization' in kwargs:
    if kwargs['initialization']=='.dat':
       # Set READ_BINARY_RESTART to False when reading restart files
       state.jsonData['READ_BINARY_RESTART'] = False
       df = Read_SU2_Restart_Binary(restartFile)
    else:
        df = pd.read_csv(restartFile)
  else:
    # move the file to prevent that the file is overwritten while reading
    # the file can still be overwritten while renaming, but the time window is smaller
    # we also try to prevent this by not calling readRestart when we are about to write a file
    # (based on current iteration number)
    try:
        lock_file = restartFile + ".lock"

        # Copy or overwrite the lock_file with the contents of restartFile
        # shutil.copy2 handles binary files correctly
        shutil.copy2(restartFile, lock_file)

        # Read the lock_file based on the state
        if state.fileio_restart_binary or restartFile.endswith(".dat"):
            df = Read_SU2_Restart_Binary(lock_file)
        else:
            df = pd.read_csv(lock_file)
    except Exception as e:
        log("info", f"Unable to read restart file. It may not be available yet or is being used by another process.\n  {e}")
        df = pd.DataFrame()


  # check if the points and cells match, if not then we probably were writing to the file
  # while reading it and we just skip this update
  log("info", f"number of points read =  = {len(df)}")
  log("info", f"number of points expected =  = {grid.GetPoints().GetNumberOfPoints()}")
  if len(df) != grid.GetPoints().GetNumberOfPoints():
    log("info", "Restart file is invalid, skipping update")
    return

  # construct the dataset_arrays
  datasetArrays = []
  counter=0
  for key in df.keys():
    name = key
    log("info", f"reading restart, field name =  = {name}")
    # let's skip these 
    if (name in ['PointID','x','y']):
      continue

    ArrayObject = vtk.vtkFloatArray()
    ArrayObject.SetName(name)
    # all components are scalars, no vectors for velocity
    ArrayObject.SetNumberOfComponents(1)
    # how many elements do we have?
    nElems = len(df[name])
    ArrayObject.SetNumberOfValues(nElems)
    ArrayObject.SetNumberOfTuples(nElems)

    # Nijso: TODO FIXME very slow!
    for i in range(nElems):
      ArrayObject.SetValue(i,df[name][i])

    grid.GetPointData().AddArray(ArrayObject)

    datasetArray = {
                "text": name,
                "value": counter,
                "type": vtkDataObject.FIELD_ASSOCIATION_POINTS,
            }

    try:
        datasetArray["range"] = [df[name].min(), df[name].max()]
    except TypeError as e:
        log("info", f"Could not compute range for field {name}: {e}")
    datasetArrays.append(datasetArray)
    counter += 1

  state.dataset_arrays = datasetArrays
  #log("info", f"dataset =  = {datasetArrays}")
  #log("info", f"dataset_0 =  = {datasetArrays[0]}")
  #log("info", f"dataset_0 =  = {datasetArrays[0].get('text'}"))

  mesh_mapper.SetInputData(grid)
  mesh_actor.SetMapper(mesh_mapper)
  renderer.AddActor(mesh_actor)

  # we should now have the scalars available. If we update the field from an active run, do not reset the
  # active scalar field
  if reset_active_field==True:
    defaultArray = datasetArrays[0]

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

  # renderer.ResetCamera()
  ctrl.view_update()


###############################################################################
def figure_size():
    if state.figure_size is None:
        return {}

    dpi = state.figure_size.get("dpi")
    rect = state.figure_size.get("size")
    w_inch = rect.get("width") / dpi
    h_inch = rect.get("height") / dpi

    if ((w_inch<=0) or (h_inch<=0)):
       return {}

    return {
        "figsize": (w_inch, h_inch),
        "dpi": dpi,
    }




###############################################################################
def mpl_plot_history():
    plt.close('all')
    fig, ax = plt.subplots(1, 1, **figure_size(), facecolor='blue')
    ax.set_facecolor('#eafff5')
    fig.set_facecolor('blue')
    fig.patch.set_facecolor('blue')
    fig.subplots_adjust(top=0.98, bottom=0.15, left=0.05, right=0.99, hspace=0.0, wspace=0.0)

    has_lines = False

    try:
        for idx in state.monitorLinesRange:
            if state.monitorLinesVisibility[idx]:
                ax.plot(state.x, state.ylist[idx], label=state.monitorLinesNames[idx], linewidth=5, markersize=20, markeredgewidth=10, color=mplColorList[idx % 20])
                has_lines = True

        ax.set_xlabel('iterations', labelpad=10)
        ax.set_ylabel('residuals', labelpad=-15)
        ax.grid(True, color="lightgray", linestyle="solid")

        if has_lines:
            ax.legend(framealpha=1, facecolor='white')

        ax.autoscale(enable=True, axis="x")
        ax.autoscale(enable=True, axis="y")

    except IndexError as e:
        log("error", f"IndexError                         : {e}. Index causing error: {idx}")
        log("error", f"state.x length                     : {len(state.x)}")
        log("error", f"state.ylist length                 : {len(state.ylist)}")
        log("error", f"state.monitorLinesNames length     : {len(state.monitorLinesNames), state.monitorLinesNames}")
        log("error", f"state.monitorLinesVisibility length: {len(state.monitorLinesVisibility)}")
        log("error", f"mplColorList length                : {len(mplColorList)}")

    return fig
