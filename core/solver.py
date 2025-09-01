# solver gittree menu

# note that in the main menu, we need to call add the following:
# 1) from core.solver import *
# 2) call solver_card() in SinglePageWithDrawerLayout
# 3) define a node in the gittree (pipeline)
# 4) define any global state variables that might be needed

import sys
import os
import shutil
import pandas as pd
import subprocess
import asyncio
import matplotlib
import warnings
import matplotlib.pyplot as plt
import vtk
from pathlib import Path

BASE = Path(__file__).parent.parent

parent_dir = str(Path(__file__).parent.parent.absolute())
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from ui.uicard import ui_card, ui_subcard, server
from trame.widgets import vuetify
from core.su2_json import *
from core.su2_io import save_su2mesh, save_json_cfg_file
from core.config_validator import SU2ConfigValidator

# check if a file is opened by another process
#import psutil
from base64 import b64decode
import io, struct

# real-time update, asynchronous io
from trame.app import get_server, asynchronous

from trame.app.file_upload import ClientFile

from vtkmodules.vtkCommonDataModel import vtkDataObject

# import the grid from the mesh module
from ui.mesh import *
from ui.vtk_helper import *

# Logging function
from core.logger import log, update_su2_logs

# matplotlib
matplotlib.use("agg")
from trame.widgets import matplotlib as tramematplotlib

# Suppress noisy mpld3 deprecation warnings with Matplotlib 3.10+
try:
    from matplotlib import MatplotlibDeprecationWarning
    warnings.filterwarnings(
        "ignore",
        category=MatplotlibDeprecationWarning,
        module=r"mpld3.*",
    )
except Exception:
    pass

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

# Initialize solver state variables
if not hasattr(state, 'solver_running'):
    state.solver_running = False
if not hasattr(state, 'solver_icon'):
    state.solver_icon = "mdi-play-circle"
if not hasattr(state, 'keep_updating'):
    state.keep_updating = False
if not hasattr(state, 'apply_auto_fixes'):
    state.apply_auto_fixes = True
if not hasattr(state, 'validation_issues'):
    state.validation_issues = []
if not hasattr(state, 'validation_fixes'):
    state.validation_fixes = []
if not hasattr(state, 'validation_summary'):
    state.validation_summary = ""

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
@state.change("active_figure", "figure_size", "countdown", "monitorLinesVisibility", "x", "ylist", "monitorLinesNames")
def update_chart(active_figure, **kwargs):
    log("info", "updating figure 1")
    try:
        if hasattr(ctrl, 'update_figure') and callable(ctrl.update_figure):
            ctrl.update_figure(globals()[active_figure]())
        else:
            log("debug", "ctrl.update_figure not available yet (normal during initialization)")
    except Exception as e:
        import traceback
        log("error", f"Error updating figure: {e}", detail=traceback.format_exc())
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

        # Validation panel
        with vuetify.VExpansionPanels():
            with vuetify.VExpansionPanel():
                vuetify.VExpansionPanelHeader("Validation & Preflight")
                with vuetify.VExpansionPanelContent():
                    with vuetify.VRow(classes="pt-2"):
                        with vuetify.VCol(cols="6"):
                            vuetify.VCheckbox(
                                v_model=("apply_auto_fixes", True),
                                label="Apply auto-fixes before run",
                                hide_details=True,
                                dense=True,
                            )
                        with vuetify.VCol(cols="6", classes="text-right"):
                            vuetify.VBtn("Run preflight", color="primary", click=run_preflight_validation)
                    # Summary
                    vuetify.VAlert(
                        v_show=("validation_summary",),
                        type_="info",
                        text=("validation_summary", ""),
                        dense=True,
                        outlined=True,
                    )
                    # Issues list
                    vuetify.VSubheader("Issues")
                    with vuetify.VList(two_line=True, dense=True):
                        with vuetify.Template(v_slot_item=True):
                            pass
                    with vuetify.VList(dense=True):
                        # Render up to 20 issues (robust guard when list may be undefined)
                        with vuetify.VListItem(v_for="(item,idx) in ((typeof validation_issues !== 'undefined' && validation_issues) ? validation_issues : []).slice(0,20)", key="idx"):
                            with vuetify.VListItemContent():
                                vuetify.VListItemTitle("`$${item.path || 'root'}`")
                                vuetify.VListItemSubtitle("`$${item.message}`")
                    # Fixes list
                    vuetify.VSubheader("Applied Fixes (preview)")
                    with vuetify.VList(dense=True):
                        with vuetify.VListItem(v_for="(fix,i) in ((typeof validation_fixes !== 'undefined' && validation_fixes) ? validation_fixes : []).slice(0,20)", key="i"):
                            vuetify.VListItemTitle("`$${fix.message}`")

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

def check_solver_requirements():
    """Check if all requirements are met to run the solver"""
    issues = []
    
    su2_path = getattr(state, "su2_cfd_path", None)
    if not su2_path:
        try:
            from core.user_config import get_su2_path
            su2_path = get_su2_path()
        except:
            pass
    
    if not su2_path:
        issues.append("SU2_CFD executable path not configured")
    elif not os.path.exists(su2_path):
        issues.append(f"SU2_CFD executable not found at: {su2_path}")
    
    # Check case name
    if not hasattr(state, 'case_name') or not state.case_name:
        issues.append("No case name specified")
    
    # Check configuration
    if not hasattr(state, 'jsonData') or not state.jsonData:
        issues.append("No configuration data loaded")
    
    return issues
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

    log("info", "=== SOLVE BUTTON CLICKED ===")
    
    # Use stored SU2_CFD path or fallback to "SU2_CFD" if not set
    su2_cfd_path = getattr(state, "su2_cfd_path", None)
    log("info", f"Initial SU2 path: {su2_cfd_path}")
    
    if not su2_cfd_path:
        # Try to get from config as fallback
        try:
            from core.user_config import get_su2_path
            su2_cfd_path = get_su2_path()
            log("info", f"Config SU2 path: {su2_cfd_path}")
        except Exception as e:
            log("error", f"Failed to import user_config: {e}")
            su2_cfd_path = None
            
        if not su2_cfd_path:
            log("error", " SU2_CFD path not configured!")
            log("error", "Please restart SU2GUI and configure the SU2_CFD executable path.")
            log("error", "Cannot start solver without SU2_CFD executable path.")
            # Reset the button state
            state.solver_running = False
            state.solver_icon = "mdi-play-circle"
            return

    # Check if SU2_CFD executable exists
    if not os.path.exists(su2_cfd_path):
        log("error", f" SU2_CFD executable not found at: {su2_cfd_path}")
        log("error", "Please check the SU2_CFD path configuration.")
        state.solver_running = False
        state.solver_icon = "mdi-play-circle"
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
            log("error", " Cannot start solver: No case name specified.")
            log("error", "Please create a case in the CASES tab first.")
            # Reset the solver state
            state.solver_running = False
            state.solver_icon = "mdi-play-circle"
            return
            
        log("info", f" Using case: {state.case_name}")
        
        # Check if required files exist
        mesh_filename = state.jsonData.get('MESH_FILENAME', 'unknown')
        log("info", f"Expected mesh file: {mesh_filename}")
        
        if not hasattr(state, 'jsonData') or not state.jsonData:
            log("error", " No configuration data available.")
            log("error", "Please load a mesh file or configuration.")
            state.solver_running = False
            state.solver_icon = "mdi-play-circle"
            return

        # save the cfg file
        try:
            save_json_cfg_file(state.filename_json_export,state.filename_cfg_export)
            log("info", f"Saved config file: {state.filename_cfg_export}")
        except Exception as e:
            log("error", f"Failed to save config file: {e}")
            state.solver_running = False
            state.solver_icon = "mdi-play-circle"
            return

        # Preflight validation: validate the saved cfg by converting to JSON, run custom checks,
        # and apply safe auto-fixes. Do not rely on bundled schema by default.
        try:
            cfg_path = str(BASE / "user" / state.case_name / state.filename_cfg_export)
            validator = SU2ConfigValidator()
            result = validator.validate_config_file(cfg_path, auto_fix=bool(state.apply_auto_fixes))

            if not result.get('valid', False):
                total = len(result.get('errors', []))
                log("error", f"Configuration preflight found {total} issues")
                # Show up to 10 issues for readability
                for i, err in enumerate(result.get('errors', [])[:10], start=1):
                    path = "/".join([str(p) for p in err.get('path', [])]) if isinstance(err, dict) else ''
                    msg = err.get('message', str(err)) if isinstance(err, dict) else str(err)
                    log("error", f"  {i}. {path}: {msg}")
                if total > 10:
                    log("error", f"  ... and {total - 10} more")

            # If auto-fixes were applied, update state.jsonData and re-save files
            fixes = result.get('applied_fixes', [])
            # Update UI state for validation panel
            state.validation_issues = [
                {
                    'path': '/'.join([str(p) for p in (e.get('path') or [])]) if isinstance(e, dict) else '',
                    'message': (e.get('message') if isinstance(e, dict) else str(e))
                }
                for e in result.get('errors', [])
            ]
            state.validation_fixes = fixes
            state.validation_summary = (
                f"Issues: {len(state.validation_issues)} | Fixes: {len(fixes)} | Auto-fix: {'ON' if state.apply_auto_fixes else 'OFF'}"
            )
            state.dirty('validation_issues'); state.dirty('validation_fixes'); state.dirty('validation_summary'); state.dirty('apply_auto_fixes')
            if fixes:
                log("info", f"Applied {len(fixes)} auto-fix(es) to configuration before run")
                for fix in fixes[:10]:
                    log("info", f"  - {fix.get('message', '')}")
                # Update in-memory config and persist
                fixed_cfg = result.get('config_data', {})
                if isinstance(fixed_cfg, dict):
                    state.jsonData.update(fixed_cfg)
                    # Persist the updated JSON/CFG so SU2 uses the corrected values
                    save_json_cfg_file(state.filename_json_export, state.filename_cfg_export)
        except Exception as e:
            log("warn", f"Preflight validation failed: {e}")

        # Continue with mesh save and solver launch
        # save the mesh file
        try:
            global root
            save_su2mesh(root, state.jsonData['MESH_FILENAME'])
            log("info", f"Saved mesh file: {state.jsonData['MESH_FILENAME']}")
        except Exception as e:
            log("error", f"Failed to save mesh file: {e}")
            state.solver_running = False
            state.solver_icon = "mdi-play-circle"
            return

        # clear old su2 log and set new one
        state.last_modified_su2_log_len = 0
        state.su2_logs = ""

        # run SU2_CFD with config.cfg
        with open(BASE / "user" / state.case_name / "su2.out", "w") as outfile:
            with open(BASE / "user" / state.case_name / "su2.err", "w") as errfile:
                proc_SU2 = subprocess.Popen([su2_cfd_path, state.filename_cfg_export],
                                            cwd=BASE / "user" / state.case_name,
                                            text=True,
                                            stdout=outfile,
                                            stderr=errfile
                                            )
        # at this point we have started the simulation
        # we can now start updating the real-time plots
        state.keep_updating = True
        log("debug", f"start polling, poll =  = {proc_SU2.poll()}")

        # Wait until process terminates
        # while result.poll() is None:
        #   time.sleep(1.0)
        log("debug", f"result =  = {proc_SU2}")
        log("debug", f"result poll=  = {proc_SU2.poll()}")

        # periodic update of the monitor and volume result
        start_countdown(proc_SU2)

    else:
        # Stop solver
        state.solver_icon = "mdi-play-circle"
        log("info", "### SU2 solver stopped!")
        log("debug", f"process= = {type(proc_SU2)}")
        if proc_SU2 is not None:
            proc_SU2.terminate()
        else:
            log("warning", "No SU2 process to terminate")

def run_preflight_validation():
    """Run preflight validation and update the validation panel, without starting SU2."""
    try:
        # Persist current JSON/CFG so validation checks the latest config
        try:
            save_json_cfg_file(state.filename_json_export, state.filename_cfg_export)
        except Exception as e:
            log('warn', f'Could not save config before preflight: {e}')
        cfg_path = str(BASE / "user" / state.case_name / state.filename_cfg_export)
        validator = SU2ConfigValidator()
        result = validator.validate_config_file(cfg_path, auto_fix=bool(state.apply_auto_fixes))
        fixes = result.get('applied_fixes', [])
        state.validation_issues = [
            {
                'path': '/'.join([str(p) for p in (e.get('path') or [])]) if isinstance(e, dict) else '',
                'message': (e.get('message') if isinstance(e, dict) else str(e))
            }
            for e in result.get('errors', [])
        ]
        state.validation_fixes = fixes
        state.validation_summary = (
            f"Issues: {len(state.validation_issues)} | Fixes: {len(fixes)} | Auto-fix: {'ON' if state.apply_auto_fixes else 'OFF'}"
        )
        state.dirty('validation_issues'); state.dirty('validation_fixes'); state.dirty('validation_summary'); state.dirty('apply_auto_fixes')
        # If fixes were applied, persist them
        if fixes:
            fixed_cfg = result.get('config_data', {})
            if isinstance(fixed_cfg, dict):
                state.jsonData.update(fixed_cfg)
                save_json_cfg_file(state.filename_json_export, state.filename_cfg_export)
        log('info', 'Preflight validation complete')
    except Exception as e:
        log('warn', f'Preflight validation failed: {e}')

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
    log("debug", f"read_history, filename={filename}")
    
    # Initialize state variables if they don't exist
    if not hasattr(state, 'monitorLinesNames'):
        state.monitorLinesNames = []
    if not hasattr(state, 'monitorLinesRange'):
        state.monitorLinesRange = []
    if not hasattr(state, 'monitorLinesVisibility'):
        state.monitorLinesVisibility = []
    if not hasattr(state, 'x'):
        state.x = []
    if not hasattr(state, 'ylist'):
        state.ylist = []
    if not hasattr(state, 'global_iter'):
        state.global_iter = 0
    
    # Check if file exists
    filename = str(filename)
    if not os.path.exists(filename):
        log("warn", f"History file does not exist: {filename}")
        # Create empty history file if it doesn't exist
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w') as f:
                f.write("# SU2 History File\n")
                f.write("# No data available yet\n")
            log("info", f"Created empty history file: {filename}")
        except Exception as e:
            log("error", f"Could not create history file: {e}")
        
        # Return empty data
        state.x = []
        state.ylist = []
        state.global_iter = 0
        return [state.x, state.ylist]
    
    try:
        skipNrRows = []
        # read the history file
        dataframe = pd.read_csv(filename, skiprows=skipNrRows)
        
        # Check if dataframe is empty
        if dataframe.empty:
            # First-run or freshly created file; keep noise low
            log("info", f"History file is empty: {filename}")
            state.x = []
            state.ylist = []
            state.global_iter = 0
            return [state.x, state.ylist]
        
        # get rid of quotation marks in the column names
        dataframe.columns = dataframe.columns.str.replace('"','')
        # get rid of spaces in the column names
        dataframe.columns = dataframe.columns.str.replace(' ','')

        # limit the columns to the ones containing the strings rms and Res
        dfrms = dataframe.filter(regex='rms|Res')
        
        # If no columns match the filter, use all columns
        if dfrms.empty:
            log("info", "No 'rms' or 'Res' columns found, using all numeric columns")
            # Select only numeric columns
            dfrms = dataframe.select_dtypes(include=['number'])
            
            # If still no numeric columns, log warning and return empty
            if dfrms.empty:
                log("warn", "No numeric columns found in history file")
                state.x = []
                state.ylist = []
                state.global_iter = 0
                return [state.x, state.ylist]

        # only set the initial state the first time
        if not state.monitorLinesNames or len(state.monitorLinesNames) == 0:
            state.monitorLinesNames = list(dfrms.columns)
            state.monitorLinesRange = list(range(0, len(state.monitorLinesNames)))
            state.monitorLinesVisibility = [True for i in range(len(dfrms.columns))]
            state.dirty('monitorLinesNames')
            state.dirty('monitorLinesVisibility')
            state.dirty('monitorLinesRange')
            log("info", f"Initialized monitor lines: {state.monitorLinesNames}")

        state.x = [i for i in range(len(dfrms.index))]
        # number of global iterations, assuming we start from 0 and every line is an iteration.
        # actually, we should look at Inner_Iter
        state.global_iter = len(dfrms.index)
        log("info", f"History data: {len(state.x)} iterations")
        
        state.ylist = []
        for c in range(len(dfrms.columns)):
            state.ylist.append(dfrms.iloc[:,c].tolist())

        # Update state
        state.dirty('x')
        state.dirty('ylist')
        state.dirty('global_iter')
        state.dirty('monitorLinesNames')
        state.dirty('monitorLinesVisibility')
        state.dirty('monitorLinesRange')
        
        # Only call dialog_card if we're in a UI context
        try:
            dialog_card()
        except Exception as e:
            log("debug", f"Could not create dialog card (normal during initialization): {e}")
            
        log("info", f"Successfully loaded history data: {len(state.x)} iterations, {len(dfrms.columns)} variables")
        return [state.x, state.ylist]
        
    except pd.errors.EmptyDataError:
        log("warn", f"History file is empty or has no data: {filename}")
        state.x = []
        state.ylist = []
        state.global_iter = 0
        return [state.x, state.ylist]
        
    except Exception as e:
        import traceback
        log("error", f"Error reading history file {filename}: {e}", detail=traceback.format_exc())
        state.x = []
        state.ylist = []
        state.global_iter = 0
        return [state.x, state.ylist]


###############################################################################
# read restart file (binary or ASCII)
def Read_SU2_Restart_Binary(val_filename):
    """
    Read restart file with improved error handling and format detection.
    This function properly handles both binary and ASCII formats.
    """
    val_filename = str(val_filename)
    log("info", f"Reading restart file: {val_filename}")
    
    def detect_file_format(file_path):
        """Detect if a restart file is binary or ASCII format with improved detection."""
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                
                if not chunk:
                    return 'ascii'  # Empty file, treat as ASCII
                
                # Check for null bytes (strong indicator of binary)
                if b'\x00' in chunk:
                    return 'binary'
                
                # Check for high percentage of non-printable characters
                non_printable = sum(1 for byte in chunk if byte < 32 or byte > 126)
                threshold = 0.3
                
                if non_printable / len(chunk) > threshold:
                    return 'binary'
                else:
                    # Additional check for SU2 ASCII format patterns
                    try:
                        text_chunk = chunk.decode('utf-8')
                        # Look for typical SU2 ASCII restart file patterns
                        if any(pattern in text_chunk.lower() for pattern in ['ndime', 'nelem', 'npoin']):
                            log("info", "SU2 ASCII format patterns detected")
                        return 'ascii'
                    except UnicodeDecodeError:
                        return 'binary'
                    
        except Exception as e:
            log("warn", f"Error detecting file format: {e}")
            return 'ascii'  # Default to ASCII if detection fails
    
    def read_ascii_restart_file(file_path):
        """Read ASCII format restart file with robust error handling."""
        try:
            # Try pandas CSV reader first
            try:
                df = pd.read_csv(file_path)
                log("info", f"Successfully read restart file as CSV: {len(df)} rows, {len(df.columns)} columns")
                return df
            except Exception as e:
                log("info", f"Could not read as CSV, trying custom parsing: {e}")
            
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
            
            if not lines:
                log("warn", "Empty restart file")
                return pd.DataFrame()
            
            data = []
            field_names = None
            data_start = 0
            
            # Try to parse header safely
            first_line = lines[0].strip().split()
            if len(first_line) >= 3:
                try:
                    nFields = int(first_line[1])
                    nPoints = int(first_line[2])
                    log("info", f"Parsed header: nFields={nFields}, nPoints={nPoints}")
                    
                    # Get field names from second line
                    if len(lines) > 1:
                        field_names = lines[1].strip().split()
                        data_start = 2
                except ValueError as e:
                    log("info", f"Header parsing failed, treating as data: {e}")
                    data_start = 0
            
            # Parse data lines with error handling
            for i in range(data_start, len(lines)):
                line = lines[i].strip()
                if line and not line.startswith('#'):
                    try:
                        values = [float(x) for x in line.split()]
                        if values:
                            data.append(values)
                    except ValueError:
                        # Skip lines that can't be parsed as numbers
                        continue
            
            if not data:
                log("warn", "No valid data found in restart file")
                return pd.DataFrame()
            
            # Create column names if not found
            if not field_names:
                max_cols = max(len(row) for row in data) if data else 0
                field_names = [f'Field_{i}' for i in range(max_cols)]
            
            # Ensure all rows have the same number of columns
            max_cols = len(field_names)
            for row in data:
                while len(row) < max_cols:
                    row.append(0.0)  # Pad with zeros instead of NaN
            
            df = pd.DataFrame(data, columns=field_names[:max_cols])
            log("info", f"Successfully parsed ASCII restart file: {len(df)} rows, {len(df.columns)} columns")
            return df
            
        except Exception as e:
            log("error", f"Error reading ASCII restart file: {e}")
            return pd.DataFrame()
    
    def read_binary_restart_file(file_path):
        """Handle binary restart files with improved detection and user guidance."""
        try:
            file_size = os.path.getsize(file_path)
            log("info", f"Binary restart file detected: {os.path.basename(file_path)} ({file_size} bytes)")
            
            # Try to detect if it's actually a text file misidentified as binary
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                    if first_line and any(c.isdigit() for c in first_line):
                        log("info", "File appears to be ASCII format despite binary detection - attempting ASCII read")
                        return read_ascii_restart_file(file_path)
            except UnicodeDecodeError:
                pass  # Truly binary file
            
            # Check for SU2 binary format signatures
            with open(file_path, 'rb') as f:
                header = f.read(64)  # Read first 64 bytes for analysis
                
            # Provide helpful guidance only once per session
            if not hasattr(read_binary_restart_file, '_guidance_shown'):
                provide_binary_restart_guidance()
                read_binary_restart_file._guidance_shown = True
            else:
                log("info", "Binary restart file detected - see previous guidance for conversion options")
            
            # Return empty DataFrame but with more context
            return pd.DataFrame()
            
        except Exception as e:
            log("error", f"Error processing binary restart file: {e}")
            return pd.DataFrame()
    
    # Main logic
    try:
        if not os.path.exists(val_filename):
            log("error", f"Restart file does not exist: {val_filename}")
            return pd.DataFrame()
        
        # Detect file format
        file_format = detect_file_format(val_filename)
        log("info", f"Detected file format: {file_format}")
        
        # Read based on format
        if file_format == 'ascii':
            df = read_ascii_restart_file(val_filename)
        else:
            df = read_binary_restart_file(val_filename)
        
        if df.empty:
            log("info", "Restart file processing completed - no data loaded")
            if file_format == 'binary':
                log("info", "This is expected for binary files until binary parsing is implemented")
        else:
            log("info", f"Successfully loaded restart file with {len(df)} rows and {len(df.columns)} columns")
        
        return df
        
    except Exception as e:
        log("error", f"Failed to read restart file {val_filename}: {e}")
        return pd.DataFrame()


# # ##### upload ascii restart file #####
@state.change("restartFile")
def uploadRestart(restartFile, **kwargs):
  log("debug", "Updating restart file")
  if restartFile is None:
    state.jsonData["RESTART_SOL"] = False
    state.jsonData["READ_BINARY_RESTART"] = False
    log("debug", "removed file")
    return

  # check if the case name is set
  if not checkCaseName():
    state.restartFile = None
    return
    
  filename = restartFile['name']
  file = ClientFile(restartFile)

  base_path = Path("e:/gsoc/su2gui/user") / state.case_name
  base_path.mkdir(parents=True, exist_ok=True)  # Create directories if they do not exist
  
  # Handle different file extensions
  file_path = BASE / "user" / state.case_name / filename
  
  try:
    if filename.endswith(".csv") or filename.endswith(".txt"):
      # Handle text-based files
      try:
          # Try to decode as UTF-8 first
          if isinstance(file.content, bytes):
              filecontent = file.content.decode('utf-8')
          else:
              filecontent = file.content
      except UnicodeDecodeError:
          try:
              # Try other encodings
              filecontent = file.content.decode('latin-1')
              log("warning", "File decoded using latin-1 encoding")
          except:
              log("error", "Could not decode file content")
              return

      with open(file_path, 'w', encoding='utf-8') as f:
        f.write(filecontent)
      
      state.jsonData["READ_BINARY_RESTART"] = False
      
    elif filename.endswith(".dat"):
      # Handle binary files
      try:
          if isinstance(file.content, str):
              # If it's a base64 string, decode it
              filecontent = b64decode(file.content)
          else:
              filecontent = file.content
      except Exception as e:
          log("error", f"Error processing binary file content: {e}")
          return

      with open(file_path, 'wb') as f:
        f.write(filecontent)
      
      state.jsonData["READ_BINARY_RESTART"] = True
      
    else:
      # For unknown extensions, try to detect format
      log("info", f"Unknown file extension: {filename}. Attempting auto-detection.")
      
      # Save as binary first to detect format
      if isinstance(file.content, str):
          try:
              filecontent = b64decode(file.content)
          except:
              filecontent = file.content.encode('utf-8')
      else:
          filecontent = file.content
          
      with open(file_path, 'wb') as f:
        f.write(filecontent)
      
      # The Read_SU2_Restart_Binary function will auto-detect the format
      state.jsonData["READ_BINARY_RESTART"] = False

    # Update configuration
    state.jsonData["SOLUTION_FILENAME"] = filename
    state.jsonData["RESTART_SOL"] = True
    
    # Read and process the restart file
    readRestart(file_path, True, initialization='.auto')
    
    log("info", f"Restart file '{filename}' loaded successfully")
    
  except Exception as e:
    log("error", f"Error uploading restart file: {e}")
    return


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
  log("debug", f"read_restart, filename= = {restartFile}")
  
  # kwargs is used to pass the initialization of the restart file
  # check if function is called by restart initialization 
  if 'initialization' in kwargs:
    # Always use the improved reading function regardless of extension
    df = Read_SU2_Restart_Binary(restartFile)
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

        # Use the improved reading function for all file types
        df = Read_SU2_Restart_Binary(lock_file)
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
        # Check if state variables are properly initialized
        if not hasattr(state, 'monitorLinesRange') or not hasattr(state, 'monitorLinesVisibility'):
            log("info", "Monitor line state variables not initialized")
            ax.text(0.5, 0.5, 'No history data available\nRun a simulation to generate data', 
                   horizontalalignment='center', verticalalignment='center', 
                   transform=ax.transAxes, fontsize=12)
            return fig
            
        if not hasattr(state, 'x') or not hasattr(state, 'ylist'):
            log("info", "History data not available")
            ax.text(0.5, 0.5, 'No history data available\nRun a simulation to generate data', 
                   horizontalalignment='center', verticalalignment='center', 
                   transform=ax.transAxes, fontsize=12)
            return fig
            
        # Check if we have data to plot
        if not state.x or not state.ylist:
            log("info", "No history data to plot")
            ax.text(0.5, 0.5, 'No history data available\nRun a simulation to generate data', 
                   horizontalalignment='center', verticalalignment='center', 
                   transform=ax.transAxes, fontsize=12)
            return fig
            
        # Ensure all arrays have the same length
        if len(state.monitorLinesRange) != len(state.monitorLinesVisibility):
            log("warn", f"Mismatch in monitor line arrays: range={len(state.monitorLinesRange)}, visibility={len(state.monitorLinesVisibility)}")
            # Fix the arrays
            max_len = max(len(state.monitorLinesRange), len(state.monitorLinesVisibility))
            while len(state.monitorLinesRange) < max_len:
                state.monitorLinesRange.append(len(state.monitorLinesRange))
            while len(state.monitorLinesVisibility) < max_len:
                state.monitorLinesVisibility.append(True)
            
        # Plot the data
        for idx in state.monitorLinesRange:
            if idx < len(state.monitorLinesVisibility) and state.monitorLinesVisibility[idx]:
                if idx < len(state.ylist):
                    label = state.monitorLinesNames[idx] if (hasattr(state, 'monitorLinesNames') and idx < len(state.monitorLinesNames)) else f'Variable {idx}'
                    color = mplColorList[idx % len(mplColorList)]
                    ax.plot(state.x, state.ylist[idx], label=label, linewidth=2, color=color)
                    has_lines = True

        ax.set_xlabel('Iterations', labelpad=10)
        ax.set_ylabel('Residuals', labelpad=10)
        ax.grid(True, color="lightgray", linestyle="solid")

        if has_lines:
            ax.legend(framealpha=1, facecolor='white')
        else:
            ax.text(0.5, 0.5, 'No visible data lines\nCheck line visibility settings', 
                   horizontalalignment='center', verticalalignment='center', 
                   transform=ax.transAxes, fontsize=12)

        ax.autoscale(enable=True, axis="x")
        ax.autoscale(enable=True, axis="y")

    except IndexError as e:
        log("error", f"IndexError in plot history: {e}")
        if hasattr(state, 'x'):
            log("error", f"state.x length: {len(state.x)}")
        if hasattr(state, 'ylist'):
            log("error", f"state.ylist length: {len(state.ylist)}")
        if hasattr(state, 'monitorLinesNames'):
            log("error", f"state.monitorLinesNames length: {len(state.monitorLinesNames)}")
        if hasattr(state, 'monitorLinesVisibility'):
            log("error", f"state.monitorLinesVisibility length: {len(state.monitorLinesVisibility)}")
        
        # Show error message on plot
        ax.text(0.5, 0.5, f'Error plotting data: {str(e)}\nCheck logs for details', 
               horizontalalignment='center', verticalalignment='center', 
               transform=ax.transAxes, fontsize=10, color='red')
               
    except Exception as e:
        log("error", f"Unexpected error in plot history: {e}")
        ax.text(0.5, 0.5, f'Error plotting data: {str(e)}\nCheck logs for details', 
               horizontalalignment='center', verticalalignment='center', 
               transform=ax.transAxes, fontsize=10, color='red')

    return fig

def provide_binary_restart_guidance():
    """Provide helpful guidance for users encountering binary restart files."""
    log("info", "")
    log("info", "=== BINARY RESTART FILE INFO ===")
    log("info", "Binary restart files detected. This is normal for SU2 simulations.")
    log("info", "")
    log("info", "Current status: Binary parsing is not yet implemented in SU2GUI.")
    log("info", "This does not affect your simulation - only the GUI visualization.")
    log("info", "")
    log("info", "To enable restart file visualization in SU2GUI:")
    log("info", "1. Configure SU2 to output ASCII restart files:")
    log("info", "   - Set OUTPUT_FILES = ['RESTART_ASCII'] in your configuration")
    log("info", "   - Re-run your simulation to generate .csv restart files")
    log("info", "")
    log("info", "2. Convert existing binary files using SU2 tools:")
    log("info", "   - Use SU2_SOL to convert binary restart files to ASCII format")
    log("info", "")
    log("info", "3. Use the File I/O tab in SU2GUI:")
    log("info", "   - Enable 'ASCII restart output' option")
    log("info", "   - This will generate .csv files instead of .dat files")
    log("info", "")
    log("info", "Note: ASCII restart files (.csv) contain the same data as binary")
    log("info", "files but are readable by SU2GUI for visualization and analysis.")
    log("info", "================================")

# Debug function to check history file and state
def debug_history_state():
    """Debug function to check the state of history-related variables"""
    log("info", "=== HISTORY DEBUG INFORMATION ===")
    log("info", f"Case name: {getattr(state, 'case_name', 'NOT SET')}")
    log("info", f"History filename: {getattr(state, 'history_filename', 'NOT SET')}")
    
    if hasattr(state, 'case_name') and hasattr(state, 'history_filename'):
        history_path = BASE / "user" / state.case_name / state.history_filename
        log("info", f"History file path: {history_path}")
        log("info", f"History file exists: {os.path.exists(history_path)}")
        
        if os.path.exists(history_path):
            try:
                file_size = os.path.getsize(history_path)
                log("info", f"History file size: {file_size} bytes")
                
                with open(history_path, 'r') as f:
                    first_lines = [f.readline().strip() for _ in range(3)]
                log("info", f"First 3 lines: {first_lines}")
                
            except Exception as e:
                log("error", f"Error reading history file: {e}")
    
    # Check state variables
    log("info", f"state.x length: {len(getattr(state, 'x', []))}")
    log("info", f"state.ylist length: {len(getattr(state, 'ylist', []))}")
    log("info", f"state.monitorLinesNames: {getattr(state, 'monitorLinesNames', 'NOT SET')}")
    log("info", f"state.monitorLinesVisibility: {getattr(state, 'monitorLinesVisibility', 'NOT SET')}")
    log("info", f"state.global_iter: {getattr(state, 'global_iter', 'NOT SET')}")
    log("info", "=== END HISTORY DEBUG ===")

# Function to create a sample history file for testing
def create_sample_history_file(filepath):
    """Create a sample history file for testing purposes"""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        sample_data = """Outer_Iter,Inner_Iter,Time(min),CL,CD,CL/CD,CMz,CX,CY,CFx,CFy,CMx,CMy,rms[Rho],rms[RhoU],rms[RhoV],rms[RhoE],CLift(Total),CDrag(Total)
1,1,0.001,0.5000,0.0100,50.000,0.0000,0.0000,0.5000,0.0000,0.5000,0.0000,0.0000,-3.123,-4.567,-5.678,-6.789,0.5000,0.0100
2,2,0.002,0.5100,0.0098,52.041,0.0001,0.0001,0.5100,0.0001,0.5100,0.0001,0.0001,-3.023,-4.467,-5.578,-6.689,0.5100,0.0098
3,3,0.003,0.5200,0.0096,54.167,0.0002,0.0002,0.5200,0.0002,0.5200,0.0002,0.0002,-2.923,-4.367,-5.478,-6.589,0.5200,0.0096
4,4,0.004,0.5300,0.0094,56.383,0.0003,0.0003,0.5300,0.0003,0.5300,0.0003,0.0003,-2.823,-4.267,-5.378,-6.489,0.5300,0.0094
5,5,0.005,0.5400,0.0092,58.696,0.0004,0.0004,0.5400,0.0004,0.5400,0.0004,0.0004,-2.723,-4.167,-5.278,-6.389,0.5400,0.0092"""
        
        with open(filepath, 'w') as f:
            f.write(sample_data)
        
        log("info", f"Created sample history file: {filepath}")
        return True
        
    except Exception as e:
        log("error", f"Error creating sample history file: {e}")
        return False

# Function to test history loading
def test_history_loading():
    """Test function to verify history loading works correctly"""
    log("info", "=== TESTING HISTORY LOADING ===")
    
    # Save current state
    original_case_name = getattr(state, 'case_name', None)
    
    # Set up test case
    test_case_name = "test_history"
    state.case_name = test_case_name
    
    # Create test directory and sample file
    test_dir = BASE / "user" / test_case_name
    test_file = test_dir / state.history_filename
    
    if create_sample_history_file(test_file):
        # Test reading the file
        try:
            result = readHistory(test_file)
            log("info", f"Test result: x={len(result[0]) if result[0] else 0}, y={len(result[1]) if result[1] else 0}")
            log("info", "History loading test: PASSED")
        except Exception as e:
            log("error", f"History loading test: FAILED - {e}")
    else:
        log("error", "Could not create test file")
    
    # Restore original state
    if original_case_name:
        state.case_name = original_case_name
        
    log("info", "=== END HISTORY LOADING TEST ===")
