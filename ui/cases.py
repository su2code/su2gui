import shutil
import zipfile, os
import sys
from io import BytesIO
from pathlib import Path

# Add parent directory to path to allow importing from sibling directories
parent_dir = str(Path(__file__).parent.parent.absolute())
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from trame.widgets import markdown
from trame.widgets import vuetify

from ui.fileio import set_json_fileio
from ui.initialization import set_json_initialization
from core.logger import log
from ui.materials import set_json_materials
from ui.numerics import set_json_numerics
from ui.physics import set_json_physics
from core.su2_io import save_json_cfg_file, save_su2mesh
from core.su2_json import updateBCDictListfromJSON
from ui.uicard import server
from ui.mesh import root, mesh_actor, mesh_mapper
from ui.vtk_helper import renderer
from core.solver import proc_SU2, set_json_solver


from pathlib import Path
BASE = Path(__file__).parent.parent
user_path = BASE / "user"
# user_path = "../../user"


state, ctrl = server.state, server.controller


# show the material dialog cards
state.show_manage_case_dialog_card = False
state.case_name = ''
state.case_name_help = ""
state.case_list = []


############# DIALOG CARDS ##############

# Dialog card for managing CASES 
def manage_case_dialog_card():
    with vuetify.VDialog(position='{X:10,Y:10}',
                         width = 650,
                         min_height = 300,
                         transition="dialog-top-transition",
                         v_model=("show_manage_case_dialog_card",False),
                         ):
        with vuetify.VCard():
            vuetify.VCardTitle("Manage Cases",
                           classes="grey lighten-1 py-1 grey--text text--darken-3")
            
            
            with vuetify.VContainer(fluid=True, style = "padding: 20px;"):
            # ####################################################### #
                
                with vuetify.VRow():
                    with vuetify.VCol( classes='col-3'):
                        markdown.Markdown(
                                content=('current_case', "Current Case: "),
                                style="color:black; background-color:white;"
                                )
                    with vuetify.VCol():
                        markdown.Markdown(
                                content=("case_name || 'None'", state.case_name),
                                style="color:black; background-color:white; "
                                )

                with vuetify.VRow():
                    with vuetify.VCol():
                        vuetify.VSelect(
                            v_model=("selected_case_idx", None),
                            items=("case_list",state.case_list),
                            # the name of the list box
                            label="Cases",
                            hide_details=True,
                            dense=True,
                            outlined=True,
                            classes="m-4",
                        )

                with vuetify.VRow():
                    with vuetify.VCol():
                        vuetify.VCheckbox(
                                    v_model=("select_all_cases", False),
                                    label = "Select all cases",
                                    outlined=True,
                                    hide_details=True,
                                    dense=True,
                                )

                with vuetify.VRow():
                    with vuetify.VCol():
                        with vuetify.VBtn("Download", 
                                    click=f"utils.download('output.zip', trigger('download_case'))"
                        ):
                            vuetify.VIcon("mdi-download-box-outline")
                    with vuetify.VCol():
                        with vuetify.VBtn("Delete", 
                                    click=(delete_case, '[selected_case_idx]'),
                                    disabled=("selected_case_idx == case_name || solver_running", False)
                        ):
                            vuetify.VIcon("mdi-trash-can-outline")
                    with vuetify.VCol():
                        with vuetify.VBtn("Load Case", 
                                    click=(load_case, '[selected_case_idx]'),
                                    disabled=("selected_case_idx == case_name || solver_running", False)
                        ):
                            vuetify.VIcon("mdi-folder-edit-outline")
                    with vuetify.VCol():
                        with vuetify.VBtn("New Case", 
                                    disabled=("solver_running",False),
                                    click=open_new_case_dialog
                        ):
                            vuetify.VIcon("mdi-folder-plus-outline")


# Dialog Box for taking case name
def case_name_dialog_card():
    with vuetify.VDialog(position='{X:10,Y:10}',
                         width = 350,
                         transition="dialog-top-transition",
                         v_model=("show_case_name_dialog", True)):
        with vuetify.VCard():
            vuetify.VCardTitle("Start a new case",
                           classes="grey lighten-1 py-1 grey--text text--darken-3")
            with vuetify.VContainer(fluid=True, style = "padding-left: 20px;"):
                    markdown.Markdown(
                        content=("case_name_help", state.case_name_help),
                        style="color:white; background-color:white;"
                        )
                    with vuetify.VCardText():
                        vuetify.VTextField(
                            label="Case Name",
                            v_model=("new_case_name", state.case_name),
                            outlined=True,
                            dense=True,
                            hide_details=True,
                        )
                    vuetify.VCheckbox(
                                    v_model=("delete_all_previous_cases", False),
                                    label = "Delete all previous cases",
                                    outlined=True,
                                    hide_details=True,
                                    dense=True,
                                )
                    
                    with vuetify.VRow(classname= 'pt-4'):
                        with vuetify.VCol():
                            with vuetify.VCardActions():
                                with vuetify.VBtn("Create ", click="trigger('create_new_case')"):
                                    vuetify.VIcon("mdi-folder-plus-outline")
                        with vuetify.VCol():
                            with vuetify.VCardActions():
                                with vuetify.VBtn("Load Case", click=open_manage_case_dialog):
                                    vuetify.VIcon("mdi-folder-edit-outline")



############# BUTTONS ##############

# function to open the new case dialog
def open_new_case_dialog():
    set_cases_list()
    state.delete_all_previous_cases = False
    state.show_manage_case_dialog_card = False
    state.case_name_help = ''
    state.show_case_name_dialog = True

# function to open the manage case dialog
def open_manage_case_dialog():
    set_cases_list()
    state.show_case_name_dialog = False
    state.case_name_help = ''
    state.show_manage_case_dialog_card = True


# function to delete the cases
def delete_case(case_name):
    # if select_all_cases is True, delete all cases
    if state.select_all_cases==True:
        state.select_all_cases=False
        set_cases_list()
        for case in state.case_list:
            delete_case(case)
        return
    if case_name is None or case_name == '' or case_name == state.case_name: 
        return
    # delete the single case
    log('info', f'case name = {case_name}')
    case_path = os.path.join(user_path, case_name)
    try:
        shutil.rmtree(case_path)
        log("info", f"Case '{case_name}' deleted successfully.")
    except FileNotFoundError:
        log("Warn", f"Case '{case_name}' not found. - {case_path}")
    set_cases_list()


# function to download the cases
@ctrl.trigger("download_case")
def download_case():
    case_name = state.selected_case_idx
    if (case_name is None or case_name == '') and state.select_all_cases==False:
        return

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_ref:

        # if select_all_cases is False, download all files in the case folder
        if state.select_all_cases==False:

            # save the cfg file
            save_json_cfg_file(state.filename_json_export,state.filename_cfg_export)

            case_path = os.path.join(user_path, case_name)
            if case_name == '':
                log("Error", "No case selected.") 
                return

            # check if the case path exists
            if not os.path.isdir(case_path):
                log("Error", f"Case '{case_path}' not found.")
                return

            for root, dirs, files in os.walk(case_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    zip_ref.write(file_path, os.path.relpath(file_path, case_path))

        # if select_all_cases is True, download all cases
        else:
            case_path = user_path

            # check if the case path exists
            if not os.path.isdir(case_path):
                log("Error", f"Cases '{case_path}' not found.")
                return

            for root, dirs, files in os.walk(case_path):
                for dir_name in dirs:
                    folder_path = os.path.join(root, dir_name)
                    # Add the directory to the zip file
                    zip_ref.write(folder_path, os.path.relpath(folder_path, case_path))
                    # Add files inside the directory to the zip file
                    for sub_root, sub_dirs, sub_files in os.walk(folder_path):
                        for file_name in sub_files:
                            file_path = os.path.join(sub_root, file_name)
                            zip_ref.write(file_path, os.path.relpath(file_path, case_path))
                        # Stop further walking into subdirectories
                        break

    zip_buffer.seek(0)  # Reset buffer position to the beginning
    log("info", f"Case '{case_name}' downloaded successfully.")
    return zip_buffer.getvalue()



# function to create a new case
@ctrl.trigger("create_new_case")
def create_new_case():
    set_cases_list()

    if state.delete_all_previous_cases == True:
        set_cases_list()
        for case in state.case_list:
            delete_case(case)

    if state.new_case_name is None or state.new_case_name == "":
        state.case_name_help = "> Please enter a valid case name."

    elif state.new_case_name in state.case_list:
        state.case_name_help = "> Case name already exists.  \nPlease enter a different name."

    else:

        state.show_case_name_dialog = False
        reset_values()
        state.case_name = state.new_case_name.replace(" ", "_")
        try:
            os.makedirs(os.path.join(BASE, "user", state.case_name))
            log("info", f"Case '{state.case_name}' created successfully.")
        except OSError as e:
            log("Warn", f"Case '{state.case_name}' already existed.  \n{e}")

        # create history file
        with open(BASE / "user" / state.case_name / state.history_filename, 'w') as f:
            f.write('"Time_Iter","Outer_Iter","Inner_Iter",     "rms[P]"     ,     "rms[U]"     ,     "rms[V]"     ,     "rms[T]"     ,     "rms[nu]"    ')

        log("info", f"Case name set to {state.case_name}")

        if state.delete_all_previous_cases == True:
            set_cases_list()
            for case in state.case_list:
                if case != state.case_name:
                    delete_case(case)


# function to load existing case
def load_case(case_name):
    # save the cfg file for the previous case
    save_json_cfg_file(state.filename_json_export,state.filename_cfg_export)
    if case_name is None or case_name == '':
        log("Error", "No case selected.")
        return
    state.case_name = case_name
    state.show_manage_case_dialog_card = False
    state.show_case_name_dialog = False
    reset_values()
    case_path = os.path.join(user_path, case_name)

    # get the list of files in the case path
    root, dirs, filenames = os.walk(case_path).__next__()
    del dirs
    
    # try to load mesh file first
    for file in filenames:
        if file.endswith(".su2"):
            mesh_path = os.path.join(root, file)
            with open(mesh_path, 'r') as f:
                content = f.read()
                state.su2_file_upload = {
                    "name": os.path.basename(mesh_path),
                    "size" : os.stat(mesh_path).st_size,
                    "content": content,
                    "type": "text/plain",
                }
            state.dirty('su2_file_upload')
            state.flush()
            break

    # try to load config file
    for file in filenames:
        if file.endswith(".cfg"):
            config_path = os.path.join(root, file)
            with open(config_path, 'r') as f:
                content = f.read()

            state.cfg_file_upload = {
                "name": os.path.basename(config_path),
                "size" : os.stat(config_path).st_size,
                "content": content,
                "type": "text/plain",
            }

            for line in content.splitlines():
                if 'RESTART_FILENAME' in line:
                    _, value = line.split('=', 1)
                    state.restart_filename = value.strip()
                    break

            log("info", f"Config file {state.cfg_file_upload['name']} loaded successfully.")

            # load the restart file
            log('info', f"Restart file name = {state.restart_filename}")
            if state.restart_filename == None or state.restart=='':
                state.restart_filename = 'restart'
                log("info", f"Restart file not found in the config file.")
                return

            # got the restart file name, now try to load the restart file
            restart_path = os.path.join(root, state.restart_filename) 

            # check if the restart file exists
            if not os.path.isfile(restart_path):
                # try to add extension to the file if not found
                if not (restart_path.endswith(".dat") or restart_path.endswith(".csv")):
                    if 'OUTPUT_FILES' in state.jsonData and 'RESTART_ASCII' in state.jsonData['OUTPUT_FILES']:
                        restart_path += ".csv"
                    else:
                        restart_path += ".dat"

                # check if the restart file exists
                if not os.path.isfile(restart_path):
                    # check if restart file is lock file, and rename it to restart file
                    if os.path.isfile(restart_path + ".lock"):
                        os.rename(restart_path + ".lock", restart_path)
                    else:
                        log("info", f"Restart file '{restart_path}' not found in the case.")
                        return

            if restart_path.endswith(".dat"):
                with open(restart_path, 'rb') as f:
                    content = f.read()
                    state.restartFile = {
                        "name": os.path.basename(restart_path),
                        "size" : os.stat(restart_path).st_size,
                        "content": content,
                        "type": "text/plain",
                    }
            else:
                with open(restart_path, 'r') as f:
                    content = f.read()
                    state.restartFile = {
                        "name": os.path.basename(restart_path),
                        "size" : os.stat(restart_path).st_size,
                        "content": content,
                        "type": "text/plain",
                    }

            log("info", f"Restart file '{state.restart_filename}' loaded successfully.")

            break

    log("info", f"Case '{case_name}' loaded successfully.")


#############################################
# Button to download the specific output files (currently not is use)
@ctrl.trigger("download_output_files")
def download_outputs():
    files_directory = BASE / "user" / state.case_name 
    
    save_json_cfg_file(state.filename_json_export,state.filename_cfg_export)
    save_su2mesh(root,state.jsonData['MESH_FILENAME'])

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_ref:
        for filename, list in state.output_list.items():
            if list[0]:
                file_path = os.path.join(files_directory, filename)
                if os.path.isfile(file_path):
                    with open(file_path, 'r') as f:
                        zip_ref.writestr(zinfo_or_arcname=list[1], data=f.read())
                else:
                    log("Warn", f"{file_path} does not exist and will not be included in the zip file.")
    
    zip_buffer.seek(0)  # Reset buffer position to the beginning
    update_manage_case_dialog_card()
    log("info", f"Zip file downloaded successfully.")
    return zip_buffer.getvalue()


#############################################

# get the names of folders under './user' and set case names list
def set_cases_list():
    try:
        contents = os.listdir(user_path)
        state.case_list = [item for item in contents if os.path.isdir(os.path.join(user_path, item))]
    except FileNotFoundError:
        log('error', f"Path to User Folder not found: '{user_path}'")
    log('info', f"Cases list = {state.case_list}")

# function to start case from the terminal
def case_args(case_name):
    set_cases_list()
    state.new_case_name = case_name
    if case_name in state.case_list:
        load_case(case_name)
    else:
        create_new_case()
    state.flush()


# reset the values, when a new case is created
def reset_values():
    # we need to terminate or kill the result process here 
    if state.solver_running:
        state.solver_running = False
        state.solver_icon="mdi-play-circle"
        # proc_SU2.kill()

    
    # reset the input files
    state.restartFile = None
    state.su2_file_upload = None
    state.cfg_file_upload = None


    state.monitorLinesVisibility = []
    state.monitorLinesNames = []
    state.monitorLinesRange = []

    state.initialize=-1
    # number of dimensions of the mesh (2 or 3)
    state.nDim = 2

    # which boundary is selected?
    state.selectedBoundaryName="none"
    state.selectedBoundaryIndex = 0

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

    state.su2_meshfile="mesh_out.su2"

    state.selectedBoundary = 0

    mesh_actor_list = [{"id":0,"name":"internal","mesh":mesh_actor}]

    mesh_actor.SetMapper(mesh_mapper)
    mesh_actor.SetObjectName("initial_square")

    # Mesh: Setup default representation to surface
    mesh_actor.GetProperty().SetRepresentationToSurface()
    mesh_actor.GetProperty().SetPointSize(1)
    # show the edges
    mesh_actor.GetProperty().EdgeVisibilityOn()
    # color is based on field values
    renderer.AddActor(mesh_actor)

    # set su2 logs to empty
    state.su2_logs = '' 

    # # reset jsondata
    # with open('./user/config.json', 'r') as f:
    #     state.jsonData = json.load(f)

    # state.dirty('jsonData')
    
    # # save the cfg file
    # # save_json_cfg_file(state.filename_json_export,state.filename_cfg_export)

    # updateBCDictListfromJSON()
    # # set all physics states from the json file
    # # this is reading the config file (done by read_json_data) and filling it into the GUI menu's
    # set_json_physics()
    # set_json_initialization()
    # set_json_numerics()
    # set_json_solver()
    # set_json_fileio()
    # set_json_materials()

# when the manage case dialog card is opened, update the cases list
def update_manage_case_dialog_card():
    set_cases_list()
    state.show_manage_case_dialog_card = not state.show_manage_case_dialog_card