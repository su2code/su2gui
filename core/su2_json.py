
# ##################################### JSON ##############################
import sys
import os
from pathlib import Path

# Add parent directory to path to allow importing from sibling directories
parent_dir = str(Path(__file__).parent.parent.absolute())
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from ui.uicard import ui_card, ui_subcard, server
from core.logger import log

import json

BASE = Path(__file__).parent.parent

state, ctrl = server.state, server.controller

# ##################################### JSON ##############################

#class jsonManager:
#    def __init__(self, state, name):
#        """ initialize the pipeline """
#        self._state = state
#        self._name = name
#        self._next_id = 1
#        self._nodes = {}
#        self._children_map = defaultdict(set)

# ##################################### JSON ##############################
def read_json_data(filenam):
  log("info", "jsondata::opening json file and reading data")
  with open(filenam,"r") as jsonFile:
    state.jsonData = json.load(jsonFile)
  return state.jsonData
# ##################################### JSON ##############################

# Read the default values for the SU2 configuration.
# this is done at startup
state.jsonData = read_json_data(BASE / "user" / "config.json")

# Q:we now have to add all mandatory fields that were not found in the json file?
# A:nijso: actually, they are added automatically when we add an item for the first time

# get the "json" name from the dictionary
def GetJsonName(value,List):
  log("info", f"value= = {value}")
  log("info", f"list= = {List}")
  entry = [item for item in List if item["value"] == value]
  log("info", f"entry= = {entry}")
  if entry:  # Check if entry is not empty
    return entry[0]["json"]
  else:
      return None  # Or a default value if no match

# get the "value" from the dictionary
def GetJsonIndex(value, List):
    try:
        return int(next(item["value"] for item in List if item["json"] == value))
    except StopIteration:
        return None

def GetBCName(value,List):
  entry = [item for item in List if item["bcName"] == value]
  return(entry[0])


def SetGUIStateWithJson():
  log("info", f"setting GUI state with Json variable")


def findBCDictByName(bcName):
        return next((bcdict for bcdict in state.BCDictList if bcdict['bcName'] == bcName), None)

def marker_corrector(marker, length: int):
    """
    This function adds 0 in place of missing elements in the marker.
    Example - 
    outlet marker before - ("outlet1", "outlet2", 10, "outlet3")
                  after  - ("outlet1", 0, "outlet2", 10, "outlet3", 0)
    """
    new_marker = []
    count = length

    for i in marker:
        if isinstance(i, str):
            if count != length:
                new_marker += [0] * count
                count = length
        new_marker.append(i)
        count -= 1
        if count == 0:
            count = length

    if count != length:
        new_marker += [0] * count

    return new_marker


def updateBCDictListfromJSON():
  if state.BCDictList is None:
        log("error", "BCDictList is not initialized.")
        return
  # marker_list = [ "INC_INLET_TYPE", "MARKER_INLET", "MARKER_FAR", "MARKER_ISOTHERMAL", "MARKER_HEATTRANSFER"
  #                 "MARKER_SYM", "INC_OUTLET_TYPE", "INC_OUTLET_TYPE", "INC_OUTLET_TYPE"]

  # undating outlet boundaries
  if "MARKER_OUTLET" in state.jsonData:
    if isinstance(state.jsonData['MARKER_OUTLET'], str):
      state.jsonData['MARKER_OUTLET'] = [state.jsonData['MARKER_OUTLET']]
    # Ensure pairs of (name, value)
    corrected = marker_corrector(state.jsonData['MARKER_OUTLET'], 2)
    state.jsonData['MARKER_OUTLET'] = corrected
    # Prepare outlet type list per outlet
    outlet_types = state.jsonData.get('INC_OUTLET_TYPE', [])
    if isinstance(outlet_types, str):
      outlet_types = [outlet_types]
    for i in range(len(state.jsonData['MARKER_OUTLET']) // 2):
      bc_name, value = state.jsonData['MARKER_OUTLET'][2*i:2*(i+1)]
      bcdict = findBCDictByName(bc_name)
      if bcdict != None:
        bcdict['bcType'] = "Outlet"
        if outlet_types:
            sel_type = outlet_types[i] if i < len(outlet_types) else outlet_types[0]
            if sel_type == 'MASS_FLOW_OUTLET':
                bcdict['bc_subtype'] = 'Target mass flow rate'
                bcdict['bc_massflow'] = value
            else:
                bcdict['bc_subtype'] = 'Pressure outlet'
                bcdict['bc_pressure'] = value
        else:
            bcdict['bc_subtype'] = 'Pressure outlet'
            bcdict['bc_pressure'] = value

  # Updating inlet boundaries
  if "MARKER_INLET" in state.jsonData:
    if isinstance(state.jsonData['MARKER_INLET'], str):
      state.jsonData['MARKER_INLET'] = [state.jsonData['MARKER_INLET']]
    corrected = marker_corrector(state.jsonData['MARKER_INLET'], 6)
    state.jsonData['MARKER_INLET'] = corrected
    # Normalize types
    inc_inlet_types = state.jsonData.get('INC_INLET_TYPE', [])
    if isinstance(inc_inlet_types, str):
      inc_inlet_types = [inc_inlet_types]
    inlet_types = state.jsonData.get('INLET_TYPE', [])
    if isinstance(inlet_types, str):
      inlet_types = [inlet_types]

    for i in range(len(state.jsonData['MARKER_INLET']) // 6):
      bc_name, val1, val2, v1, v2, v3 = state.jsonData['MARKER_INLET'][6*i:6*(i+1)]
      bcdict = findBCDictByName(bc_name) 
      if bcdict != None:
        bcdict['bcType'] = "Inlet"
        bcdict['bc_velocity_normal'] = [v1, v2, v3]

        # Checking the type of inlet marker
        if inc_inlet_types:
            bcdict['bc_temperature'] = val1
            sel_type = inc_inlet_types[i] if i < len(inc_inlet_types) else inc_inlet_types[0]
            if sel_type == 'PRESSURE_INLET':
                bcdict['bc_subtype'] = 'Pressure inlet'
                bcdict['bc_pressure'] = val2
            else:
                bcdict['bc_subtype'] = 'Velocity inlet'
                bcdict['bc_velocity_magnitude'] = val2

        elif inlet_types:
            sel_type = inlet_types[i] if i < len(inlet_types) else inlet_types[0]
            if sel_type == 'TOTAL_CONDITIONS':
                bcdict['bc_subtype'] = 'Total Conditions'
                bcdict['bc_temperature'] = val1
                bcdict['bc_pressure'] = val2
            else:
                bcdict['bc_subtype'] = 'Mass Flow'
                bcdict['bc_density'] = val1
                bcdict['bc_velocity_magnitude'] = val2

  # updating symmetry boundaries
  if "MARKER_SYM" in state.jsonData:
    if isinstance(state.jsonData['MARKER_SYM'], str):
      state.jsonData['MARKER_SYM'] = [state.jsonData['MARKER_SYM']]
    for bc_name in state.jsonData['MARKER_SYM']:
      bcdict = findBCDictByName(bc_name) 
      if bcdict != None:
        bcdict["bcType"] = 'Symmetry'
        bcdict["bc_subtype"] = 'Symmetry'

  # updating farfield boundaries
  if "MARKER_FAR" in state.jsonData:
    if isinstance(state.jsonData['MARKER_FAR'], str):
      state.jsonData['MARKER_FAR'] = [state.jsonData['MARKER_FAR']]
    for bc_name in state.jsonData['MARKER_FAR']:
      bcdict = findBCDictByName(bc_name) 
      if bcdict != None:
        bcdict["bcType"] = 'Far-field'
        bcdict["bc_subtype"] = 'Far-field'

  # updating iso-thermal boundaries
  # Always normalize to a list (empty if missing) and correct shape
  iso = state.jsonData.get('MARKER_ISOTHERMAL', [])
  if isinstance(iso, str):
    iso = [iso]
  corrected = marker_corrector(iso, 2)
  state.jsonData['MARKER_ISOTHERMAL'] = corrected
  for i in range(len(state.jsonData['MARKER_ISOTHERMAL']) // 2):
      bc_name, value = state.jsonData['MARKER_ISOTHERMAL'][2*i:2*(i+ 1)]
      bcdict = findBCDictByName(bc_name) 
      if bcdict != None:
        bcdict["bcType"] = 'Wall'
        bcdict["bc_subtype"] = 'Temperature'
        bcdict['bc_temperature'] = value

  # updating Heat flux boundaries
  heatflux = state.jsonData.get('MARKER_HEATFLUX', [])
  if isinstance(heatflux, str):
    heatflux = [heatflux]
  corrected = marker_corrector(heatflux, 2)
  state.jsonData['MARKER_HEATFLUX'] = corrected
  for i in range(len(state.jsonData['MARKER_HEATFLUX']) // 2):
      bc_name, value = state.jsonData['MARKER_HEATFLUX'][2*i:2*(i+ 1)]
      bcdict = findBCDictByName(bc_name) 
      if bcdict != None:
        bcdict["bcType"] = 'Wall'
        bcdict["bc_subtype"] = 'Heat flux'
        bcdict['bc_heatflux'] = value


  # updating Heat transfer boundaries
  heattransfer = state.jsonData.get('MARKER_HEATTRANSFER', [])
  if isinstance(heattransfer, str):
    heattransfer = [heattransfer]
  corrected = marker_corrector(heattransfer, 3)
  state.jsonData['MARKER_HEATTRANSFER'] = corrected
  for i in range(len(state.jsonData['MARKER_HEATTRANSFER']) // 3):
      bc_name, val1, val2 = state.jsonData['MARKER_HEATTRANSFER'][3*i:3*(i + 1)]
      bcdict = findBCDictByName(bc_name) 
      if bcdict != None:
        bcdict["bcType"] = 'Wall'
        bcdict["bc_subtype"] = 'Heat transfer'
        bcdict["bc_heattransfer"] = [val1, val2]

  # updating symmetry boundaries
  if "MARKER_EULER" in state.jsonData:
    if isinstance(state.jsonData['MARKER_EULER'], str):
      state.jsonData['MARKER_EULER'] = [state.jsonData['MARKER_EULER']]
    for bc_name in state.jsonData['MARKER_EULER']:
      bcdict = findBCDictByName(bc_name) 
      if bcdict != None:
        bcdict["bcType"] = 'Wall'
        bcdict["bc_subtype"] = 'Euler'

  state.dirty("BCDictList")
  log("debug", f"updateBCDictList + {state.BCDictList}")