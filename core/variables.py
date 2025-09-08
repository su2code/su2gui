import sys
import os
from pathlib import Path

# Add parent directory to path to allow importing from sibling directories
parent_dir = str(Path(__file__ ).parent.parent.absolute())
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from ui.uicard import ui_card, ui_subcard, server
from core.logger import log

state, ctrl = server.state, server.controller

# Initialize variables and derived parameters in state
if not hasattr(state, 'variables'):
    state.variables = {}

if not hasattr(state, 'derived_parameters'):
    state.derived_parameters = {}

def add_variable(name, value, description=""):
   
    state.variables[name] = {
        'value': value,
        'description': description
    }
    log("info", f"Added variable: {name} = {value}")
    state.dirty('variables')

def update_variable(name, value):
   
    if name in state.variables:
        state.variables[name]['value'] = value
        log("info", f"Updated variable: {name} = {value}")
        state.dirty('variables')
    else:
        log("error", f"Variable {name} does not exist")

def remove_variable(name):
    
    if name in state.variables:
        del state.variables[name]
        log("info", f"Removed variable: {name}")
        state.dirty('variables')
    else:
        log("error", f"Variable {name} does not exist")

def add_derived_parameter(name, definition, description=""):
    
    state.derived_parameters[name] = {
        'definition': definition,
        'description': description
    }
    log("info", f"Added derived parameter: {name} = {definition}")
    state.dirty('derived_parameters')

def update_derived_parameter(name, definition):
   
    if name in state.derived_parameters:
        state.derived_parameters[name]['definition'] = definition
        log("info", f"Updated derived parameter: {name} = {definition}")
        state.dirty('derived_parameters')
    else:
        log("error", f"Derived parameter {name} does not exist")

def remove_derived_parameter(name):
    
    if name in state.derived_parameters:
        del state.derived_parameters[name]
        log("info", f"Removed derived parameter: {name}")
        state.dirty('derived_parameters')
    else:
        log("error", f"Derived parameter {name} does not exist")

def get_variables_dict():
    
    return {name: var['value'] for name, var in state.variables.items()}

def get_derived_parameters_dict():
    
    return {name: param['definition'] for name, param in state.derived_parameters.items()}

def substitute_variables(text, variables=None):
   
    if variables is None:
        variables = get_variables_dict()
    
    result = text
    for var_name, var_value in variables.items():
        result = result.replace(var_name, str(var_value))
    
    return result

# Initialize with some example variables and derived parameters
# if not state.variables:
#     add_variable('__WIDTH__', 0.055, 'Channel width')
#     add_variable('__AMPLITUDE__', 0.045, 'Deformation amplitude')

# if not state.derived_parameters:
#     add_derived_parameter('p_tot', 'PRESSURE + 0.5 * DENSITY * (pow(VELOCITY_X, 2) + pow(VELOCITY_Y, 2))', 'Total pressure')
#     add_derived_parameter('p_drop', 'p_out - p_in', 'Pressure drop')
