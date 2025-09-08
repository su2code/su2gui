"""
Enhanced SU2 Configuration Validator with Cross-Parameter Validation
Implements JSON Schema validation for SU2 CFD configuration files
based on CConfig.cpp validation logic.
"""

import json
import importlib
import os
_jsonschema_spec = importlib.util.find_spec('jsonschema')
if _jsonschema_spec is not None:  # Optional dependency
    from jsonschema import Draft7Validator  # type: ignore
else:
    Draft7Validator = None  # type: ignore
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import re

class SU2ConfigValidator:
    """
    Advanced validator for SU2 configuration files with cross-parameter validation.
    """
    
    def __init__(self, schema_path: Optional[str] = None, enable_schema: Optional[bool] = None):
        """
        Initialize the validator with schema.
        
        Args:
            schema_path: Path to the validation schema JSON file
            enable_schema: Force enable/disable JSON Schema validation. If None, defaults to False
                           unless environment variable SU2GUI_STRICT_SCHEMA is set to 1/true.
        """
        self.base_path = Path(__file__).parent.parent
        
        # Prefer the repo schema by default; caller can override via schema_path.
        self.validator = None
        # Default behavior: if a schema path is provided or a default schema exists, enable schema
        # unless explicitly disabled. Environment variable can also force enable.
        env_flag = str(os.environ.get('SU2GUI_STRICT_SCHEMA', '')).lower()
        env_enable = env_flag in ('1', 'true', 'yes', 'on')
        if enable_schema is not None:
            self.schema_enabled = bool(enable_schema)
        else:
            # Tentatively enable; we'll confirm once we find a schema file and jsonschema is available
            self.schema_enabled = env_enable

        try:
            # Resolve schema path: explicit > repo default > disabled
            if schema_path is None:
                default_schema = self.base_path / "su2_validation_schema.json"
                schema_file = default_schema if default_schema.exists() else None
            else:
                schema_file = Path(schema_path)

            # Auto-enable if a schema file is present and no explicit disable was set
            if schema_file and schema_file.exists() and Draft7Validator is not None:
                if enable_schema is None and not env_flag:
                    self.schema_enabled = True
            if self.schema_enabled and Draft7Validator is not None and schema_file and schema_file.exists():
                with open(schema_file, 'r', encoding='utf-8') as f:
                    self.validation_schema = json.load(f)
                self.validator = Draft7Validator(self.validation_schema)
        except Exception:
            # Fall back to custom validations only
            self.validator = None
            self.schema_enabled = False
    
    def validate_config_file(self, config_file_path: str, auto_fix: bool = False) -> Dict[str, Any]:
        """
        Validate SU2 configuration file against the complete JSON schema.
        
        Args:
            config_file_path: Path to the SU2 config file (.cfg or .json)
            
        Returns:
            dict: Validation result with 'valid' boolean, 'errors' list, and config data
        """
        try:
            config_path = Path(config_file_path)
            
            # Load and parse the config file
            if config_path.suffix.lower() == '.json':
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
            else:
                config_data = self.convert_cfg_to_json(config_path)
            
            # Perform JSON Schema validation (only if explicitly enabled)
            validation_errors = []
            if self.schema_enabled and self.validator is not None:
                for error in self.validator.iter_errors(config_data):
                    validation_errors.append({
                        'path': list(error.path),
                        'message': error.message,
                        'schema_path': list(error.schema_path),
                        'validator': error.validator,
                        'instance': error.instance
                    })
            
            # Additional custom validations
            custom_errors = self.perform_custom_validations(config_data)
            # Non-fatal guidance warnings
            guidance_warnings = self.perform_guidance_warnings(config_data)

            applied_fixes: List[Dict[str, Any]] = []
            if auto_fix:
                config_data, applied_fixes = self.apply_auto_fixes(config_data, custom_errors)
                # Re-run custom validations after fixes
                custom_errors = self.perform_custom_validations(config_data)
            
            all_errors = validation_errors + custom_errors
            
            return {
                'valid': len(all_errors) == 0,
                'errors': all_errors,
                'warnings': guidance_warnings,
                'config_data': config_data,
                'message': 'Configuration is valid' if len(all_errors) == 0 else f'Found {len(all_errors)} validation errors',
                'schema_errors': len(validation_errors),
                'custom_errors': len(custom_errors),
                'applied_fixes': applied_fixes
            }
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [{'message': f'Error processing file: {str(e)}', 'type': 'processing_error'}],
                'config_data': None,
                'message': f'Processing error: {str(e)}',
                'applied_fixes': []
            }
    
    def perform_custom_validations(self, config_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Perform additional custom validations not covered by JSON Schema.
        
        Args:
            config_data: The parsed configuration data
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check inlet type count matches inlet marker count
        errors.extend(self.validate_inlet_consistency(config_data))
        
        # Check solver-specific parameter consistency
        errors.extend(self.validate_solver_consistency(config_data))
        
        # Check turbulence model dependencies
        errors.extend(self.validate_turbulence_dependencies(config_data))
        
        # Check marker compatibility
        errors.extend(self.validate_marker_compatibility(config_data))
        
        return errors

    def perform_guidance_warnings(self, config_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Produce non-fatal guidance warnings to nudge users about recommended combos.
        Examples:
        - FEM solvers with LES models: suggest checking numerical settings.
        - Harmonic Balance runs: suggest reasonable write frequencies.
        """
        warnings: List[Dict[str, Any]] = []

        solver = config_data.get('SOLVER', '')
        turb_model = config_data.get('KIND_TURB_MODEL', 'NONE')
        time_marching = config_data.get('TIME_MARCHING', 'STEADY')

        # FEM + LES pairing guidance (warn-only)
        fem_solvers = [s for s in [solver] if isinstance(s, str) and s.startswith('FEM_')]
        les_like = turb_model in ['IMPLICIT_LES', 'SMAGORINSKY', 'WALE', 'VREMAN']
        if fem_solvers and les_like:
            warnings.append({
                'path': ['KIND_TURB_MODEL'],
                'message': 'FEM_* with LES (KIND_TURB_MODEL) may require tuned stabilization and filters. Review NUM_METHOD_FEM_FLOW and time discretization.',
                'type': 'fem_les_guidance',
                'solver': solver,
                'turbulence_model': turb_model
            })

        # HB-specific output nudges
        if time_marching == 'HARMONIC_BALANCE':
            out_freq = config_data.get('OUTPUT_WRT_FREQ')
            if out_freq is None:
                warnings.append({
                    'path': ['OUTPUT_WRT_FREQ'],
                    'message': 'For HB runs, consider setting OUTPUT_WRT_FREQ to a small value to capture cycle convergence diagnostics.',
                    'type': 'hb_output_frequency_nudge'
                })
            if 'HB_CONV_WINDOW' not in config_data:
                warnings.append({
                    'path': ['HB_CONV_WINDOW'],
                    'message': 'HB_CONV_WINDOW not set. A value like 20-50 can help stabilize cycle convergence checks.',
                    'type': 'hb_conv_window_nudge'
                })

        return warnings
    
    def validate_inlet_consistency(self, config_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Validate that INC_INLET_TYPE count matches MARKER_INLET count for incompressible solvers.
        """
        errors = []
        
        solver = config_data.get('SOLVER', '')
        marker_inlet = config_data.get('MARKER_INLET', [])
        inc_inlet_type = config_data.get('INC_INLET_TYPE', [])
        # Normalize inc_inlet_type to list
        if isinstance(inc_inlet_type, str):
            inc_inlet_type = [inc_inlet_type]
        elif not isinstance(inc_inlet_type, list):
            inc_inlet_type = []
        
        inlet_count = self._count_markers_in_list(marker_inlet) if isinstance(marker_inlet, list) else 0
        
        if solver in ['INC_EULER', 'INC_NAVIER_STOKES', 'INC_RANS'] and inlet_count:
            if len(inc_inlet_type) != inlet_count:
                errors.append({
                    'path': ['INC_INLET_TYPE'],
                    'message': f'INC_INLET_TYPE must have exactly {inlet_count} entries to match MARKER_INLET count, but found {len(inc_inlet_type)}',
                    'type': 'inlet_count_mismatch',
                    'expected_count': inlet_count,
                    'actual_count': len(inc_inlet_type)
                })
        
        return errors
    
    def validate_solver_consistency(self, config_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Validate solver-specific parameter consistency.
        """
        errors = []
        
        solver = config_data.get('SOLVER', '')
        
        # INC_EULER specific validations
        if solver == 'INC_EULER':
            density_model = config_data.get('INC_DENSITY_MODEL', '')
            # Prefer incompressible energy flag; fall back to ENERGY_EQUATION if present
            inc_energy = config_data.get('INC_ENERGY_EQUATION', config_data.get('ENERGY_EQUATION', None))

            # Normalize possible string booleans
            if isinstance(inc_energy, str):
                inc_energy_norm = inc_energy.upper() in ['YES', 'TRUE', 'ON']
            else:
                inc_energy_norm = bool(inc_energy) if inc_energy is not None else None

            if density_model != 'CONSTANT' or inc_energy_norm is not False:
                errors.append({
                    'path': ['SOLVER'],
                    'message': 'INC_EULER requires INC_DENSITY_MODEL=CONSTANT and INC_ENERGY_EQUATION=NO',
                    'type': 'inc_euler_consistency',
                    'current_density_model': density_model,
                    'current_inc_energy_equation': inc_energy
                })
        
        return errors
    
    def validate_turbulence_dependencies(self, config_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Validate turbulence and transition model dependencies.
        """
        errors = []
        
        solver = config_data.get('SOLVER', '')
        turb_model = config_data.get('KIND_TURB_MODEL', 'NONE')
        trans_model = config_data.get('KIND_TRANS_MODEL', 'NONE')

        # RANS solvers require a turbulence model
        if solver in ['RANS', 'INC_RANS'] and turb_model in ['NONE', 'NO_TURB_MODEL', None, '']:
            errors.append({
                'path': ['KIND_TURB_MODEL'],
                'message': f'{solver} requires an active turbulence model (e.g., SA or SST), but KIND_TURB_MODEL is {turb_model}',
                'type': 'rans_requires_turbulence',
                'solver': solver,
                'turbulence_model': turb_model
            })
        
        # Check transition model requires turbulence model
        if trans_model not in ['NONE', 'NO_TRANS_MODEL'] and turb_model in ['NONE', 'NO_TURB_MODEL']:
            errors.append({
                'path': ['KIND_TRANS_MODEL'],
                'message': f'Transition model {trans_model} requires an active turbulence model, but KIND_TURB_MODEL is {turb_model}',
                'type': 'transition_requires_turbulence',
                'transition_model': trans_model,
                'turbulence_model': turb_model
            })
        
        # LM transition model 2D restriction (if we can detect axisymmetric)
        if trans_model == 'LM' and (config_data.get('AXISYMMETRIC', 'NO') == 'YES' or config_data.get('AXISYMMETRIC') is True):
            errors.append({
                'path': ['KIND_TRANS_MODEL'],
                'message': 'LM transition model is not compatible with axisymmetric flows',
                'type': 'lm_axisymmetric_incompatible'
            })
        
        return errors
    
    def validate_marker_compatibility(self, config_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Validate marker compatibility with solver types.
        """
        errors = []
        
        solver = config_data.get('SOLVER', '')
        
        # Heat/temperature markers incompatible with Euler solvers
        if solver in ['EULER', 'INC_EULER', 'FEM_EULER', 'NEMO_EULER']:
            heat_markers = [
                'MARKER_HEATFLUX', 'MARKER_ISOTHERMAL', 'MARKER_HEATTRANSFER',
                'MARKER_SMOLUCHOWSKI_MAXWELL', 'MARKER_CHT_INTERFACE'
            ]
            
            for marker_type in heat_markers:
                markers = config_data.get(marker_type, [])
                if markers:
                    errors.append({
                        'path': [marker_type],
                        'message': f'{marker_type} is not compatible with Euler solver {solver}. Euler solvers only support slip walls.',
                        'type': 'euler_heat_marker_incompatible',
                        'solver': solver,
                        'incompatible_markers': len(markers)
                    })
        
        return errors

    def _count_markers_in_list(self, marker_list: Any) -> int:
        """
        Best-effort count of markers from a flattened SU2 list like
        (name, v1, v2, name2, v1, v2). We count string tokens.
        Also supports list-of-tuples form: [(name, ...), (name2, ...)].
        """
        if not isinstance(marker_list, list):
            return 0
        count = 0
        for el in marker_list:
            if isinstance(el, str):
                count += 1
            elif isinstance(el, (list, tuple)) and el and isinstance(el[0], str):
                count += 1
        return count

    def apply_auto_fixes(self, config_data: Dict[str, Any], current_errors: Optional[List[Dict[str, Any]]] = None) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Apply safe auto-fixes to make the configuration runnable. Returns (fixed_config, fixes_applied).
        The strategy is conservative: disable incompatible features or fill missing entries with reasonable defaults.
        """
        cfg = dict(config_data) if isinstance(config_data, dict) else {}
        fixes: List[Dict[str, Any]] = []

        solver = cfg.get('SOLVER', '')

        # INC_EULER requirements
        if solver == 'INC_EULER':
            if cfg.get('INC_DENSITY_MODEL') != 'CONSTANT':
                old = cfg.get('INC_DENSITY_MODEL')
                cfg['INC_DENSITY_MODEL'] = 'CONSTANT'
                fixes.append({'path': ['INC_DENSITY_MODEL'], 'message': f"Set INC_DENSITY_MODEL to CONSTANT (was {old})"})
            inc_energy = cfg.get('INC_ENERGY_EQUATION', cfg.get('ENERGY_EQUATION', None))
            inc_energy_norm = None
            if isinstance(inc_energy, str):
                inc_energy_norm = inc_energy.upper() in ['YES', 'TRUE', 'ON']
            elif inc_energy is not None:
                inc_energy_norm = bool(inc_energy)
            if inc_energy_norm is not False:
                cfg['INC_ENERGY_EQUATION'] = False
                fixes.append({'path': ['INC_ENERGY_EQUATION'], 'message': 'Set INC_ENERGY_EQUATION to NO for INC_EULER'})

        # Transition requires turbulence -> disable transition if no turb
        turb_model = cfg.get('KIND_TURB_MODEL', 'NONE')
        trans_model = cfg.get('KIND_TRANS_MODEL', 'NONE')
        if trans_model not in ['NONE', 'NO_TRANS_MODEL'] and turb_model in ['NONE', 'NO_TURB_MODEL']:
            old = trans_model
            cfg['KIND_TRANS_MODEL'] = 'NONE'
            fixes.append({'path': ['KIND_TRANS_MODEL'], 'message': f'Disabled transition model {old} because no turbulence model is active'})

        # LM transition with axisymmetric -> disable LM
        if cfg.get('AXISYMMETRIC', 'NO') in ['YES', True] and cfg.get('KIND_TRANS_MODEL') == 'LM':
            cfg['KIND_TRANS_MODEL'] = 'NONE'
            fixes.append({'path': ['KIND_TRANS_MODEL'], 'message': 'Disabled LM transition for axisymmetric flow'})

        # Inlet type count mismatches -> extend or trim INC_INLET_TYPE to match the number of inlet markers
        if solver in ['INC_EULER', 'INC_NAVIER_STOKES', 'INC_RANS']:
            marker_inlet = cfg.get('MARKER_INLET', [])
            inlet_count = self._count_markers_in_list(marker_inlet)
            if inlet_count > 0:
                types = cfg.get('INC_INLET_TYPE', [])
                if isinstance(types, str):
                    types = [types]
                types = list(types) if isinstance(types, list) else []
                if len(types) < inlet_count:
                    default_type = types[-1] if types else 'VELOCITY_INLET'
                    missing = inlet_count - len(types)
                    types.extend([default_type] * missing)
                    cfg['INC_INLET_TYPE'] = types
                    fixes.append({'path': ['INC_INLET_TYPE'], 'message': f'Extended INC_INLET_TYPE to {inlet_count} entries using default {default_type}'})
                elif len(types) > inlet_count:
                    cfg['INC_INLET_TYPE'] = types[:inlet_count]
                    fixes.append({'path': ['INC_INLET_TYPE'], 'message': f'Trimmed INC_INLET_TYPE to {inlet_count} entries to match MARKER_INLET'})

        # Euler solvers cannot use thermal wall markers -> convert to MARKER_EULER
        if solver in ['EULER', 'INC_EULER', 'FEM_EULER', 'NEMO_EULER']:
            heat_marker_keys = ['MARKER_HEATFLUX', 'MARKER_ISOTHERMAL', 'MARKER_HEATTRANSFER']
            euler_list = cfg.get('MARKER_EULER', [])
            if isinstance(euler_list, str):
                euler_list = [euler_list]
            moved = []
            for key in heat_marker_keys:
                if key in cfg and isinstance(cfg[key], list) and cfg[key]:
                    # Collect names (string entries)
                    names = [el for el in cfg[key] if isinstance(el, str)]
                    moved.extend(names)
                    # Remove incompatible marker
                    cfg.pop(key, None)
            if moved:
                euler_list = list(euler_list) + moved
                cfg['MARKER_EULER'] = euler_list
                fixes.append({'path': ['MARKER_EULER'], 'message': f'Converted thermal wall markers to Euler walls: {moved}'})

        return cfg, fixes
    
    def convert_cfg_to_json(self, cfg_file_path: Path) -> Dict[str, Any]:
        """
        Convert SU2 .cfg file to JSON format for validation.
        Enhanced version with better parsing and error handling.
        """
        config_dict = {}
        
        try:
            with open(cfg_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                # Skip comments and empty lines
                if not line or line.startswith('%'):
                    i += 1
                    continue
                
                # Handle line continuation
                while line.endswith('\\') and i + 1 < len(lines):
                    i += 1
                    next_line = lines[i].strip()
                    if next_line.startswith('%'):
                        break
                    line = line[:-1] + ' ' + next_line
                
                # Parse key-value pairs
                if '=' in line:
                    # Remove inline comments
                    if '%' in line:
                        comment_pos = line.index('%')
                        line = line[:comment_pos].strip()
                    
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Parse the value
                    parsed_value = self.parse_config_value(value)
                    config_dict[key] = parsed_value
                
                i += 1
                
        except Exception as e:
            raise ValueError(f"Error parsing CFG file: {str(e)}")
        
        return config_dict
    
    def parse_config_value(self, value: Any) -> Any:
        """
        Parse configuration value from string to appropriate type.
        Enhanced with better type detection and error handling.
        """
        # If already parsed to non-string, return as-is
        if not isinstance(value, str):
            return value

        value = value.strip()
        
        # Handle parentheses (arrays/tuples)
        if value.startswith('(') and value.endswith(')'):
            inner = value[1:-1].strip()
            if not inner:
                return []
            
            # Handle nested parentheses for complex structures
            elements = self.split_respecting_parentheses(inner)
            return [self.parse_single_value(elem.strip()) for elem in elements]
        
        return self.parse_single_value(value)
    
    def split_respecting_parentheses(self, text: str) -> List[str]:
        """
        Split text by commas while respecting parentheses nesting.
        """
        elements = []
        current = ""
        paren_depth = 0
        
        for char in text:
            if char == '(':
                paren_depth += 1
                current += char
            elif char == ')':
                paren_depth -= 1
                current += char
            elif char == ',' and paren_depth == 0:
                elements.append(current)
                current = ""
            else:
                current += char
        
        if current:
            elements.append(current)
        
        return elements
    
    def parse_single_value(self, value: Any) -> Any:
        """
        Parse a single value to its appropriate type with enhanced type detection.
        """
        # If already a non-string, return as-is
        if not isinstance(value, str):
            return value

        value = value.strip()
        
        # Handle empty values
        if not value:
            return ""
        
        # Boolean values (SU2 style)
        if value.upper() in ['YES', 'TRUE', 'ON']:
            return True
        elif value.upper() in ['NO', 'FALSE', 'OFF']:
            return False
        
        # Numeric values
        try:
            # Try integer first
            if '.' not in value and 'e' not in value.lower() and 'E' not in value:
                return int(value)
            else:
                return float(value)
        except ValueError:
            pass
        
        # String value (remove quotes if present)
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            return value[1:-1]
        
        return value
    
    def validate_with_existing_workflow(self, filename_cfg: str = "config.cfg") -> Dict[str, Any]:
        """
        Validate config file using existing su2_json.py workflow integration.
        """
        try:
            from core.su2_json import state
            from core.logger import log
            
            config_path = self.base_path / "user" / state.case_name / filename_cfg
            
            # Perform validation
            validation_result = self.validate_config_file(str(config_path))
            
            if validation_result['valid']:
                log("info", f"✓ Configuration file {filename_cfg} passed all validation checks")
                
                # Update state.jsonData with validated config
                if validation_result['config_data']:
                    state.jsonData.update(validation_result['config_data'])
                    log("info", "JSON data updated with validated configuration")
            else:
                log("error", f"✗ Configuration file {filename_cfg} has {len(validation_result['errors'])} validation errors:")
                
                # Group errors by type for better reporting
                schema_errors = [e for e in validation_result['errors'] if 'validator' in e]
                custom_errors = [e for e in validation_result['errors'] if 'type' in e]
                
                if schema_errors:
                    log("error", f"  Schema validation errors ({len(schema_errors)}):")
                    for error in schema_errors[:5]:  # Limit to first 5
                        path = "  ".join(str(p) for p in error['path']) if error['path'] else 'root'
                        log("error", f"    {path}: {error['message']}")
                    
                    if len(schema_errors) > 5:
                        log("error", f"    ... and {len(schema_errors) - 5} more schema errors")
                
                if custom_errors:
                    log("error", f"  Cross-parameter validation errors ({len(custom_errors)}):")
                    for error in custom_errors[:5]:  # Limit to first 5
                        path = "  ".join(str(p) for p in error.get('path', [])) if error.get('path') else 'root'
                        log("error", f"    {path}: {error['message']}")
                    
                    if len(custom_errors) > 5:
                        log("error", f"    ... and {len(custom_errors) - 5} more cross-parameter errors")

                # Log guidance warnings if any
                guidance_warnings = validation_result.get('warnings', [])
                if guidance_warnings:
                    log("warn", f"  Guidance warnings ({len(guidance_warnings)}):")
                    for warn in guidance_warnings[:5]:
                        path = "  ".join(str(p) for p in warn.get('path', [])) if warn.get('path') else 'root'
                        log("warn", f"    {path}: {warn['message']}")
                    if len(guidance_warnings) > 5:
                        log("warn", f"    ... and {len(guidance_warnings) - 5} more warnings")
            
            return validation_result
            
        except Exception as e:
            error_msg = f"Error validating config file: {str(e)}"
            try:
                from core.logger import log
                log("error", error_msg)
            except ImportError:
                print(error_msg)
            
            return {
                'valid': False,
                'errors': [{'message': error_msg, 'type': 'validation_error'}],
                'config_data': None,
                'message': f'Validation error: {str(e)}'
            }
    
    def generate_validation_report(self, validation_result: Dict[str, Any]) -> str:
        """
        Generate a detailed validation report.
        """
        report = []
        report.append("=" * 60)
        report.append("SU2 Configuration Validation Report")
        report.append("=" * 60)
        
        if validation_result['valid']:
            report.append("✓ VALIDATION PASSED")
            report.append(f"Configuration is valid with no errors found.")
        else:
            report.append("✗ VALIDATION FAILED")
            report.append(f"Found {len(validation_result['errors'])} validation errors")
            
            # Group and display errors
            schema_errors = [e for e in validation_result['errors'] if 'validator' in e]
            custom_errors = [e for e in validation_result['errors'] if 'type' in e]
            
            if schema_errors:
                report.append(f"\nSchema Validation Errors ({len(schema_errors)}):")
                report.append("-" * 40)
                for i, error in enumerate(schema_errors, 1):
                    path = "  ".join(str(p) for p in error['path']) if error['path'] else 'root'
                    report.append(f"{i}. Path: {path}")
                    report.append(f"   Error: {error['message']}")
                    if 'instance' in error:
                        report.append(f"   Value: {error['instance']}")
                    report.append("")
            
            if custom_errors:
                report.append(f"\nCross-Parameter Validation Errors ({len(custom_errors)}):")
                report.append("-" * 40)
                for i, error in enumerate(custom_errors, 1):
                    path = "  ".join(str(p) for p in error.get('path', [])) if error.get('path') else 'root'
                    report.append(f"{i}. Path: {path}")
                    report.append(f"   Error: {error['message']}")
                    report.append(f"   Type: {error.get('type', 'unknown')}")
                    report.append("")

        # Include guidance warnings
        warnings = validation_result.get('warnings', [])
        if warnings:
            report.append(f"\nGuidance Warnings ({len(warnings)}):")
            report.append("-" * 40)
            for i, warn in enumerate(warnings, 1):
                path = "  ".join(str(p) for p in warn.get('path', [])) if warn.get('path') else 'root'
                report.append(f"{i}. Path: {path}")
                report.append(f"   Warning: {warn['message']}")
                report.append(f"   Type: {warn.get('type', 'guidance')}")
                report.append("")
        
        report.append("=" * 60)
        return "\n".join(report)


# Convenience functions for integration with existing codebase
def validate_su2_config(config_file_path: str, schema_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to validate a SU2 config file.
    
    Args:
        config_file_path: Path to the config file
        schema_path: Optional path to validation schema
        
    Returns:
        Validation result dictionary
    """
    validator = SU2ConfigValidator(schema_path)
    return validator.validate_config_file(config_file_path)


def check_config_with_workflow(filename_cfg: str = "config.cfg") -> Dict[str, Any]:
    """
    Convenience function for workflow integration.
    """
    validator = SU2ConfigValidator()
    return validator.validate_with_existing_workflow(filename_cfg)


# Example usage and testing
if __name__ == "__main__":
    # Test the validator (custom validations only by default)
    validator = SU2ConfigValidator()
    
    # Example config for testing
    test_config = {
        "SOLVER": "RANS",
        "KIND_TURB_MODEL": "NONE",  # This should trigger an error
        "KIND_TRANS_MODEL": "LM",   # This should trigger an error (no turb model)
        "MARKER_INLET": [["inlet1"], ["inlet2"]],
        "INC_INLET_TYPE": ["VELOCITY_INLET"]  # This should trigger count mismatch
    }
    
    print("Testing validation with problematic config...")
    # This would normally validate against a file, but we can test the custom validations
    errors = validator.perform_custom_validations(test_config)
    
    print(f"Found {len(errors)} custom validation errors:")
    for error in errors:
        print(f"  - {error['message']}")
