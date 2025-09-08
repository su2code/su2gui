import sys
from pathlib import Path

# Add parent directory to path to allow importing from sibling directories
parent_dir = str(Path(__file__).parent.parent.absolute())
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from ui.uicard import ui_card, ui_subcard, server
from trame.widgets import vuetify
from core.logger import log
from core.variables import *
from core.su2_py_wrapper import save_json_cfg_py_file
import json


state, ctrl = server.state, server.controller

# Initialize core data structures first (critical for preventing NoneType errors)
if not hasattr(state, 'variables') or state.variables is None:
    state.variables = {}
if not hasattr(state, 'derived_parameters') or state.derived_parameters is None:
    state.derived_parameters = {}

# Initialize default state variables for Variables
state.variables_list = []
state.derived_parameters_list = []

# Initialize state for all handlers
state.addVariable = False
state.editVariable = False
state.updateVariable = False
state.deleteVariable = False
state.addDerivedParameter = False
state.editDerivedParameter = False
state.updateDerivedParameter = False
state.deleteDerivedParameter = False
state.generatePythonWrapper = False
# state.generatePythonWrapperWithDynamicTemp = False  # Moved to boundaries.py
state.confirmDeleteVariable = False
state.confirmDeleteDerivedParameter = False
# state.showAddVariableDialog = False
# state.showAddDerivedParameterDialog = False
# state.showEditVariableDialog = False
# state.showEditDerivedParameterDialog = False

# Initialize state for dynamic wall temperature (moved to boundaries.py)
# state.dynamic_temp_enabled = False
# state.dynamic_temp_function = "293.0 + 257.0 * sin(pi * 0.5 * time)"
# state.dynamic_temp_wrapper_filename = "run_su2.py"
state.last_generated_wrapper_path = ""
state.show_wrapper_path_info = False

# Initialize button click trigger variables  
state.openVariableDialog = False
state.openDerivedDialog = False
state.cancelVariableDialog = False
state.cancelDerivedDialog = False

# Initialize values to prevent "object has no attribute" errors
state.new_variable_name = ""
state.new_variable_value = ""
state.new_variable_description = ""
state.edit_variable_name = ""
state.edit_variable_value = ""
state.edit_variable_description = ""
state.new_derived_parameter_name = ""
state.new_derived_parameter_definition = ""
state.new_derived_parameter_description = ""
state.edit_derived_parameter_name = ""
state.edit_derived_parameter_definition = ""
state.edit_derived_parameter_description = ""
state.python_wrapper_filename = "run_su2.py"

# Dialog state variables
state.add_variable_dialog = False
state.edit_variable_dialog = False
state.add_derived_parameter_dialog = False
state.edit_derived_parameter_dialog = False
state.confirm_delete_variable_dialog = False
state.confirm_delete_derived_parameter_dialog = False
state.item_to_delete = ""
state.item_type_to_delete = ""

# Button state variables for synchronization
state.can_add_variable = True
state.can_add_derived = True
state.can_edit_variable = False
state.can_edit_derived = False
state.can_delete_variable = False
state.can_delete_derived = False
state.can_generate_wrapper = True

# Dialog open state tracking
state.variable_dialog_open = False
state.derived_dialog_open = False

# Form validation state variables
state.variable_form_valid = False
state.derived_form_valid = False
state.edit_variable_form_valid = False
state.edit_derived_form_valid = False

# Variables selection indices for main UI  
state.variables_main_selection = 0

# List options for variables management
state.LVariablesMain = [
    {"text": "Variables", "value": 0},
    {"text": "Derived Parameters", "value": 1}, 
    {"text": "Python Wrapper", "value": 2},
]

###############################################################
# ACTION HANDLER FUNCTIONS 
###############################################################

def edit_variable_action(event, item_name):
    # Handle JSON-to-Python data conversion
    item_name = json.loads(item_name) if isinstance(item_name, str) else item_name
    
    if not hasattr(state, 'variables') or item_name not in state.variables:
        log("error", f"Variable {item_name} not found")
        return
    
    var = state.variables[item_name]
    state.edit_variable_name = item_name
    state.edit_variable_value = var.get("value", "")
    state.edit_variable_description = var.get("description", "")
    state.edit_variable_dialog = True

def delete_variable_action(event, item_name):
    # Handle variable delete    
    item_name = json.loads(item_name) if isinstance(item_name, str) else item_name
    
    if not hasattr(state, 'variables') or item_name not in state.variables:
        log("error", f"Variable {item_name} not found")
        return
    
    # Show confirmation dialog
    state.item_to_delete = item_name
    state.item_type_to_delete = "variable"
    state.confirm_delete_variable_dialog = True

def edit_derived_parameter_action(event, item_name):
    # Handle derived parameter edit    
    item_name = json.loads(item_name) if isinstance(item_name, str) else item_name
    
    if not hasattr(state, 'derived_parameters') or item_name not in state.derived_parameters:
        log("error", f"Derived parameter {item_name} not found")
        return
    
    param = state.derived_parameters[item_name]
    state.edit_derived_parameter_name = item_name
    state.edit_derived_parameter_definition = param.get("definition", "")
    state.edit_derived_parameter_description = param.get("description", "")
    state.edit_derived_parameter_dialog = True

def delete_derived_parameter_action(event, item_name):
    # Handle derived parameter delete     
    item_name = json.loads(item_name) if isinstance(item_name, str) else item_name
    
    if not hasattr(state, 'derived_parameters') or item_name not in state.derived_parameters:
        log("error", f"Derived parameter {item_name} not found")
        return
      # Show confirmation dialog
    state.item_to_delete = item_name
    state.item_type_to_delete = "derived_parameter"
    state.confirm_delete_derived_parameter_dialog = True

def handle_click(action, *args):
    # Generic click handler 
    try:
        if hasattr(ctrl, action) and callable(getattr(ctrl, action)):
            getattr(ctrl, action)(*args)
        else:
            log("error", f"Action {action} not found in controller")
    except Exception as e:
        log("error", f"Error handling click action {action}: {str(e)}")

###############################################################
# PIPELINE CARD : VARIABLES
###############################################################
def variables_card():
    # the variables management 
    with ui_card(title="Variables", ui_name="Variables"):
        log("info", "     ## Variables Management ##")
        
        # Main selection dropdown for variables management
        with vuetify.VRow(classes="pt-2"):
            with vuetify.VCol(cols="12"):
                vuetify.VSelect(
                    v_model=("variables_main_selection", 0),
                    items=("Object.values(LVariablesMain)",),
                    label="Variables Management",
                    hide_details=True,
                    dense=True,
                    outlined=True,
                    classes="pt-1 mt-1",
                )

###############################################################
# PIPELINE SUBCARD : VARIABLES
###############################################################
def variables_subcard():
    # the variables management subcards.
    
    # Variables subcard - shows when variables_main_selection is 0
    with ui_subcard(title="Variables", sub_ui_name="subvariables_vars"):
        with vuetify.VContainer(fluid=True):
            with vuetify.VRow():
                with vuetify.VCol(cols="12"):
                    vuetify.VCardSubtitle("Define variables that can be used in the configuration")
                      # Variables data table with action buttons
                    with vuetify.VDataTable(
                        headers=[
                            {"text": "Name", "value": "name", "sortable": True},
                            {"text": "Value", "value": "value", "sortable": True},
                            {"text": "Description", "value": "description", "sortable": False},
                            {"text": "Actions", "value": "actions", "sortable": False, "width": "120px"}
                        ],
                        items=("variables_list", []),
                        elevation=1,
                        items_per_page=5,
                        item_key="name",
                        __properties=[("v_slot_item_actions", "v-slot:item.actions")]
                    ):# Add action buttons for each row
                        with vuetify.Template(v_slot_item_actions="{ item }"):
                            vuetify.VBtn(
                                icon=True,
                                small=True,
                                color="primary",
                                click=(ctrl.edit_variable, "[$event, item.name]"),
                                children=[vuetify.VIcon("mdi-pencil")]
                            )
                            vuetify.VBtn(
                                icon=True,
                                small=True,
                                color="error",
                                click=(ctrl.delete_variable, "[$event, item.name]"),
                                children=[vuetify.VIcon("mdi-delete")]
                            )
                    with vuetify.VRow(classes="mt-4"):
                        with vuetify.VCol(cols="12"):
                            vuetify.VBtn(
                                "Add Variable",
                                color="primary", 
                                click="openVariableDialog = !openVariableDialog",
                                disabled=("!can_add_variable",),
                                block=True
                            )

    # Derived Parameters subcard 
    with ui_subcard(title="Derived Parameters", sub_ui_name="subvariables_params"):
        with vuetify.VContainer(fluid=True):
            with vuetify.VRow():
                with vuetify.VCol(cols="12"):
                    vuetify.VCardSubtitle("Define derived parameters based on variables")
                      # Derived Parameters data table with action buttons
                    with vuetify.VDataTable(
                        headers=[
                            {"text": "Name", "value": "name", "sortable": True},
                            {"text": "Definition", "value": "definition", "sortable": True},
                            {"text": "Description", "value": "description", "sortable": False},
                            {"text": "Actions", "value": "actions", "sortable": False, "width": "120px"}
                        ],
                        items=("derived_parameters_list", []),
                        elevation=1,
                        items_per_page=5,
                        item_key="name",
                        __properties=[("v_slot_item_actions", "v-slot:item.actions")]
                    ):# Add action buttons for each row
                        with vuetify.Template(v_slot_item_actions="{ item }"):
                            vuetify.VBtn(
                                icon=True,
                                small=True,
                                color="primary",
                                click=(ctrl.edit_derived_parameter, "[$event, item.name]"),
                                children=[vuetify.VIcon("mdi-pencil")]
                            )
                            vuetify.VBtn(
                                icon=True,
                                small=True,
                                color="error",
                                click=(ctrl.delete_derived_parameter, "[$event, item.name]"),
                                children=[vuetify.VIcon("mdi-delete")]
                            )
                    with vuetify.VRow(classes="mt-4"):
                        with vuetify.VCol(cols="12"):
                            vuetify.VBtn(
                                "Add Derived Parameter",
                                color="primary", 
                                click="openDerivedDialog = !openDerivedDialog",
                                disabled=("!can_add_derived",),
                                block=True
                            )    # Python Wrapper subcard - shows when variables_main_selection is 2
    with ui_subcard(title="Python Wrapper", sub_ui_name="subvariables_wrapper"):
        with vuetify.VContainer(fluid=True):
            with vuetify.VRow():
                with vuetify.VCol(cols="12"):
                    vuetify.VCardSubtitle("Generate Python wrapper for SU2 execution")
                    
                    # WRAPPER GENERATION SECTION
                    with vuetify.VRow(classes="mt-4"):
                        with vuetify.VCol(cols="8"):
                            vuetify.VTextField(
                                v_model=("python_wrapper_filename", "run_su2.py"),
                                label="Standard Python wrapper filename",
                                outlined=True,
                                dense=True,
                            )
                        with vuetify.VCol(cols="4"):
                            vuetify.VBtn(
                                "Generate Standard Wrapper",
                                color="primary",
                                click="generatePythonWrapper = !generatePythonWrapper",
                                disabled=("!can_generate_wrapper",),
                                block=True
                            )
                      # INFO TEXT
                    with vuetify.VRow(classes="mt-2"):
                        with vuetify.VCol(cols="12"):
                            vuetify.VCardText(
                                "This will generate a Python script that includes all defined variables "
                                "and derived parameters for use with SU2 simulations."
                            )
                      # GENERATED FILE PATH DISPLAY
                    with vuetify.VRow(classes="mt-2", v_if=("show_wrapper_path_info",)):
                        with vuetify.VCol(cols="12"):
                            with vuetify.VAlert(
                                type="success",
                                outlined=True,
                                dense=True,
                                dismissible=True,
                                v_model=("show_wrapper_path_info", False)
                            ):
                                with vuetify.VRow(no_gutters=True):
                                    with vuetify.VCol(cols="12"):
                                        vuetify.VIcon("mdi-check-circle", color="success", classes="mr-2")
                                        "Wrapper generated successfully!"
                                    with vuetify.VCol(cols="12", classes="mt-1"):
                                        vuetify.VTextField(
                                            v_model=("last_generated_wrapper_path", ""),
                                            label="Generated File Location",
                                            readonly=True,
                                            dense=True,
                                            outlined=True,
                                            prepend_icon="mdi-file-code",
                                            append_icon="mdi-content-copy",
                                            click_append="copyPathToClipboard = !copyPathToClipboard"
                                        )

###############################################################
# Dialog boxes for Variables Management
###############################################################
def variables_dialog_cards():
    """Create all the dialog boxes for variables management."""
    
    # Add Variable Dialog
    with vuetify.VDialog(v_model=("add_variable_dialog", False), max_width="500px", persistent=True, close_on_click=False):
        with vuetify.VCard():
            vuetify.VCardTitle(
                "Add Variable",
                classes="grey lighten-1 py-2 grey--text text--darken-3"
            )
            with vuetify.VCardText():
                with vuetify.VContainer():
                    with vuetify.VRow():
                        with vuetify.VCol(cols="12"):
                            vuetify.VTextField(
                                v_model=("new_variable_name", ""),
                                label="Variable Name",
                                hint="e.g., __WIDTH__, __AMPLITUDE__",
                                required=True,
                                outlined=True,
                                dense=True
                            )
                        with vuetify.VCol(cols="12"):
                            vuetify.VTextField(
                                v_model=("new_variable_value", ""),
                                label="Variable Value",
                                hint="e.g., 0.055, 1.4",
                                required=True,
                                outlined=True,
                                dense=True
                            )
                        with vuetify.VCol(cols="12"):
                            vuetify.VTextField(
                                v_model=("new_variable_description", ""),
                                label="Description (Optional)",
                                hint="Brief description of the variable",
                                outlined=True,
                                dense=True
                            )
            with vuetify.VCardActions():
                vuetify.VSpacer()
                vuetify.VBtn(
                    "Cancel",
                    color="grey",
                    text=True,                    click="cancelVariableDialog = !cancelVariableDialog"
                )
                vuetify.VBtn(
                    "Save",
                    color="primary",
                    text=True,
                    disabled=("!variable_form_valid",),
                    click="addVariable = !addVariable"
                )
    
    # Edit Variable Dialog
    with vuetify.VDialog(v_model=("edit_variable_dialog", False), max_width="500px", persistent=True, close_on_click=False):
        with vuetify.VCard():
            vuetify.VCardTitle(
                "Edit Variable",
                classes="grey lighten-1 py-2 grey--text text--darken-3"
            )
            with vuetify.VCardText():
                with vuetify.VContainer():
                    with vuetify.VRow():
                        with vuetify.VCol(cols="12"):
                            vuetify.VTextField(
                                v_model=("edit_variable_name", ""),
                                label="Variable Name",
                                disabled=True,
                                outlined=True,
                                dense=True
                            )
                        with vuetify.VCol(cols="12"):                            vuetify.VTextField(
                                v_model=("edit_variable_value", ""),
                                label="Variable Value",
                                required=True,
                                outlined=True,
                                dense=True
                            )
                        with vuetify.VCol(cols="12"):
                            vuetify.VTextField(
                                v_model=("edit_variable_description", ""),
                                label="Description (Optional)",
                                outlined=True,
                                dense=True
                            )
            with vuetify.VCardActions():
                vuetify.VSpacer()
                vuetify.VBtn(
                    "Cancel",
                    color="grey",
                    text=True,                    click="edit_variable_dialog = false"
                )
                vuetify.VBtn(
                    "Update",
                    color="primary",
                    text=True,
                    disabled=("!edit_variable_form_valid",),
                    click="updateVariable = !updateVariable"
                )
    
    # Add Derived Parameter Dialog
    with vuetify.VDialog(v_model=("add_derived_parameter_dialog", False), max_width="600px", persistent=True, close_on_click=False):
        with vuetify.VCard():
            vuetify.VCardTitle(
                "Add Derived Parameter",
                classes="grey lighten-1 py-2 grey--text text--darken-3"
            )
            with vuetify.VCardText():
                with vuetify.VContainer():
                    with vuetify.VRow():
                        with vuetify.VCol(cols="12"):
                            vuetify.VTextField(
                                v_model=("new_derived_parameter_name", ""),
                                label="Parameter Name",
                                hint="e.g., p_tot, p_drop",
                                required=True,
                                outlined=True,
                                dense=True
                            )
                        with vuetify.VCol(cols="12"):
                            vuetify.VTextarea(
                                v_model=("new_derived_parameter_definition", ""),
                                label="Parameter Definition",                                hint="e.g., PRESSURE + 0.5 * DENSITY * pow(VELOCITY_X, 2)",
                                required=True,
                                outlined=True,
                                rows=3,
                                auto_grow=True
                            )
                        with vuetify.VCol(cols="12"):
                            vuetify.VTextField(
                                v_model=("new_derived_parameter_description", ""),
                                label="Description (Optional)",
                                hint="Brief description of the derived parameter",
                                outlined=True,                                dense=True
                            )
            with vuetify.VCardActions():
                vuetify.VSpacer()
                vuetify.VBtn(
                    "Cancel",
                    color="grey",
                    text=True,                    click="cancelDerivedDialog = !cancelDerivedDialog"
                )
                vuetify.VBtn(
                    "Save",
                    color="primary",
                    text=True,
                    disabled=("!derived_form_valid",),
                    click="addDerivedParameter = !addDerivedParameter"
                )
      
    # Edit Derived Parameter Dialog
    with vuetify.VDialog(v_model=("edit_derived_parameter_dialog", False), max_width="600px", persistent=True, close_on_click=False):
        with vuetify.VCard():
            vuetify.VCardTitle(
                "Edit Derived Parameter",
                classes="grey lighten-1 py-2 grey--text text--darken-3"
            )
            with vuetify.VCardText():
                with vuetify.VContainer():
                    with vuetify.VRow():
                        with vuetify.VCol(cols="12"):
                            vuetify.VTextField(
                                v_model=("edit_derived_parameter_name", ""),
                                label="Parameter Name",
                                disabled=True,
                                outlined=True,
                                dense=True
                            )
                        with vuetify.VCol(cols="12"):
                            vuetify.VTextarea(
                                v_model=("edit_derived_parameter_definition", ""),                                label="Parameter Definition",
                                required=True,
                                outlined=True,
                                rows=3,
                                auto_grow=True
                            )
                        with vuetify.VCol(cols="12"):
                            vuetify.VTextField(
                                v_model=("edit_derived_parameter_description", ""),
                                label="Description (Optional)",
                                outlined=True,
                                dense=True
                            )
            with vuetify.VCardActions():
                vuetify.VSpacer()
                vuetify.VBtn(
                    "Cancel",
                    color="grey",
                    text=True,
                    click="edit_derived_parameter_dialog = false"
                )
                vuetify.VBtn(
                    "Update",                    color="primary",
                    text=True,
                    disabled=("!edit_derived_form_valid",),
                    click="updateDerivedParameter = !updateDerivedParameter"
                )

    # Confirmation dialog for deleting variables
    with vuetify.VDialog(v_model=("confirm_delete_variable_dialog", False), max_width="400px", persistent=True):
        with vuetify.VCard():
            vuetify.VCardTitle(
                "Confirm Delete",
                classes="error white--text py-2"
            )
            with vuetify.VCardText(classes="pt-4"):
                "Are you sure you want to delete this variable? This action cannot be undone."
            with vuetify.VCardActions():
                vuetify.VSpacer()
                vuetify.VBtn(
                    "Cancel",
                    color="grey",
                    text=True,
                    click="confirm_delete_variable_dialog = false"
                )
                vuetify.VBtn(
                    "Delete",
                    color="error",                    text=True,
                    click="confirmDeleteVariable = !confirmDeleteVariable"
                )

    # Confirmation dialog for deleting derived parameters
    with vuetify.VDialog(v_model=("confirm_delete_derived_parameter_dialog", False), max_width="400px", persistent=True):
        with vuetify.VCard():
            vuetify.VCardTitle(
                "Confirm Delete",
                classes="error white--text py-2"
            )
            with vuetify.VCardText(classes="pt-4"):
                "Are you sure you want to delete this derived parameter? This action cannot be undone."
            with vuetify.VCardActions():
                vuetify.VSpacer()
                vuetify.VBtn(
                    "Cancel",
                    color="grey",
                    text=True,                    click="confirm_delete_derived_parameter_dialog = false"
                )
                vuetify.VBtn(
                    "Delete",
                    color="error",
                    text=True,
                    click="confirmDeleteDerivedParameter = !confirmDeleteDerivedParameter"
                )

###############################################################
# State change handlers for main selection
###############################################################
@state.change("variables_main_selection")
def update_variables_main_selection(variables_main_selection, **kwargs):
    """Update the active subcard based on main selection."""
    log("info", f"Variables main selection: {variables_main_selection}")
    
    if state.active_ui == "Variables":
        if variables_main_selection == 0:
            state.active_sub_ui = "subvariables_vars"
        elif variables_main_selection == 1:
            state.active_sub_ui = "subvariables_params"
        elif variables_main_selection == 2:
            state.active_sub_ui = "subvariables_wrapper"
        else:
            state.active_sub_ui = "subvariables_vars"  # Default

###############################################################
# Computed properties for the UI
###############################################################
@state.change("variables")
def update_variables_list(variables, **kwargs):
    """Update the variables list for the UI when variables change."""
    variables_list = []
    print(state.variables_list)
    print(state.variables)
    if hasattr(variables, '__iter__') and not isinstance(variables, bool) and isinstance(variables, dict):
        for name, var in variables.items():
            if isinstance(var, dict):  # Make sure var is a dictionary
                variables_list.append({
                    "name": name,
                    "value": var.get("value", ""),
                    "description": var.get("description", ""),                    "actions": name  # Pass the name for action buttons
                })
            else:
                log("error", f"Invalid variable format: {name} = {var}")
    else:
        log("warning", f"variables is not iterable or not a dict: {type(variables)}, value: {variables}")
    state.variables_list = variables_list
    
    # Update button states based on data availability
    update_button_states()

@state.change("derived_parameters")
def update_derived_parameters_list(derived_parameters, **kwargs):
    """Update the derived parameters list for the UI when parameters change."""
    derived_parameters_list = []
    if derived_parameters:
        for name, param in derived_parameters.items():
            if isinstance(param, dict):  # Make sure param is a dictionary
                derived_parameters_list.append({
                    "name": name,
                    "definition": param.get("definition", ""),
                    "description": param.get("description", ""),
                    "actions": name  # Pass the name for action buttons
                })
            else:
                log("error", f"Invalid derived parameter format: {name} = {param}")
    state.derived_parameters_list = derived_parameters_list
    
    # Update button states based on data availability
    update_button_states()

# Form validation state watchers
@state.change("new_variable_name", "new_variable_value")
def update_variable_form_validation(**kwargs):
    """Update variable form validation state when fields change."""
    state.variable_form_valid = get_variable_form_valid()

@state.change("new_derived_parameter_name", "new_derived_parameter_definition")
def update_derived_form_validation(**kwargs):
    """Update derived parameter form validation state when fields change."""
    state.derived_form_valid = get_derived_form_valid()

@state.change("edit_variable_value")
def update_edit_variable_form_validation(**kwargs):
    """Update edit variable form validation state when field changes."""
    state.edit_variable_form_valid = get_edit_variable_form_valid()

@state.change("edit_derived_parameter_definition")
def update_edit_derived_form_validation(**kwargs):
    """Update edit derived parameter form validation state when field changes."""
    state.edit_derived_form_valid = get_edit_derived_form_valid()

# Button state management function
def update_button_states():
    """Update button states based on current application state."""
    # Generate wrapper is only available if we have variables or derived parameters
    has_data = (
        (hasattr(state, 'variables') and len(state.variables) > 0) or
        (hasattr(state, 'derived_parameters') and len(state.derived_parameters) > 0)
    )
    
    # Only update if not currently in a dialog operation
    if not state.variable_dialog_open and not state.derived_dialog_open:
        state.can_generate_wrapper = has_data and hasattr(state, 'case_name') and state.case_name

# Form validation functions
def get_variable_form_valid():
    """Check if variable form is valid for enabling Save button."""
    return bool(
        state.new_variable_name and 
        state.new_variable_name.strip() and
        state.new_variable_value and 
        state.new_variable_value.strip()
    )

def get_derived_form_valid():
    """Check if derived parameter form is valid for enabling Save button."""
    return bool(
        state.new_derived_parameter_name and 
        state.new_derived_parameter_name.strip() and
        state.new_derived_parameter_definition and 
        state.new_derived_parameter_definition.strip()
    )

def get_edit_variable_form_valid():
    """Check if edit variable form is valid for enabling Update button."""
    return bool(
        state.edit_variable_value and 
        state.edit_variable_value.strip()
    )

def get_edit_derived_form_valid():
    """Check if edit derived parameter form is valid for enabling Update button."""
    return bool(
        state.edit_derived_parameter_definition and 
        state.edit_derived_parameter_definition.strip()
    )

###############################################################
# Controller functions for the UI
###############################################################

# Button click handlers with proper state management
@state.change("openVariableDialog")
def open_variable_dialog(**kwargs):
    """Open the add variable dialog with proper state management."""
    if not state.can_add_variable:
        log("warning", "Cannot add variable - button is disabled")
        return
    
    # Clear form fields
    state.new_variable_name = ""
    state.new_variable_value = ""
    state.new_variable_description = ""
    
    # Update dialog states
    state.add_variable_dialog = True
    state.variable_dialog_open = True
    
    # Update button states
    state.can_add_variable = False  # Prevent multiple dialogs
    
    log("info", "Variable dialog opened")

@state.change("openDerivedDialog")
def open_derived_dialog(**kwargs):
    """Open the add derived parameter dialog with proper state management."""
    if not state.can_add_derived:
        log("warning", "Cannot add derived parameter - button is disabled")
        return
    
    # Clear form fields
    state.new_derived_parameter_name = ""
    state.new_derived_parameter_definition = ""
    state.new_derived_parameter_description = ""
    
    # Update dialog states
    state.add_derived_parameter_dialog = True
    state.derived_dialog_open = True
      # Update button states
    state.can_add_derived = False  # Prevent multiple dialogs
    
    log("info", "Derived parameter dialog opened")

# Cancel dialog handlers with proper state management
@state.change("cancelVariableDialog")
def cancel_variable_dialog(**kwargs):
    """Cancel the add variable dialog and reset button states."""
    # Close dialog
    state.add_variable_dialog = False
    state.variable_dialog_open = False
    
    # Clear form fields
    state.new_variable_name = ""
    state.new_variable_value = ""
    state.new_variable_description = ""
    
    # Re-enable the add button
    state.can_add_variable = True
    
    log("info", "Variable dialog cancelled")

@state.change("cancelDerivedDialog")
def cancel_derived_dialog(**kwargs):
    """Cancel the add derived parameter dialog and reset button states."""
    # Close dialog
    state.add_derived_parameter_dialog = False
    state.derived_dialog_open = False
    
    # Clear form fields
    state.new_derived_parameter_name = ""
    state.new_derived_parameter_definition = ""
    state.new_derived_parameter_description = ""
    
    # Re-enable the add button
    state.can_add_derived = True
    
    log("info", "Derived parameter dialog cancelled")

@state.change("showAddVariableDialog")
def show_add_variable_dialog(**kwargs):
    """Show the add variable dialog."""
    state.new_variable_name = ""
    state.new_variable_value = ""
    state.new_variable_description = ""
    state.add_variable_dialog = True

@state.change("addVariable")
def add_variable_ui(**kwargs):
    """Add a new variable from the UI."""
    # Prevent recursive calls by checking if dialog is actually open
    if not state.add_variable_dialog:
        return
        
    # Validate input
    valid, error_msg = validate_variable_input(state.new_variable_name, state.new_variable_value)
    if not valid:
        log("error", f"Failed to add variable: {error_msg}")
        return
      # Check if variable already exists
    if hasattr(state, 'variables') and state.variables and state.new_variable_name in state.variables:
        log("error", f"Variable '{state.new_variable_name}' already exists")
        return
      # Add the variable
    try:
        add_variable(state.new_variable_name, state.new_variable_value, state.new_variable_description)
        # Close dialog and clear form only after successful addition
        state.add_variable_dialog = False
        state.variable_dialog_open = False
        state.new_variable_name = ""
        state.new_variable_value = ""
        state.new_variable_description = ""
        
        # Re-enable the add button
        state.can_add_variable = True
        
        log("info", f"Variable '{state.new_variable_name}' added successfully")
    except Exception as e:
        log("error", f"Failed to add variable: {str(e)}")
        # Re-enable button even on error so user can try again
        state.can_add_variable = True

@state.change("updateVariable")
def update_variable_ui(**kwargs):
    """Update an existing variable from the UI."""
    # Prevent recursive calls by checking if dialog is actually open
    if not state.edit_variable_dialog:
        return
        
    # Validate input
    valid, error_msg = validate_variable_input(state.edit_variable_name, state.edit_variable_value)
    if not valid:
        log("error", f"Failed to update variable: {error_msg}")
        return
    
    var_name = state.edit_variable_name
    var_value = state.edit_variable_value
    var_description = state.edit_variable_description
    
    # Update the variable
    try:
        if not hasattr(state, 'variables'):
            state.variables = {}
        
        state.variables[var_name] = {
            "value": var_value,
            "description": var_description
        }
        state.dirty("variables")
        
        # Close dialog and clear form only after successful update
        state.edit_variable_dialog = False
        state.edit_variable_name = ""
        state.edit_variable_value = ""
        state.edit_variable_description = ""
        log("info", f"Variable '{var_name}' updated successfully")
    except Exception as e:
        log("error", f"Failed to update variable: {str(e)}")

@state.change("addDerivedParameter")
def add_derived_parameter_ui(**kwargs):
    """Add a new derived parameter from the UI."""
    # Prevent recursive calls by checking if dialog is actually open
    if not state.add_derived_parameter_dialog:
        return
        
    # Validate input
    valid, error_msg = validate_derived_parameter_input(state.new_derived_parameter_name, state.new_derived_parameter_definition)
    if not valid:
        log("error", f"Failed to add derived parameter: {error_msg}")
        return
      # Check if parameter already exists
    if hasattr(state, 'derived_parameters') and state.derived_parameters and state.new_derived_parameter_name in state.derived_parameters:
        log("error", f"Derived parameter '{state.new_derived_parameter_name}' already exists")
        return
      # Add the derived parameter
    try:
        add_derived_parameter(
            state.new_derived_parameter_name,
            state.new_derived_parameter_definition,
            state.new_derived_parameter_description
        )
        # Close dialog and clear form only after successful addition
        state.add_derived_parameter_dialog = False
        state.derived_dialog_open = False
        state.new_derived_parameter_name = ""
        state.new_derived_parameter_definition = ""
        state.new_derived_parameter_description = ""
        
        # Re-enable the add button
        state.can_add_derived = True
        
        log("info", f"Derived parameter '{state.new_derived_parameter_name}' added successfully")
    except Exception as e:
        log("error", f"Failed to add derived parameter: {str(e)}")
        # Re-enable button even on error so user can try again
        state.can_add_derived = True

@state.change("updateDerivedParameter")
def update_derived_parameter_ui(**kwargs):
    """Update an existing derived parameter from the UI."""
    # Prevent recursive calls by checking if dialog is actually open
    if not state.edit_derived_parameter_dialog:
        return
        
    # Validate input
    valid, error_msg = validate_derived_parameter_input(state.edit_derived_parameter_name, state.edit_derived_parameter_definition)
    if not valid:
        log("error", f"Failed to update derived parameter: {error_msg}")
        return
    
    param_name = state.edit_derived_parameter_name
    param_definition = state.edit_derived_parameter_definition
    param_description = state.edit_derived_parameter_description
    
    # Update the derived parameter
    try:
        if not hasattr(state, 'derived_parameters'):
            state.derived_parameters = {}
        
        state.derived_parameters[param_name] = {
            "definition": param_definition,
            "description": param_description
        }
        state.dirty("derived_parameters")
        
        # Close dialog and clear form only after successful update
        state.edit_derived_parameter_dialog = False
        state.edit_derived_parameter_name = ""
        state.edit_derived_parameter_definition = ""
        state.edit_derived_parameter_description = ""
        log("info", f"Derived parameter '{param_name}' updated successfully")
    except Exception as e:
        log("error", f"Failed to update derived parameter: {str(e)}")

@state.change("showAddDerivedParameterDialog")
def show_add_derived_parameter_dialog(**kwargs):
    """Show the add derived parameter dialog."""
    log("DEBUG", "show_add_derived_parameter_dialog called")
    state.new_derived_parameter_name = ""
    state.new_derived_parameter_definition = ""
    state.new_derived_parameter_description = ""
    state.add_derived_parameter_dialog = True
    log("info", "Add derived parameter dialog shown")

@state.change("deleteVariable")
def delete_variable_ui(**kwargs):
    """Delete a variable from the UI."""
    # Only proceed if we have an actual item to delete
    item = kwargs.get('item')
    if not item:
        log("info", "delete_variable_ui called without item data during initialization - skipping")
        return
    
    remove_variable(item["name"])

@state.change("deleteDerivedParameter")
def delete_derived_parameter_ui(**kwargs):
    """Delete a derived parameter from the UI."""
    # Only proceed if we have an actual item to delete
    item = kwargs.get('item')
    if not item:
        log("info", "delete_derived_parameter_ui called without item data during initialization - skipping")
        return
    
    remove_derived_parameter(item["name"])

@state.change("generatePythonWrapper")
def generate_python_wrapper_ui(**kwargs):
    """Generate Python wrapper from the UI."""
    # Check button state
    if not state.can_generate_wrapper:
        log("warning", "Cannot generate wrapper - button is disabled")
        return
      # Disable button during generation
    state.can_generate_wrapper = False
    
    try:
        # Check if case name is defined and not empty
        if not hasattr(state, 'case_name') or not state.case_name:
            log("info", "Case name is not defined or empty, cannot generate Python wrapper")
            return
        
        filename_json_export = getattr(state, 'filename_json_export', 'config.json')
        filename_cfg_export = getattr(state, 'filename_cfg_export', 'config.cfg')
        filename_py_export = getattr(state, 'python_wrapper_filename', 'run_su2.py')
        
        variables = get_variables_dict()
        derived_parameters = get_derived_parameters_dict()
          # For standard wrapper, disable dynamic temperature
        dynamic_wall_temp_markers = {}
        
        # Save files with standard wrapper
        generated_wrapper_path = save_json_cfg_py_file(
            filename_json_export,
            filename_cfg_export,
            filename_py_export,
            variables=variables,
            derived_parameters=derived_parameters,
            dynamic_wall_temp_markers=dynamic_wall_temp_markers
        )
        
        if generated_wrapper_path:
            state.last_generated_wrapper_path = generated_wrapper_path
            state.show_wrapper_path_info = True
            log("info", f"Standard wrapper generated successfully!")
            log("info", f"Location: {generated_wrapper_path}")
        else:
            log("error", "Failed to generate standard wrapper")
            state.show_wrapper_path_info = False
    except Exception as e:
        log("error", f"Failed to generate Python wrapper: {str(e)}")
    finally:
        # Re-enable button
        state.can_generate_wrapper = True

# Dynamic temperature wrapper generation moved to boundaries.py
# @state.change("generatePythonWrapperWithDynamicTemp")
# def generate_python_wrapper_with_dynamic_temp_ui(**kwargs):
#     """Generate Python wrapper with dynamic temperature from the UI."""
#     # Check button state
#     if not state.can_generate_wrapper:
#         log("warning", "Cannot generate wrapper - button is disabled")
#         return
#     
#     # Disable button during generation
#     state.can_generate_wrapper = False
#     
#     try:
#         # Check if case name is defined and not empty
#         if not hasattr(state, 'case_name') or not state.case_name:
#             log("info", "Case name is not defined or empty, cannot generate Python wrapper")
#             return
#         
#         filename_json_export = getattr(state, 'filename_json_export', 'config.json')
#         filename_cfg_export = getattr(state, 'filename_cfg_export', 'config.cfg')
#         filename_py_export = getattr(state, 'dynamic_temp_wrapper_filename', 'run_su2.py')
#         
#         variables = get_variables_dict()
#         derived_parameters = get_derived_parameters_dict()
#           # Create dynamic wall temperature markers dictionary
#         dynamic_wall_temp_markers = {"airfoil": state.dynamic_temp_function}
#         
#         # Save files with dynamic temperature
#         generated_wrapper_path = save_json_cfg_py_file(
#             filename_json_export,
#             filename_cfg_export,
#             filename_py_export,
#             variables=variables,
#             derived_parameters=derived_parameters,
#             dynamic_wall_temp_markers=dynamic_wall_temp_markers
#         )
#         
#         if generated_wrapper_path:
#             state.last_generated_wrapper_path = generated_wrapper_path
#             state.show_wrapper_path_info = True
#             log("info", f"Dynamic temperature wrapper generated successfully!")
#             log("info", f"Location: {generated_wrapper_path}")
#         else:
#             log("error", "Failed to generate dynamic temperature wrapper")
#             state.show_wrapper_path_info = False
#     except Exception as e:
#         log("error", f"Failed to generate Python wrapper with dynamic temperature: {str(e)}")
#     finally:
#         # Re-enable button
#         state.can_generate_wrapper = True

# Add confirmation handlers for delete operations
@state.change("confirmDeleteVariable")
def confirm_delete_variable(**kwargs):
    """Confirm deletion of a variable."""
    if state.item_to_delete and state.item_type_to_delete == "variable":
        remove_variable(state.item_to_delete)
        log("info", f"Variable '{state.item_to_delete}' deleted successfully")
    state.confirm_delete_variable_dialog = False
    state.item_to_delete = ""
    state.item_type_to_delete = ""

@state.change("confirmDeleteDerivedParameter")
def confirm_delete_derived_parameter(**kwargs):
    """Confirm deletion of a derived parameter."""
    if state.item_to_delete and state.item_type_to_delete == "derived_parameter":
        remove_derived_parameter(state.item_to_delete)
        log("info", f"Derived parameter '{state.item_to_delete}' deleted successfully")
    state.confirm_delete_derived_parameter_dialog = False
    state.item_to_delete = ""
    state.item_type_to_delete = ""

# Add validation functions
def validate_variable_input(name, value):
    """Validate variable input."""
    if not name or not name.strip():
        return False, "Variable name cannot be empty"
    if not value or not value.strip():
        return False, "Variable value cannot be empty"
    if not name.replace('_', '').isalnum():
        return False, "Variable name must contain only letters, numbers, and underscores"
    return True, ""

def validate_derived_parameter_input(name, definition):
    """Validate derived parameter input."""
    if not name or not name.strip():
        return False, "Parameter name cannot be empty"
    if not definition or not definition.strip():
        return False, "Parameter definition cannot be empty"
    if not name.replace('_', '').isalnum():
        return False, "Parameter name must contain only letters, numbers, and underscores"
    return True, ""

@state.change("copyPathToClipboard")
def copy_path_to_clipboard(**kwargs):
    """Copy the generated wrapper path to clipboard."""
    try:
        # This is a simple notification - actual clipboard copy would need browser API
        log("info", f"Path copied to clipboard: {state.last_generated_wrapper_path}")
    except Exception as e:
        log("error", f"Failed to copy path: {str(e)}")


###############################################################
# MAIN TAB FUNCTION FOR VARIABLES
###############################################################
def variables_tab():
    """Create the variables tab in the main interface."""
    with vuetify.VTabItem(
        value=(4,), style="width: 100%; height: 100%; padding: 3rem"
    ):
        variables_card()
        variables_subcard()
        variables_dialog_cards()

###############################################################
# CONTROLLER REGISTRATION
###############################################################
# Register handler methods with the controller
ctrl.edit_variable = edit_variable_action
ctrl.delete_variable = delete_variable_action
ctrl.edit_derived_parameter = edit_derived_parameter_action
ctrl.delete_derived_parameter = delete_derived_parameter_action
ctrl.handle_click = handle_click
# ctrl.generate_python_wrapper_with_dynamic_temp = generate_python_wrapper_with_dynamic_temp_ui  # Moved to boundaries.py
