import sys
import os
from pathlib import Path
from datetime import date

# Add parent directory to path to allow importing from sibling directories
parent_dir = str(Path(__file__).parent.parent.absolute())
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from trame.widgets import vuetify, markdown

# functions to update GUI after user enters a new key-value pair in jsonData
from ui.fileio import set_json_fileio
from ui.initialization import set_json_initialization
from ui.materials import set_json_materials
from ui.numerics import set_json_numerics
from ui.physics import set_json_physics
from core.solver import set_json_solver
from core.su2_json import updateBCDictListfromJSON
from core.su2_io import createjsonMarkers

from ui.uicard import server
from core.logger import log

# for JSON schema validation
# imports for json schema
# import json
# import jsonschema

# Extract state and controller from the server
state, ctrl = server.state, server.controller

state.cofig_str = ""
state.config_desc = f"""%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%                                                                              %
% SU2 configuration file                                                       %
% Case description:                                                            %
% Author:                                                                      %
% Date: {str(date.today()) }                                                             %
% SU2 version:                                                                 %
%                                                                              %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
"""

def add_new_property():
    # prepare a valid schema for using the function given below
    # validate_dict_against_schema()
    if state.new_config_key==None or state.new_config_value==None:
        return
    value = state.new_config_value
    # trying to convert new_config_value to a bool or float
    try:
        value =  float(value)
    except:
        if value.lower() in ("yes", "true", "no", "false"):
            value =  value.lower() == "yes" or value.lower() == "true"
        elif ',' in value or ' ' in value or ((value.startswith('(') and value.endswith(')')) or (value.startswith('[') and value.endswith(']')) or (value.startswith('{') and value.endswith('}'))) :
            # Remove parentheses and split by comma
            if value[0]=='(' or value[-1]==')' or value[0]=='[' or value[-1]==']' or value[0]=='{' or value[-1]=='}':
               value = value[1:-1]
            if ',' in value:
               value =  value.split(',')
            else:
               value = value.split()
            # Convert each item to an appropriate type
            value = [v.strip() for v in value]
            value = [int(v) if v.isdigit() else v for v in value]
    state.new_config_key = state.new_config_key.upper().strip()
    state.jsonData[state.new_config_key] = value
    state.dirty('jsonData')
    update_config_str()
    set_json_physics()
    set_json_initialization()
    set_json_numerics()
    set_json_solver()
    set_json_fileio()
    set_json_materials()
    updateBCDictListfromJSON()
    log("info", f"Added {state.new_config_key} : {state.new_config_value}({type(state.new_config_value)})")

def update_config_str():
    createjsonMarkers()
    max_key_len = max(len(key) for key in state.jsonData.keys())  
    state.config_str = "  \n".join([f"\t{key:{max_key_len}} : {value}" for key, value in state.jsonData.items()])

@state.change("key")
def update_new_config_key(key, **kwargs):
    state.new_config_key = key

@state.change("value")
def update_new_config_value(value, **kwargs):
    state.new_config_value = value

@state.change("config_desc")
def update_config_desc(config_desc, **kwargs):
    new_config_desc = ""
    for line in config_desc.splitlines():
        if not line.startswith("%"):
            line = '%' + line
        new_config_desc += line + "\n"
    state.config_desc = new_config_desc

#################### JSON SCHEMA VALIDATION ####################
# Validate the dictionary against the JSON schema
# this will be used later when the JSON schema is ready
# def validate_dict_against_schema():
#     log("info", state.jsonData)
#     # Load the JSON schema from the file
#     try:
#         with open("./user/JsonSchema.json", 'r') as file:
#             schema = json.load(file)
#     except FileNotFoundError:
#         log("error", "Schema file not found.")
#         return False
#     except json.JSONDecodeError:
#         log("error", "Invalid JSON schema file.")
#         return False

#     # Validate the dictionary against the schema
#     try:
#         validate(instance=state.jsonData, schema=schema)
#         log("info", "The dictionary is valid.")
#         return True
#     except jsonschema.exceptions.ValidationError as ve:
#         log("error", f"Validation error: {ve.message}")
#         return False
#     except jsonschema.exceptions.SchemaError as se:
#         log("error", f"Schema error: {se.message}")
#         return False
    


############### CONFIG TAB GUI ####################
def config_tab():
    with vuetify.VTabItem(
        value=(2,), style="width: 100%; height: 100%; padding: 3rem"
    ):
        
        markdown.Markdown(
            content = ('config_tab_heading', "Add Properties Manually  \n"), 
            style = "font-weight:bolder;background-color: white; color:black; font-size: larger; "
        )

        with vuetify.VRow(
            style= "margin:1rem;"
        ):
            with vuetify.VCol(
                    style = "width:30%"):
                vuetify.VTextField(
                    label="Key",
                    v_model = ("key", None),
                    outlined=True,
                    dense=True,
                    hide_details=True,
                )
            with vuetify.VCol(
                    style = "width:70%"):
                vuetify.VTextField(
                    label="Value",
                    v_model = ("value", None),
                    outlined=True,
                    dense=True,
                    hide_details=True,
                )
        vuetify.VBtn("Add",click=(add_new_property),
                        style = "background-color: #3a76de; margin-left: 2rem; color: white; margin-bottom: 1rem;"
                        )

        markdown.Markdown(
            content = ('config_tab_desc_heading', "Edit description for Configuration file:  \n"), 
            style = "font-weight:bolder;background-color: white; color:black;"
        )

        vuetify.VTextarea(
                v_model=("config_desc", ""),
                style="font-family: monospace; margin-bottom: 2rem;",
                hide_details=True,
        )

        with vuetify.VRow(
            style = "justify-content: space-between; margin:.5rem;"
        ):
            markdown.Markdown(
                content = ('config_data_heading', "Configuration File Data  \n"), 
                style = "font-weight:bolder;background-color: white; color:black;"
            )
            vuetify.VBtn("Reload",click=(update_config_str),
                style = "background-color: #3a76de; margin-left: 2rem; color: white;"
                )
                
        markdown.Markdown(
            content = ('config_str', state.confing_str), 
            style = "background-color: white;"
        )