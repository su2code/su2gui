from .enhanced_config_validator import SU2ConfigValidator, validate_su2_config, check_config_with_workflow

def validate_su2_config_file(config_file_path, schema_file_path=None):
    """
    Validate SU2 configuration file against the complete JSON schema.
    Enhanced version using the new SU2ConfigValidator class.
    
    Args:
        config_file_path (str): Path to the SU2 config file (.cfg or .json)
        schema_file_path (str): Path to the JSON schema file (optional)
        
    Returns:
        dict: Validation result with 'valid' boolean and 'errors' list
    """
    return validate_su2_config(config_file_path, schema_file_path)


# Integration function for your existing workflow
def check_config_with_existing_workflow(filename_cfg="config.cfg"):
    """
    Check SU2 config file using your existing su2_json.py and su2_io.py workflow.
    Enhanced version with comprehensive cross-parameter validation.
    """
    return check_config_with_workflow(filename_cfg)

def convert_cfg_to_json(cfg_file_path):
    """
    Convert SU2 .cfg file to JSON format for validation.
    This function works similarly to your existing su2_io.py logic.
    """
    config_dict = {}
    
    with open(cfg_file_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('%'):
                continue
                
            # Handle line continuation
            if line.endswith('\\'):
                continue  # Skip for now, implement if needed
                
            # Parse key-value pairs
            if '=' in line:
                # Remove inline comments
                if '%' in line:
                    line = line[:line.index('%')].strip()
                    
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Parse the value
                parsed_value = parse_config_value(value)
                config_dict[key] = parsed_value
                
    return config_dict

def parse_config_value(value):
    """
    Parse configuration value from string to appropriate type.
    Compatible with your existing su2_json.py logic.
    Be defensive: when value is not a string, just return it unchanged.
    """
    # If value is not a string, return as-is (pre-parsed elsewhere)
    if not isinstance(value, str):
        return value

    value = value.strip()
    
    # Handle parentheses (arrays/tuples)
    if value.startswith('(') and value.endswith(')'):
        inner = value[1:-1].strip()
        if not inner:
            return []
            
        # Split by comma and parse each element
        elements = [elem.strip() for elem in inner.split(',')]
        return [parse_single_value(elem) for elem in elements]
    
    return parse_single_value(value)

def parse_single_value(value):
    """Parse a single value to its appropriate type."""
    # If value is not a string, return as-is
    if not isinstance(value, str):
        return value

    value = value.strip()
    
    # Boolean values
    if value.upper() in ['YES', 'TRUE']:
        return True
    elif value.upper() in ['NO', 'FALSE']:
        return False
    
    # Numeric values
    try:
        if '.' in value or 'e' in value.lower():
            return float(value)
        else:
            return int(value)
    except ValueError:
        pass
    
    # String value (remove quotes if present)
    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    
    return value

# Integration function for your existing workflow
def check_config_with_existing_workflow(filename_cfg="config.cfg"):
    """
    Check SU2 config file using your existing su2_json.py and su2_io.py workflow.
    This function integrates with your current state management.
    """
    from core.su2_json import state
    from core.logger import log
    from pathlib import Path
    
    BASE = Path(__file__).parent.parent
    
    try:
        config_path = BASE / "user" / state.case_name / filename_cfg
        config_path = BASE / "user" / state.case_name / filename_cfg
        
        # Validate the config file
        validation_result = validate_su2_config_file(config_path)
        
        if validation_result['valid']:
            log("info", f" Configuration file {filename_cfg} is valid")
            
            # Update state.jsonData with validated config
            if validation_result['config_data']:
                state.jsonData.update(validation_result['config_data'])
                log("info", "JSON data updated with validated configuration")
                
        else:
            log("error", f" Configuration file {filename_cfg} has validation errors:")
            for error in validation_result['errors']:
                log("error", f"  - {error}")
                
        return validation_result
        
    except Exception as e:
        log("error", f"Error validating config file: {str(e)}")
        return {
            'valid': False,
            'errors': [str(e)],
            'config_data': None,
            'message': f'Validation error: {str(e)}'
        }

# Usage example for your workflow
def validate_and_update_config():
    """
    Example function showing how to integrate validation into your workflow.
    """
    # Validate current config
    result = check_config_with_existing_workflow("config.cfg")
    
    if result['valid']:
        # Continue with your existing workflow
        from core.su2_io import createjsonMarkers, save_json_cfg_file
        
        # Create markers from BCDictList
        createjsonMarkers()
        
        # Save validated config
        save_json_cfg_file("config_validated.json", "config_validated.cfg")
        
        return True
    else:
        # Handle validation errors
        print("Configuration validation failed. Please fix the errors before proceeding.")
        return False
