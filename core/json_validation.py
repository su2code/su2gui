import json
import re
import sys
import traceback
from typing import Union, Dict, Any, List
from pathlib import Path

# Use the enhanced validator as the single source of truth
from core.config_validator import SU2ConfigValidator

def parse_value(value_str: str) -> Union[str, float, int, bool, list]:
    
    value_str = value_str.strip()
    
    # Handle empty values
    if not value_str:
        return ""
    
    # Handle boolean-like values
    if value_str.upper() in ["YES", "TRUE"]:
        return True
    elif value_str.upper() in ["NO", "FALSE"]:
        return False
    
    # Enhanced list handling for SU2 configs
    if value_str.startswith("(") and value_str.endswith(")"):
        return parse_su2_list(value_str)
    
    # Numeric values with scientific notation support
    if re.match(r"^[+-]?[0-9]*\.?[0-9]+([eE][+-]?[0-9]+)?$", value_str):
        try:
            return float(value_str) if "." in value_str or "e" in value_str.lower() else int(value_str)
        except ValueError:
            pass
    
    # String values (preserve case sensitivity)
    return value_str

def parse_su2_list(value_str: str) -> List[Union[str, float, int]]:
    
    # Remove outer parentheses
    inner = value_str.strip()[1:-1].strip()
    if not inner:
        return []
    
    elements = []
    current = ""
    in_quotes = False
    paren_depth = 0
    
    for char in inner + ",":  
        if char == "\"" or char == "\'":
            in_quotes = not in_quotes
        elif char == "(":
            paren_depth += 1
        elif char == ")":
            paren_depth -= 1
            
        if char == "," and not in_quotes and paren_depth == 0:
            if current.strip():
                elements.append(current.strip())
            current = ""
        else:
            if char != "," or in_quotes or paren_depth > 0:  
                current += char
    
    # Parse each element recursively
    parsed_elements = []
    for elem in elements:
        elem = elem.strip()
        if elem.startswith("(") and elem.endswith(")"):
            parsed_elements.append(parse_su2_list(elem))
        else:
            parsed_elements.append(parse_value(elem))
    
    return parsed_elements

def cfg_to_json_dict(cfg_file_path: str) -> Dict[str, Any]:
   
    config_dict = {}
    
    try:
        with open(cfg_file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {cfg_file_path}")
    except Exception as e:
        raise Exception(f"Error reading file: {e}")
    
    for line_num, line in enumerate(lines, 1):
       
        line = line.strip()
        
       
        if not line or line.startswith("%"):
            continue
        
        # Remove comments 
        comment_pos = line.find("%")
        if comment_pos != -1:
            line = line[:comment_pos].strip()
        
       
        if not line:
            continue
        
       
        equals_pos = line.find("=")
        if equals_pos == -1:
            print(f"Warning: Line {line_num} does not contain \"=\" - skipping: {line}")
            continue
        
       
        key = line[:equals_pos].strip()
        value_str = line[equals_pos + 1:].strip()
        
        if not key:
            print(f"Warning: Line {line_num} has empty key - skipping: {line}")
            continue
        
        # Parse the value
        try:
            parsed_value = parse_value(value_str)
            config_dict[key] = parsed_value
        except Exception as e:
            print(f"Warning: Error parsing value on line {line_num}: {e}")
            config_dict[key] = value_str  # Store as string if parsing fails
    
    return config_dict

from typing import Optional

def validate_cfg_with_schema(cfg_path: str, schema_path: Optional[str] = None):
    """Validate a CFG using SU2ConfigValidator and the provided schema."""
    BASE = Path(__file__).parent.parent
    if not schema_path:
        schema_path = str(BASE / "su2_validation_schema.json")

    try:
        validator = SU2ConfigValidator(schema_path)
        if not getattr(validator, 'schema_enabled', False):
            print("Warning: jsonschema not available or schema not found. Running custom validations only.")
        result = validator.validate_config_file(cfg_path)
        is_valid = bool(result.get("valid"))
        errors = result.get("errors", [])
        return is_valid, result.get("config_data", {}), errors
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False, {}, [str(e)]

def apply_su2_fixes(config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Backwards-compat shim: not needed when using SU2ConfigValidator. Return as-is."""
    return dict(config_dict)

def apply_schema_fixes(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Deprecated: validator now consumes the schema directly."""
    return schema

def validate_config_standalone(schema_path=None, config_path=None):
    """
    Original validation function for JSON files"""
    
    BASE = Path(__file__).parent.parent
    if not schema_path:
        schema_path = str(BASE / "su2_validation_schema.json")
    if not config_path:
        config_path = str(BASE / "config_new.json")
    try:
        validator = SU2ConfigValidator(schema_path)
        result = validator.validate_config_file(config_path)
        if result.get("valid"):
            print("Configuration is valid!")
            return True
        print(f"Found {len(result.get('errors', []))} validation errors:")
        for i, error in enumerate(result.get('errors', []), 1):
            path = " -> ".join(str(p) for p in error.get('path', [])) if error.get('path') else "root"
            print(f"   {i}. Path: {path}")
            print(f"      Message: {error.get('message')}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def cfg_to_json(cfg_file_path: str, output_json_path: str = None) -> Dict[str, Any]:
    
    try:
        with open(cfg_file_path, "r", encoding="utf-8") as file:
            cfg_content = file.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {cfg_file_path}")
    except Exception as e:
        raise Exception(f"Error reading file: {e}")

    # Convert to dict using existing function
    config_dict = cfg_to_json_dict(cfg_file_path)

    # Save to JSON file if output path is provided
    if output_json_path:
        try:
            with open(output_json_path, "w", encoding="utf-8") as json_file:
                json.dump(config_dict, json_file, indent=2, ensure_ascii=False)
            print(f"Configuration successfully converted to JSON: {output_json_path}")
        except Exception as e:
            raise Exception(f"Error writing JSON file: {e}")

    return config_dict

def json_to_cfg(json_file_path: str, output_cfg_path: str) -> None:
    
    
    def format_value(value) -> str:
       
        if isinstance(value, bool):
            return "YES" if value else "NO"
        elif isinstance(value, list):
            if not value:
                return "()"
            formatted_items = []
            for item in value:
                if isinstance(item, str):
                    formatted_items.append(item)
                else:
                    formatted_items.append(str(item))
            return f"({', '.join(formatted_items)})"
        elif isinstance(value, str):
            return value
        else:
            return str(value)

    try:
        with open(json_file_path, "r", encoding="utf-8") as json_file:
            config_dict = json.load(json_file)
    except Exception as e:
        raise Exception(f"Error reading JSON file: {e}")

    try:
        with open(output_cfg_path, "w", encoding="utf-8") as cfg_file:
            cfg_file.write("% SU2 Configuration File\n")
            cfg_file.write("% Converted from JSON\n\n")
            
            for key, value in config_dict.items():
                formatted_value = format_value(value)
                cfg_file.write(f"{key}= {formatted_value}\n")
                
        print(f"JSON successfully converted to SU2 config: {output_cfg_path}")
        
    except Exception as e:
        raise Exception(f"Error writing config file: {e}")

def create_test_configs():
    """Create test configuration cases for validation testing."""
    
    # Test Case 1: Valid RANS configuration
    valid_rans = {
        "SOLVER": "RANS",
        "KIND_TURB_MODEL": "SST",
        "KIND_TRANS_MODEL": "NONE",
        "INC_DENSITY_MODEL": "CONSTANT",
        "ENERGY_EQUATION": "YES"
    }
    
    # Test Case 2: Invalid - RANS solver without turbulence model
    invalid_rans_no_turb = {
        "SOLVER": "RANS",
        "KIND_TURB_MODEL": "NONE",  # ERROR: RANS requires turbulence model
        "KIND_TRANS_MODEL": "NONE"
    }
    
    # Test Case 3: Invalid - Transition model without turbulence
    invalid_trans_no_turb = {
        "SOLVER": "NAVIER_STOKES",
        "KIND_TURB_MODEL": "NONE",
        "KIND_TRANS_MODEL": "LM"  # ERROR: Transition model requires turbulence
    }
    
    # Test Case 4: Invalid - Euler solver with heat markers
    invalid_euler_heat = {
        "SOLVER": "EULER",
        "KIND_TURB_MODEL": "NONE",
        "MARKER_HEATFLUX": [["wall1", 1000.0]],  # ERROR: Euler incompatible with heat markers
        "MARKER_ISOTHERMAL": [["wall2", 300.0]]  # ERROR: Euler incompatible with temperature markers
    }
    
    # Test Case 5: Invalid - INC_EULER density/energy inconsistency
    invalid_inc_euler = {
        "SOLVER": "INC_EULER",
        "INC_DENSITY_MODEL": "VARIABLE",  # ERROR: Should be CONSTANT for INC_EULER
        "ENERGY_EQUATION": "YES"          # ERROR: Should be NO for INC_EULER
    }
    
    # Test Case 6: Invalid - Inlet type count mismatch
    invalid_inlet_count = {
        "SOLVER": "INC_NAVIER_STOKES",
        "KIND_TURB_MODEL": "NONE",
        "MARKER_INLET": [["inlet1"], ["inlet2"], ["inlet3"]],
        "INC_INLET_TYPE": ["VELOCITY_INLET", "PRESSURE_INLET"]  # ERROR: Should have 3 entries
    }
    
    # Test Case 7: Valid incompressible configuration
    valid_incompressible = {
        "SOLVER": "INC_NAVIER_STOKES",
        "KIND_TURB_MODEL": "NONE",
        "INC_DENSITY_MODEL": "CONSTANT",
        "ENERGY_EQUATION": "NO",
        "MARKER_INLET": [["inlet1"], ["inlet2"]],
        "INC_INLET_TYPE": ["VELOCITY_INLET", "PRESSURE_INLET"]
    }
    
    # Test Case 8: Invalid - LM transition with axisymmetric
    invalid_lm_axisym = {
        "SOLVER": "RANS",
        "KIND_TURB_MODEL": "SST",
        "KIND_TRANS_MODEL": "LM",
        "AXISYMMETRIC": "YES"  # ERROR: LM not compatible with axisymmetric
    }
    
    return {
        "valid_rans": valid_rans,
        "invalid_rans_no_turb": invalid_rans_no_turb,
        "invalid_trans_no_turb": invalid_trans_no_turb,
        "invalid_euler_heat": invalid_euler_heat,
        "invalid_inc_euler": invalid_inc_euler,
        "invalid_inlet_count": invalid_inlet_count,
        "valid_incompressible": valid_incompressible,
        "invalid_lm_axisym": invalid_lm_axisym
    }


def run_enhanced_validation_tests():
    """Run comprehensive validation tests using the enhanced validator."""
    
    print("=" * 80)
    print("SU2 Configuration Cross-Parameter Validation Test Suite")
    print("Testing validation rules extracted from CConfig.cpp")
    print("=" * 80)
    
    try:
        base = Path(__file__).parent.parent
        validator = SU2ConfigValidator(str(base / "su2_validation_schema.json"))
        test_configs = create_test_configs()
        
        results = {}
        for test_name, config in test_configs.items():
            print(f"\n Testing: {test_name}")
            print("-" * 50)
            
            # Perform custom validations
            errors = validator.perform_custom_validations(config)
            
            # Also test against JSON schema if available
            schema_error_messages = []
            if getattr(validator, 'validator', None) is not None:
                try:
                    schema_errors = list(validator.validator.iter_errors(config))
                    schema_error_messages = [{"message": err.message, "type": "schema"} for err in schema_errors]
                except Exception as e:
                    schema_error_messages = [{"message": f"Schema validation error: {str(e)}", "type": "schema"}]
            
            all_errors = errors + schema_error_messages
            is_valid = len(all_errors) == 0
            
            results[test_name] = {
                "valid": is_valid,
                "errors": all_errors,
                "config": config
            }
            
            # Display results
            if is_valid:
                print(" PASSED - Configuration is valid")
            else:
                print(f" FAILED - Found {len(all_errors)} errors:")
                for i, error in enumerate(all_errors, 1):
                    error_type = error.get('type', 'unknown')
                    print(f"   {i}. [{error_type}] {error['message']}")
            
            # Show key config parameters
            print(f"   Config: SOLVER={config.get('SOLVER', 'N/A')}, "
                  f"TURB_MODEL={config.get('KIND_TURB_MODEL', 'N/A')}, "
                  f"TRANS_MODEL={config.get('KIND_TRANS_MODEL', 'N/A')}")
        
        # Summary
        print("\n" + "=" * 80)
        print("VALIDATION TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for r in results.values() if r["valid"])
        total = len(results)
        
        print(f"Total tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        
        expected_failures = [
            "invalid_rans_no_turb", "invalid_trans_no_turb", "invalid_euler_heat",
            "invalid_inc_euler", "invalid_inlet_count", "invalid_lm_axisym"
        ]
        expected_passes = ["valid_rans", "valid_incompressible"]
        
        print("\nExpected Results Check:")
        all_correct = True
        
        for test_name in expected_failures:
            if results[test_name]["valid"]:
                print(f" {test_name} should have FAILED but PASSED")
                all_correct = False
            else:
                print(f" {test_name} correctly FAILED")
        
        for test_name in expected_passes:
            if not results[test_name]["valid"]:
                print(f" {test_name} should have PASSED but FAILED")
                all_correct = False
            else:
                print(f" {test_name} correctly PASSED")
        
        if all_correct:
            print("\n All validation rules are working correctly!")
        else:
            print("\n Some validation rules may need adjustment")
        
        return results
        
    except ImportError as e:
        print(f" Cannot import enhanced validator: {str(e)}")
        print("Make sure enhanced_config_validator.py is available")
        return None
    except Exception as e:
        print(f" Test suite error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    import sys
    
    print("SU2 Configuration Validation Test Suite")
    print("Choose an option:")
    print("1. Run original validation test")
    print("2. Run enhanced cross-parameter validation tests")
    print("3. Convert and validate specific CFG file")
    
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = input("Enter choice (1-3): ").strip()
    
    if choice == "2":
        print("\nRunning enhanced cross-parameter validation tests...")
        run_enhanced_validation_tests()
    elif choice == "3":
        # Original specific file test
        cfg_file = input("Enter CFG file path (default: user/new_2/config_new.cfg): ").strip()
        if not cfg_file:
            cfg_file = r"user/new_2/config_new.cfg"
        
        schema_file = "su2_validation_schema.json"
        json_output_file = "config_2.json"
        
        print("=" * 80)
        print("SU2 CONFIG FILE CONVERSION AND VALIDATION")
        print("=" * 80)
        print(f"Config File: {cfg_file}")
        print(f"Schema File: {schema_file}")
        print(f"JSON Output: {json_output_file}")
        print("=" * 80)
        
        try:
            # Step 1: Convert CFG to JSON and save it
            print("Step 1: Converting CFG to JSON...")
            config_dict = cfg_to_json(cfg_file, json_output_file)
            print(f" Successfully converted {len(config_dict)} configuration parameters")
            
            # Step 2: Validate CFG with schema using predefined function
            print("\nStep 2: Validating CFG against schema...")
            is_valid, validated_config, errors = validate_cfg_with_schema(cfg_file, schema_file)
            
            print("\n" + "=" * 80)
            print("VALIDATION RESULTS")
            print("=" * 80)
            
            if is_valid:
                print(" VALIDATION: PASSED")
                print(f" Configuration is valid according to the schema.")
                print(f" Found {len(validated_config)} valid parameters.")
            else:
                print(" VALIDATION: FAILED")
                print(f" Found {len(errors)} validation errors:")
                
                print(f"\nFirst 5 Validation Errors:")
                for i, error in enumerate(errors[:5], 1):
                    if hasattr(error, 'message'):
                        path = " -> ".join(str(p) for p in error.absolute_path) if hasattr(error, 'absolute_path') and error.absolute_path else "root"
                        print(f"   {i}. Path: {path}")
                        print(f"      Error: {error.message}")
                        if hasattr(error, 'instance'):
                            print(f"      Value: {error.instance}")
                    else:
                        print(f"   {i}. {str(error)}")
                    print()
            
        except FileNotFoundError as e:
            print(f" Error: {e}")
            print("Make sure the config file exists in the current directory.")
        except Exception as e:
            print(f" Unexpected error: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 80)
    else:
        # Original default test
        cfg_file = r"user/new_2/config_new.cfg"  # The SU2 config file to validate
        schema_file = "su2_validation_schema.json"  # Updated to use validation schema
        json_output_file = "config_2.json"  # Output JSON file
        
        print("=" * 80)
        print("SU2 CONFIG FILE CONVERSION AND VALIDATION")
        print("=" * 80)
        print(f"Config File: {cfg_file}")
        print(f"Schema File: {schema_file}")
        print(f"JSON Output: {json_output_file}")
        print("=" * 80)

        try:
            # Step 1: Convert CFG to JSON and save it
            print("Step 1: Converting CFG to JSON...")
            config_dict = cfg_to_json(cfg_file, json_output_file)
            print(f" Successfully converted {len(config_dict)} configuration parameters")
            
            # Step 2: Validate CFG with schema using predefined function
            print("\nStep 2: Validating CFG against schema...")
            is_valid, validated_config, errors = validate_cfg_with_schema(cfg_file, schema_file)
            
            print("\n" + "=" * 80)
            print("VALIDATION RESULTS")
            print("=" * 80)
            print(f"Config File: {cfg_file}")
            print(f"Schema File: {schema_file}")
            print(f"JSON Output: {json_output_file}")
            print(f"Validation Result: {' VALID' if is_valid else ' INVALID'}")
            print(f"Total Parameters: {len(config_dict)}")
            print(f"Validation Errors: {len(errors) if errors else 0}")
            
            if not is_valid and errors:
                print(f"\nFirst 5 Validation Errors:")
                for i, error in enumerate(errors, 1):
                    if hasattr(error, 'message'):
                        path = " -> ".join(str(p) for p in error.absolute_path) if hasattr(error, 'absolute_path') and error.absolute_path else "root"
                        print(f"   {i}. Path: {path}")
                        print(f"      Error: {error.message}")
                        if hasattr(error, 'instance'):
                            print(f"      Value: {error.instance}")
                    else:
                        print(f"   {i}. {str(error)}")
                    print()
            
        except FileNotFoundError as e:
            print(f" Error: {e}")
            print("Make sure the config file exists in the current directory.")
        except Exception as e:
            print(f" Unexpected error: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 80)