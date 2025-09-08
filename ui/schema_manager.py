"""
JSON Schema Management UI
Provides GUI dialog for viewing, editing, and validating JSON schema
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to path
parent_dir = str(Path(__file__).parent.parent.absolute())
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from trame.widgets import vuetify, html
from ui.uicard import server, ui_card, ui_subcard
from core.logger import log

# Extract state and controller from the server
state, ctrl = server.state, server.controller

# Schema management state variables
state.show_schema_dialog = False
state.schema_properties = {}
state.selected_property = None
state.new_property_name = ""
state.new_property_type = "string"
state.new_property_description = ""
state.new_property_default = ""
state.new_property_enum = ""
state.property_types = ["string", "number", "integer", "boolean", "array", "object"]
state.validation_results = []
state.schema_validation_status = "Not validated"

@ctrl.trigger("load_schema_properties")
def load_schema_properties():
    """Load schema properties for display in GUI"""
    try:
        import json
        from pathlib import Path
        
        schema_path = Path(__file__).parent.parent / "user" / "start" / "JsonSchema.json"
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        state.schema_properties = schema.get("properties", {})
        log("info", f"Loaded {len(state.schema_properties)} schema properties")
    except Exception as e:
        log("error", f"Error loading schema properties: {e}")

@ctrl.trigger("validate_configuration")
def validate_configuration():
    """Validate current configuration against schema"""
    try:
        from core.json_validation import validate_config_standalone
        from pathlib import Path
        
        schema_path = str(Path(__file__).parent.parent / "user" / "start" / "JsonSchema.json")
        config_path = str(Path(__file__).parent.parent / "user" / "start" / "config_new.json")
        
        is_valid = validate_config_standalone(schema_path, config_path)
        
        if is_valid:
            state.schema_validation_status = " Valid"
            state.validation_results = []
        else:
            state.schema_validation_status = " Invalid"
            state.validation_results = []  # Simplified - errors logged elsewhere
        
        state.dirty("schema_validation_status", "validation_results")
        
    except Exception as e:
        log("error", f"Validation error: {e}")
        state.schema_validation_status = "Error"

@ctrl.trigger("add_schema_property")
def add_schema_property():
    """Add new property to schema"""
    try:
        if not state.new_property_name.strip():
            log("error", "Property name cannot be empty")
            return
        
        # Create new property definition
        new_prop = {
            "type": state.new_property_type,
            "description": state.new_property_description
        }
        
        # Add default value if provided
        if state.new_property_default.strip():
            try:
                if state.new_property_type == "string":
                    new_prop["default"] = state.new_property_default
                elif state.new_property_type == "number":
                    new_prop["default"] = float(state.new_property_default)
                elif state.new_property_type == "integer":
                    new_prop["default"] = int(state.new_property_default)
                elif state.new_property_type == "boolean":
                    new_prop["default"] = state.new_property_default.lower() in ["true", "1", "yes"]
                elif state.new_property_type == "array":
                    new_prop["default"] = json.loads(state.new_property_default)
                elif state.new_property_type == "object":
                    new_prop["default"] = json.loads(state.new_property_default)
            except (ValueError, json.JSONDecodeError):
                log("error", f"Invalid default value for type {state.new_property_type}")
                return
        
        # Add enum values if provided
        if state.new_property_enum.strip() and state.new_property_type == "string":
            enum_values = [val.strip() for val in state.new_property_enum.split(",")]
            new_prop["enum"] = enum_values
          # Update schema
        from pathlib import Path
        schema_path = Path(__file__).parent.parent / "user" / "start" / "JsonSchema.json"
        
        # Load current schema
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        if "properties" not in schema:
            schema["properties"] = {}
        
        schema["properties"][state.new_property_name] = new_prop
        
        # Save updated schema
        with open(schema_path, 'w') as f:
            json.dump(schema, f, indent=2)
        
        # Reload properties
        load_schema_properties()
        
        # Clear form
        state.new_property_name = ""
        state.new_property_description = ""
        state.new_property_default = ""
        state.new_property_enum = ""
        
        log("info", f"Added new property: {state.new_property_name}")
        
    except Exception as e:
        log("error", f"Error adding property: {e}")

@ctrl.trigger("remove_schema_property")
def remove_schema_property(property_name):
    """Remove property from schema"""
    try:
        from pathlib import Path
        schema_path = Path(__file__).parent.parent / "user" / "start" / "JsonSchema.json"
        
        # Load current schema
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        if "properties" in schema and property_name in schema["properties"]:
            del schema["properties"][property_name]
            
            # Save updated schema
            with open(schema_path, 'w') as f:
                json.dump(schema, f, indent=2)
                
            load_schema_properties()
            log("info", f"Removed property: {property_name}")
        else:
            log("error", f"Property {property_name} not found in schema")
            
    except Exception as e:
        log("error", f"Error removing property: {e}")

@ctrl.trigger("save_schema")
def save_schema():
    """Save current schema to file"""
    try:
        from pathlib import Path
        schema_path = Path(__file__).parent.parent / "user" / "start" / "JsonSchema.json"
        
        # Load current schema
        with open(schema_path, 'r') as f:
            schema = json.load(f)
            
        # Save it back (this function can be extended for more operations)
        with open(schema_path, 'w') as f:
            json.dump(schema, f, indent=2)
        log("info", "Schema saved successfully")
    except Exception as e:
        log("error", f"Error saving schema: {e}")

@ctrl.trigger("export_schema")
def export_schema():
    """Export schema to file"""
    try:
        from pathlib import Path
        schema_path = Path(__file__).parent.parent / "user" / "start" / "JsonSchema.json"
        
        # Load current schema
        with open(schema_path, 'r') as f:
            schema = json.load(f)
            
        export_path = str(schema_path).replace('.json', '_exported.json')
        with open(export_path, 'w') as f:
            json.dump(schema, f, indent=2)
        log("info", f"Schema exported to: {export_path}")
        return export_path
    except Exception as e:
        log("error", f"Error exporting schema: {e}")
        return None

def create_schema_dialog():
    """Create the schema management dialog"""
    
    with vuetify.VDialog(
        v_model=("show_schema_dialog", False),
        max_width="1200px",
        persistent=True,
    ):
        with vuetify.VCard():
            # Header
            with vuetify.VCardTitle(
                class_="headline primary white--text",
                style="position: sticky; top: 0; z-index: 1;"
            ):
                html.Span("JSON Schema Manager")
                vuetify.VSpacer()
                vuetify.VBtn(
                    icon=True,
                    click="show_schema_dialog = false",
                    children=[vuetify.VIcon("mdi-close")]
                )
            
            with vuetify.VCardText():
                # Validation Status
                with vuetify.VRow():
                    with vuetify.VCol(cols=12):
                        with vuetify.VAlert(
                            type="info",
                            border="left",
                            colored_border=True,
                        ):
                            html.Div("{{ schema_validation_status }}")
                
                # Validation and Export buttons
                with vuetify.VRow():
                    with vuetify.VCol(cols=12):
                        vuetify.VBtn(
                            "Load Schema",
                            color="primary",
                            click=ctrl.load_schema_properties,
                            style="margin-right: 10px;"
                        )
                        vuetify.VBtn(
                            "Validate Config",
                            color="success",
                            click=ctrl.validate_configuration,
                            style="margin-right: 10px;"
                        )
                        vuetify.VBtn(
                            "Save Schema",
                            color="warning",
                            click=ctrl.save_schema,
                            style="margin-right: 10px;"
                        )
                        vuetify.VBtn(
                            "Export Schema",
                            color="info",
                            click=ctrl.export_schema
                        )
                
                # Tabs for different sections
                with vuetify.VTabs(v_model="schema_tab", background_color="primary", dark=True):
                    vuetify.VTab("Properties")
                    vuetify.VTab("Add Property")
                    vuetify.VTab("Validation Results")
                
                with vuetify.VTabsItems(v_model="schema_tab"):
                    # Properties Tab
                    with vuetify.VTabItem():
                        create_properties_view()
                    
                    # Add Property Tab
                    with vuetify.VTabItem():
                        create_add_property_form()
                    
                    # Validation Results Tab
                    with vuetify.VTabItem():
                        create_validation_results_view()

def create_properties_view():
    """Create the properties view tab"""
    with vuetify.VContainer():
        with vuetify.VRow():
            with vuetify.VCol(cols=12):
                html.H3("Schema Properties", class_="mb-4")
                
                # Properties table
                with vuetify.VDataTable(
                    headers=[
                        {"text": "Property", "value": "name"},
                        {"text": "Type", "value": "type"},
                        {"text": "Description", "value": "description"},
                        {"text": "Default", "value": "default"},
                        {"text": "Actions", "value": "actions", "sortable": False}
                    ],
                    items=("schema_properties_list", []),
                    class_="elevation-1"
                ):
                    with vuetify.Template(v_slot_item_actions="{ item }"):
                        vuetify.VBtn(
                            "Delete",
                            color="error",
                            small=True,
                            click=f"remove_schema_property(item.name)"
                        )

def create_add_property_form():
    """Create the add property form"""
    with vuetify.VContainer():
        with vuetify.VRow():
            with vuetify.VCol(cols=12):
                html.H3("Add New Property", class_="mb-4")
        
        with vuetify.VRow():
            with vuetify.VCol(cols=6):
                vuetify.VTextField(
                    label="Property Name",
                    v_model=("new_property_name", ""),
                    required=True,
                    outlined=True
                )
            
            with vuetify.VCol(cols=6):
                vuetify.VSelect(
                    label="Property Type",
                    v_model=("new_property_type", "string"),
                    items=("property_types", []),
                    outlined=True
                )
        
        with vuetify.VRow():
            with vuetify.VCol(cols=12):
                vuetify.VTextarea(
                    label="Description",
                    v_model=("new_property_description", ""),
                    outlined=True,
                    rows=2
                )
        
        with vuetify.VRow():
            with vuetify.VCol(cols=6):
                vuetify.VTextField(
                    label="Default Value",
                    v_model=("new_property_default", ""),
                    outlined=True,
                    hint="JSON format for arrays/objects"
                )
            
            with vuetify.VCol(cols=6):
                vuetify.VTextField(
                    label="Enum Values (comma-separated)",
                    v_model=("new_property_enum", ""),
                    outlined=True,
                    hint="For string types only"
                )
        
        with vuetify.VRow():
            with vuetify.VCol(cols=12):
                vuetify.VBtn(
                    "Add Property",
                    color="success",
                    click=ctrl.add_schema_property,
                    block=True
                )

def create_validation_results_view():
    """Create the validation results view"""
    with vuetify.VContainer():
        with vuetify.VRow():
            with vuetify.VCol(cols=12):
                html.H3("Validation Results", class_="mb-4")
        
        # Show validation errors if any
        with html.Div(v_if="validation_results.length > 0"):
            with vuetify.VAlert(
                type="error",
                border="left",
                colored_border=True,
                class_="mb-4"
            ):
                html.Div("Configuration validation failed. See errors below:")
            
            # Error list
            with html.Div(v_for="(error, index) in validation_results", key="index"):
                with vuetify.VCard(class_="mb-2"):
                    with vuetify.VCardText():
                        html.Strong("Path: {{ error.path.join('  ') || 'root' }}")
                        html.Br()
                        html.Span("Message: {{ error.message }}")
                        html.Br()
                        html.Span("Invalid value: {{ error.invalid_value }}")
        
        # Show success message if valid
        with html.Div(v_else=""):
            with vuetify.VAlert(
                type="success",
                border="left",
                colored_border=True,
            ):
                html.Div("No validation errors found. Configuration is valid!")

# Controller to open schema dialog
@ctrl.trigger("open_schema_dialog")
def open_schema_dialog():
    """Open the schema management dialog"""
    state.show_schema_dialog = True
    load_schema_properties()

# Initialize schema tab
state.schema_tab = 0

# Convert schema properties to list format for table display
@state.change("schema_properties")
def update_properties_list(schema_properties, **kwargs):
    """Update properties list when schema changes"""
    props_list = []
    for name, prop_def in schema_properties.items():
        props_list.append({
            "name": name,
            "type": prop_def.get("type", "unknown"),
            "description": prop_def.get("description", ""),
            "default": str(prop_def.get("default", ""))
        })
    state.schema_properties_list = props_list
