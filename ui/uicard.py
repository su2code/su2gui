# definition of the ui cards

import sys
import os
from pathlib import Path

# Add parent directory to path to allow importing from sibling directories
parent_dir = str(Path(__file__).parent.parent.absolute())
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from trame.widgets import vuetify
from trame.app import get_server

server = get_server(client_type='vue2')
#state, ctrl = server.state, server.controller

# Logging function
from core.logger import log

# Main definition of the card for all gittree items.
# note that "active_ui" points to a state change
# the active_ui is set in the main su2gui in def actives_change(ids)
def ui_card(title, ui_name):
    log("info", f"##### def ui_card = {ui_name}")
    with vuetify.VCard(v_show=f"active_ui == '{ui_name}'"):
        vuetify.VCardTitle(
            title,
            classes="grey lighten-1 py-1 grey--text text--darken-3",
            style="user-select: none; cursor: pointer",
            hide_details=True,
            dense=True,
        )
        content = vuetify.VCardText(classes="py-2")
    return content

# subcard, appearing below the main card. Visible depending on the
# selection in the main card
# note that "active_sub_ui" points to a state change
def ui_subcard(title, sub_ui_name):
    log("info", f"##### def ui_subcard = {sub_ui_name}")
    with vuetify.VCard(v_show=f"active_sub_ui == '{sub_ui_name}'"):
        vuetify.VCardTitle(
            title,
            classes="grey lighten-1 py-1 grey--text text--darken-3",
            style="user-select: none; cursor: pointer",
            hide_details=True,
            dense=True,
        )
        content = vuetify.VCardText(classes="py-2")
    return content

# show the card only for children of a head/parent node
def ui_card_children_only(title, parent_ui_name):
    log("info", f"##### def ui_card_children_only = {parent_ui_name}")
    with vuetify.VCard(v_show=f"active_parent_ui == '{parent_ui_name}'"):
        vuetify.VCardTitle(
            title,
            classes="grey lighten-1 py-1 grey--text text--darken-3",
            style="user-select: none; cursor: pointer",
            hide_details=True,
            dense=True,
        )
        content = vuetify.VCardText(classes="py-2")
    return content

# show the card only for head/parent node
def ui_card_parent_only(title, parent_ui_name):
    log("info", f"##### def ui_card_parent_only = {parent_ui_name}")
    with vuetify.VCard(v_show=f"active_head_ui == '{parent_ui_name}'"):
        vuetify.VCardTitle(
            title,
            classes="grey lighten-1 py-1 grey--text text--darken-3",
            style="user-select: none; cursor: pointer",
            hide_details=True,
            dense=True,
        )
        content = vuetify.VCardText(classes="py-2")
    return content