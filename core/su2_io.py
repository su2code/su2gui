import sys
import os
import json
from pathlib import Path

# Try to import VTK (optional for validation functions)
try:
    import vtk
    VTK_AVAILABLE = True
except ImportError:
    VTK_AVAILABLE = False

# Add parent directory to path to allow importing from sibling directories
parent_dir = str(Path(__file__).parent.parent.absolute())
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

try:
    from core.su2_json import *
except ImportError:
    pass

try:
    from core.logger import log
except ImportError:
    # Fallback logging function
    def log(level, message):
        print(f"[{level.upper()}] {message}")

try:
    from core.su2_py_wrapper import save_json_cfg_py_file
except ImportError:
    pass

# Import validation functions
try:
    from core.json_validation import cfg_to_json_dict, validate_cfg_with_schema, apply_su2_fixes, apply_schema_fixes
    VALIDATION_AVAILABLE = True
except ImportError:
    log("warning", "Validation functions not available")
    VALIDATION_AVAILABLE = False

BASE = Path(__file__).parent.parent

# remove empty lists from dictlist object
def remove_empty_lists(d):
  final_dict = {}
  for a, b in d.items():
     if b:
       if isinstance(b, dict):
         final_dict[a] = remove_empty_lists(b)
       elif isinstance(b, list):
         final_dict[a] = list(filter(None, [remove_empty_lists(i) for i in b]))
       else:
         final_dict[a] = b
  return final_dict

########################################################################################
# create the json entries for the boundaries using BCDictList
########################################################################################
def createjsonMarkers():
  log("info", "creating json entry for inlet")
  marker_inlet=[]
  marker_isothermal=[]
  marker_heatflux=[]
  marker_heattransfer=[]
  marker_euler=[]
  marker_symmetry=[]
  marker_farfield=[]
  marker_outlet=[]
  marker_supersonic_inlet=[]
  marker_supersonic_outlet=[]
  marker_wall_functions = []

  # PRESSURE_OUTLET or MASS_FLOW_OUTLET
  marker_inc_outlet_type=[]
  # PRESSURE_INLET or VELOCITY_INLET
  marker_inc_inlet_type=[]
  # TOTAL_CONDITIONS or MASS_FLOW
  marker_inlet_type=[]

  # loop over the boundaries and construct the markers
  for bcdict in state.BCDictList:
    log("info", f"bcdict =  = {bcdict}")
    # ##### WALL BOUNDARY CONDITIONS #####
    if bcdict['bc_subtype']=="Temperature":
        marker = [bcdict['bcName'], bcdict['bc_temperature']]
        marker_isothermal.append( marker )
        marker_wall_functions.append( [bcdict['bcName'], "STANDARD_WALL_FUNCTION"] )
    elif bcdict['bc_subtype']=="Heat flux":
        marker = [bcdict['bcName'], bcdict['bc_heatflux']]
        marker_heatflux.append( [bcdict['bcName'], bcdict['bc_heatflux']] )
        marker_wall_functions.append( [bcdict['bcName'], "STANDARD_WALL_FUNCTION"] )
    elif bcdict['bc_subtype']=="Heat transfer":
        marker = [bcdict['bcName']]
        marker.extend(bcdict['bc_heattransfer'])
        log("info", f"heat transfer marker= = {marker}")
        marker_heattransfer.append( marker )
        marker_wall_functions.append( [bcdict['bcName'], "STANDARD_WALL_FUNCTION"] )
    elif bcdict['bc_subtype']=="Euler":
        marker = [bcdict['bcName']]
        marker_euler.append(marker)
        marker_wall_functions.append( [bcdict['bcName'], "STANDARD_WALL_FUNCTION"] )
    # ##### OUTLET BOUNDARY CONDITIONS #####
    elif bcdict['bc_subtype']=="Target mass flow rate":
        marker = [bcdict['bcName'], bcdict['bc_massflow']]
        marker_outlet.append( marker )
        marker_inc_outlet_type.append("MASS_FLOW_OUTLET")
    elif bcdict['bc_subtype']=="Pressure outlet":
        marker = [bcdict['bcName'], bcdict['bc_pressure']]
        marker_outlet.append( marker )
        marker_inc_outlet_type.append("PRESSURE_OUTLET")
    # ##### INLET BOUNDARY CONDITIONS #####
    elif bcdict['bc_subtype']=="Velocity inlet":
        # note that temperature is always saved.
        marker = [bcdict['bcName'], bcdict['bc_temperature'], bcdict['bc_velocity_magnitude']]
        marker.extend(bcdict['bc_velocity_normal'])
        marker_inlet.append( marker )
        marker_inc_inlet_type.append("VELOCITY_INLET")
    elif bcdict['bc_subtype']=="Pressure inlet":
        marker = [bcdict['bcName'], bcdict['bc_temperature'], bcdict['bc_pressure']]
        marker.extend(bcdict['bc_velocity_normal'])
        marker_inlet.append( marker )
        marker_inc_inlet_type.append("PRESSURE_INLET")
    elif bcdict['bc_subtype']=="Total Conditions":
        marker = [bcdict['bcName'], bcdict['bc_temperature'], bcdict['bc_pressure']]
        marker.extend(bcdict['bc_velocity_normal'])
        marker_inlet.append( marker )
        marker_inlet_type.append("TOTAL_CONDITIONS")
    elif bcdict['bc_subtype']=="Mass Flow":
        marker = [bcdict['bcName'], bcdict['bc_density'], bcdict['bc_velocity_magnitude']]
        marker.extend(bcdict['bc_velocity_normal'])
        marker_inlet.append( marker )
        marker_inlet_type.append("MASS_FLOW")
    # ##### SYMMETRY BOUNDARY CONDITIONS #####
    elif bcdict['bc_subtype']=="Symmetry":
        marker = [bcdict['bcName']]
        marker_symmetry.append( marker )
    # ##### FARFIELD BOUNDARY CONDITIONS #####
    elif bcdict['bc_subtype']=="Far-field":
        marker = [bcdict['bcName']]
        marker_farfield.append( marker )
    # ##### SUPERSONIC INLET BOUNDARY CONDITIONS #####
    elif bcdict['bc_subtype']=="Supersonic Inlet":
        marker = [bcdict['bcName'], bcdict['bc_temperature'], bcdict['bc_pressure']]
        marker.extend(bcdict['bc_velocity_normal'])
        marker_supersonic_inlet.append( marker )
    # ##### SUPERSONIC OUTLET BOUNDARY CONDITIONS #####
    elif bcdict['bc_subtype']=="Supersonic Outlet":
        marker = [bcdict['bcName']]
        marker_supersonic_outlet.append( marker )

  # ##### WALL #####
  state.jsonData['MARKER_ISOTHERMAL']=marker_isothermal
  state.jsonData['MARKER_HEATFLUX']=marker_heatflux
  state.jsonData['MARKER_HEATTRANSFER']=marker_heattransfer
  state.jsonData['MARKER_EULER']=marker_euler

  # ##### WALL FUNCTIONS #####
  if state.wall_function:
    state.jsonData['MARKER_WALL_FUNCTIONS']=marker_wall_functions

  # ##### OUTLET #####
  state.jsonData['MARKER_OUTLET']=marker_outlet
  state.jsonData['INC_OUTLET_TYPE']=marker_inc_outlet_type

  state.jsonData['MARKER_SYM']=marker_symmetry
  state.jsonData['MARKER_FAR']=marker_farfield

  state.jsonData['MARKER_INLET']=marker_inlet
  state.jsonData['INC_INLET_TYPE']=marker_inc_inlet_type
  state.jsonData['INLET_TYPE']=marker_inlet_type

  # ##### SUPERSONIC #####
  state.jsonData['MARKER_SUPERSONIC_INLET']=marker_supersonic_inlet
  state.jsonData['MARKER_SUPERSONIC_OUTLET']=marker_supersonic_outlet

  log("info", f"marker_isothermal= = {state.jsonData['MARKER_ISOTHERMAL']}")
  log("info", f"marker_heatflux= = {state.jsonData['MARKER_HEATFLUX']}")
  log("info", f"marker_heattransfer= = {state.jsonData['MARKER_HEATTRANSFER']}")
  log("info", f"marker_outlet= = {state.jsonData['MARKER_OUTLET']}")
  log("info", f"marker_inc_outlet_type= = {state.jsonData['INC_OUTLET_TYPE']}")
  log("info", f"marker_symmetry= = {state.jsonData['MARKER_SYM']}")
  log("info", f"marker_far= = {state.jsonData['MARKER_FAR']}")
  log("info", f"marker_inlet= = {state.jsonData['MARKER_INLET']}")
  log("info", f"marker_inc_inlet_type= = {state.jsonData['INC_INLET_TYPE']}")
  log("info", f"marker_supersonic_inlet= = {state.jsonData['MARKER_SUPERSONIC_INLET']}")
  log("info", f"marker_supersonic_outlet= = {state.jsonData['MARKER_SUPERSONIC_OUTLET']}")

  log("info", state.jsonData)
  # all empty markers will be removed for writing
  myDict = {key:val for key, val in state.jsonData.items() if val != []}
  log("info", myDict)
  state.jsonData = myDict

########################################################################################
# Export the new json configuration file as .json and as .cfg #
# TODO: why do all the states get checked at startup?
# TODO: when we click the save button, the icon color changes
########################################################################################
def save_json_cfg_file(filename_json_export,filename_cfg_export):
    if state.case_name == None or state.case_name == "":
        log("info", "Case name is not defined, did not export the configuration file")
        return
    log("info", "exporting files")
    log("info", f"write config file  = {filename_json_export}"),
    log("info", f"write config file  = {filename_cfg_export}"),
    state.counter = state.counter + 1
    log("info", f"counter= = {state.counter}")
    if (state.counter==2):
      log("info", f"counter= = {state.counter}")

    # construct the boundaries using BCDictList
    createjsonMarkers()
    #
    ########################################################################################
    # ##### save the json file
    ########################################################################################
    with open(BASE / "user" / state.case_name / filename_json_export,'w') as jsonOutputFile:
        json.dump(state.jsonData,jsonOutputFile,sort_keys=True,indent=4,ensure_ascii=False)
    ########################################################################################

    ########################################################################################
    # ##### convert json file to cfg file and save
    ########################################################################################
    with open(BASE / "user" / state.case_name / filename_cfg_export,'w') as f:
      f.write(f"{state.config_desc}  \n")
      #for k in state.jsonData:
      for attribute, value in state.jsonData.items():
        # print(attribute, value)
        # convert boolean
        if isinstance(value, bool):
            if value==True:
                value="YES"
            else:
                value="NO"
        # we can have lists or lists of lists
        # we can simply flatten the list, remove the quotations,
        # convert square brackets to round brackets and done.
        elif isinstance(value, list):

          flat_list = []
          for sublist in value:
            #print(sublist)
            if isinstance(sublist,list):
              #log("info", f"sublist= = {sublist}")
              for num in sublist:
                flat_list.append(num)
                #log("info", f"flatlist= = {flat_list}")
            else:
              flat_list.append(sublist)


          flatlist = ', '.join(str(e) for e in flat_list)
          # put the list between brackets
          value = "(" + flatlist + ")"

        # pass if value is none
        if value == None or (isinstance(value, str) and value.lower()=='none'):
           continue

        filestring=str(attribute) + "= " + str(value) + "\n"
        f.write(filestring)



########################################################################################
# ##### export internal vtk multiblock mesh to an su2 file
# ##### exports single block .su2 mesh with boundary conditions only
########################################################################################
def save_su2mesh(multiblock,su2_export_filename):
    log("info", type(multiblock))
    # export an su2 file
    # first, get the dimensions. If the z-dimension is smaller than 1e-6, we assume 2D

    # Set some initial values
    #MARKER_TAG = "1"
    #MARKER_ELEMS = 1

    log("info", "saving su2 mesh file")
    #global mb1
    #log("info", type(mb1))
    #log("info", dir(mb1))
    #log("info", f"nr of blocks inside block =  = {mb1.GetNumberOfBlocks(}"))

    internalBlock = multiblock.GetBlock(0)
    if (internalBlock==None):
        log("info", "no internal block, exiting")
        return

    boundaryBlock = multiblock.GetBlock(1)
    #log("info", f"nr of blocks inside internal block =  = {internalBlock.GetNumberOfBlocks(}"))
    #log("info", f"nr of blocks inside block =  = {boundaryBlock.GetNumberOfBlocks(}"))

    log("info", dir(internalBlock))
    # nr of data in internal block
    NELEM = internalBlock.GetNumberOfCells()
    NPOINT = internalBlock.GetNumberOfPoints()
    BOUND=[0,0,0,0,0,0]
    internalBlock.GetBounds(BOUND)
    dz = BOUND[5] - BOUND[2]
    log("info", f"dz = {dz}")
    NDIME= state.nDim
    # if (dz<1e-12):
    #     log("info", "case is 2D")
    #     NDIME= 2
    # else:
    #     log("info", "dz > 0, case is 3D")
    #     NDIME= 3

    pts = vtk.vtkIdList()
    for i in range(internalBlock.GetNumberOfBlocks()):
        #log("info", f"number of internal elements =  = {i+1," / ", internalBlock.GetNumberOfBlocks(}") )
        data = internalBlock.GetBlock(i)
        celldata = data.GetCells()
        #log("info", f"data type= = {type(data}"))
        #log("info", f"data type= = {dir(data}"))
        #log("info", f"celldata type= = {type(celldata}"))
        #log("info", f"celldata type= = {dir(celldata}"))

        for i in range(NELEM):
            #log("info", i," ",celldata.GetCellSize(i))
            celldata.GetCellAtId(i,pts)
            #log("info", f"number of ids =  = {pts.GetNumberOfIds(}"))
            #log("info", f"cell type = = {data.GetCellType(i}"))
            #for j in range(pts.GetNumberOfIds()):
            #    log("info", pts.GetId(j))


    for i in range(internalBlock.GetNumberOfBlocks()):
        #log("info", f"number of internal elements =  = {i+1," / ", internalBlock.GetNumberOfBlocks(}") )
        data = internalBlock.GetBlock(i)
        #for p in range(NPOINT):
        #    log("info", p," ",data.GetPoint(p))


    with open(BASE / "user" /  state.case_name /su2_export_filename, 'w') as f:
      # write dimensions
      s = "NDIME= " + str(NDIME) + "\n"
      f.write(s)
      # write element connectivity
      s = "NELEM= " + str(NELEM) + "\n"
      f.write(s)

      # write element connectivity
      for i in range(NELEM):
        s = str(data.GetCellType(i)) + " "
        #log("info", i," ",celldata.GetCellSize(i))
        celldata.GetCellAtId(i,pts)
        #log("info", f"number of ids =  = {pts.GetNumberOfIds(}"))
        for j in range(pts.GetNumberOfIds()):
            #log("info", pts.GetId(j))
            s += str(pts.GetId(j)) + " "
        s += str(i) + "\n"
        f.write(s)

      # write point coordinates
      s = "NPOIN= " + str(NPOINT) + "\n"
      f.write(s)
      for i in range(NPOINT):
          p = data.GetPoint(i)
          if (NDIME==3):
            s = str(p[0]) + " " + str(p[1]) + " " + str(p[2]) + " " + str(i) + "\n"
          else:
            s = str(p[0]) + " " + str(p[1]) + " " + str(i) + "\n"
          f.write(s)
      # write markers
      NMARK = boundaryBlock.GetNumberOfBlocks()
      s = "NMARK= " + str(NMARK) + "\n"
      f.write(s)
      for i in range(NMARK):
        #log("info", f"i =  = {i} {NMARK}")
        data = boundaryBlock.GetBlock(i)
        celldata = data.GetCells()
        name = boundaryBlock.GetMetaData(i).Get(vtk.vtkCompositeDataSet.NAME())
        s = "MARKER_TAG= " + str(name) + "\n"
        f.write(s)
        #log("info", f"metadata block name =  = {name}")
        #log("info", type(data))
        NCELLS = data.GetNumberOfCells()
        #log("info", f"Npoints =  = {data.GetNumberOfPoints(}"))
        s = "MARKER_ELEMS= " + str(NCELLS) + "\n"
        f.write(s)
        for i in range(NCELLS):
            s = str(data.GetCellType(i)) + " "
            celldata.GetCellAtId(i,pts)
            for j in range(pts.GetNumberOfIds()):
              s += str(pts.GetId(j)) + " "
            s += "\n"
            f.write(s)

########################################################################################
# Convert config file to JSON and validate with schema using predefined functions
########################################################################################
def convert_and_validate_config(cfg_file_path: str, schema_path: str = None, output_json_path: str = None):
    """
    Convert SU2 config file to JSON and validate it against a schema using predefined functions.
    
    Args:
        cfg_file_path (str): Path to the SU2 configuration file (.cfg)
        schema_path (str, optional): Path to the JSON schema file. Defaults to JsonSchema.json
        output_json_path (str, optional): Path to save the converted JSON file
    
    Returns:
        tuple: (is_valid, config_dict, errors)
    """
    
    if not VALIDATION_AVAILABLE:
        log("error", "Validation functions are not available")
        return False, {}, ["Validation functions not imported"]
    
    try:
        # Set default schema path if not provided
        if not schema_path:
            schema_path = str(BASE / "JsonSchema.json")
        
        log("info", f"Converting config file: {cfg_file_path}")
        log("info", f"Using schema: {schema_path}")
        
        config_dict = cfg_to_json_dict(cfg_file_path)
        log("info", f"Successfully parsed {len(config_dict)} configuration parameters")
        
        config_dict = apply_su2_fixes(config_dict)
        log("info", "Applied SU2 compatibility fixes")
        
        if output_json_path:
            try:
                with open(output_json_path, "w", encoding="utf-8") as json_file:
                    json.dump(config_dict, json_file, indent=2, ensure_ascii=False)
                log("info", f"JSON file saved to: {output_json_path}")
            except Exception as e:
                log("error", f"Error saving JSON file: {e}")
        
        # Validate using predefined function
        is_valid, validated_config, errors = validate_cfg_with_schema(cfg_file_path, schema_path)
        
        if is_valid:
            log("info", "Configuration is valid against schema!")
        else:
            log("error", f"Configuration validation failed with {len(errors)} errors")
            for i, error in enumerate(errors, 1):
                if hasattr(error, 'message'):
                    log("error", f"  {i}. {error.message}")
                else:
                    log("error", f"  {i}. {str(error)}")
        
        return is_valid, config_dict, errors
        
    except FileNotFoundError as e:
        log("error", f"File not found: {e}")
        return False, {}, [str(e)]
    except Exception as e:
        log("error", f"Unexpected error in convert_and_validate_config: {e}")
        return False, {}, [str(e)]

########################################################################################
# Simple wrapper function for easy use
########################################################################################
def load_and_validate_config(cfg_file_path: str, schema_file: str = "JsonSchema.json"):
    """
    Simple wrapper to load a config file and validate it.
    
    Args:
        cfg_file_path (str): Path to the SU2 configuration file
        schema_file (str): Name of schema file (defaults to JsonSchema.json)
    
    Returns:
        tuple: (is_valid, config_dict, errors)
    """
    schema_path = str(BASE / schema_file)
    return convert_and_validate_config(cfg_file_path, schema_path)