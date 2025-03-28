"""
A wrapper around EDMCs Configuration
"""
import os
import l10n
import functools
from massacre.logger_factory import logger
from massacre.version_check import download_url
from typing import Callable, Optional
from config import config
import tkinter as tk
from ttkHyperlinkLabel import HyperlinkLabel
# noinspection PyPep8Naming
import myNotebook as nb

_ = functools.partial(l10n.Translations.translate, context=__file__)
plugin_name = os.path.basename(os.path.dirname(__file__))

class Configuration:
    """
    Abstraction around the config store
    """

    #######################################
    @property
    def check_updates(self):
        return config.get_bool(f"{self.plugin_name}.check_updates", default=True)

    @check_updates.setter
    def check_updates(self, value: bool):
        config.set(f"{self.plugin_name}.check_updates", value)

    #######################################
    @property
    def display_delta_column(self):
        return config.get_bool(f"{self.plugin_name}.display_delta_column", default=True)

    @display_delta_column.setter
    def display_delta_column(self, value: bool):
        config.set(f"{self.plugin_name}.display_delta_column", value)

    #######################################
    @property
    def display_sum_row(self):
        return config.get_bool(f"{self.plugin_name}.display_sum_row", default=True)

    @display_sum_row.setter
    def display_sum_row(self, value: bool):
        config.set(f"{self.plugin_name}.display_sum_row", value)

    #######################################
    @property
    def display_ratio_and_cr_per_kill_row(self):
        return config.get_bool(f"{self.plugin_name}.display_ratio_and_cr_per_kill_row", default=True)

    @display_ratio_and_cr_per_kill_row.setter
    def display_ratio_and_cr_per_kill_row(self, value: bool):
        config.set(f"{self.plugin_name}.display_ratio_and_cr_per_kill_row", value)

    #######################################
    @property
    def display_first_user_help(self):
        return config.get_bool(f"{self.plugin_name}.display_first_user_help", default=True)

    @display_first_user_help.setter
    def display_first_user_help(self, value: bool):
        config.set(f"{self.plugin_name}.display_first_user_help", value)
    
    #######################################
    @property
    def display_mission_count(self):
        return config.get_bool(f"{self.plugin_name}.display_mission_count", default=True)
    
    @display_mission_count.setter
    def display_mission_count(self, value: bool):
        config.set(f"{self.plugin_name}.display_mission_count", value)

    #######################################
    def __init__(self, plugin_name: str):
       self.plugin_name = plugin_name
       self.config_changed_listeners: list[Callable[[Configuration], None]] = []

    def notify_about_changes(self, data: dict[str, tk.Variable]):
        keys = data.keys()

        if "check_updates" in keys:
            self.check_updates = data["check_updates"].get()
        if "display_delta_column" in keys:
            self.display_delta_column = data["display_delta_column"].get()
        if "display_sum_row" in keys:
            self.display_sum_row = data["display_sum_row"].get()
        if "display_ratio_and_cr_per_kill_row" in keys:
            self.display_ratio_and_cr_per_kill_row = data["display_ratio_and_cr_per_kill_row"].get()
        if "overlay_enabled" in keys:
            self.overlay_enabled = data["overlay_enabled"].get()
        if "overlay_ttl" in keys:
            self.overlay_ttl = data['overlay_ttl'].get()
        if "display_mission_count" in keys:
            self.display_mission_count = data['display_mission_count'].get()

        for listener in self.config_changed_listeners:
            listener(self)
        

configuration = Configuration(plugin_name)


__setting_changes: dict[str, tk.Variable] = {}
"""
Changes made in the Prefs-UI are stored here. If EDMC notifies the plugin that changes have been applied values from
this dict are then applied to the config.
"""


def push_new_changes():
    """Callback to be used when the user has closed the Settings. This applies changes to the Config."""
    import massacre.integrations.main
    massacre.integrations.main.notify_about_settings_finished()
    
    configuration.notify_about_changes(__setting_changes)
    __setting_changes.clear()


def build_settings_ui(root: nb.Notebook) -> tk.Frame:
    """
    Builds the UI for the Prefs-Tab for this Plugin.
    """
    checkbox_offset = 10
    title_offset = 20

    frame = nb.Frame(root) #type: ignore
    frame.columnconfigure(1, weight=1)
    __setting_changes.clear()
    __setting_changes["check_updates"] = \
        tk.IntVar(value=configuration.check_updates)
    __setting_changes["display_delta_column"] = \
        tk.IntVar(value=configuration.display_delta_column)
    __setting_changes["display_sum_row"] = \
        tk.IntVar(value=configuration.display_sum_row)
    __setting_changes["display_ratio_and_cr_per_kill_row"] = \
        tk.IntVar(value=configuration.display_ratio_and_cr_per_kill_row)
    __setting_changes["display_mission_count"] = \
        tk.IntVar(value=configuration.display_mission_count)


    nb.Label(frame, text=_("UI Settings"), pady=10).grid(sticky=tk.W, padx=title_offset)
    ui_settings_checkboxes = [
        nb.Checkbutton(frame, text=_("Display Delta-Column"),
                       variable=__setting_changes["display_delta_column"]),
        nb.Checkbutton(frame, text=_("Display Sum-Row"),
                       variable=__setting_changes["display_sum_row"]),
        nb.Checkbutton(frame, text=_("Display Summary-Row"),
                       variable=__setting_changes["display_ratio_and_cr_per_kill_row"]),
        nb.Checkbutton(frame, text=_("Display Mission Count"),
                        variable=__setting_changes["display_mission_count"])
    ]
    for entry in ui_settings_checkboxes:
        entry.grid(columnspan=2, padx=checkbox_offset, sticky=tk.W)
 
    nb.Label(frame, text=_("Other"), pady=10, padx=title_offset).grid(sticky=tk.W)
    nb.Checkbutton(frame, text=_("Check for Updates on Start"), variable=__setting_changes["check_updates"])\
        .grid(columnspan=2, sticky=tk.W, padx=checkbox_offset)
    nb.Label(frame, text="", pady=10).grid()
    

    import massacre.integrations.main
    massacre.integrations.main.notify_about_settings(frame)
    
    
    nb.Label(frame, text="Made by CMDR WDX \nFixby CMDR CKX").grid(sticky=tk.W, padx=checkbox_offset)
    HyperlinkLabel(frame, text="Github", background=nb.Label().cget("background"), url=download_url, underline=True)\
        .grid(columnspan=2, sticky=tk.W, padx=checkbox_offset)

    

    return frame
