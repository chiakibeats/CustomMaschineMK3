from ableton.v3.control_surface.component import Component
from ableton.v3.control_surface.display import Renderable
from ableton.v3.control_surface.controls import (
    StepEncoderControl,
    ButtonControl,
    control_list
)
from ableton.v3.base import clamp, depends, listenable_property

from .Logger import logger

class BrowserComponent(Component, Renderable):
    select_encoder = StepEncoderControl(num_steps = 64)
    load_button = ButtonControl(color = None)
    shift_button = ButtonControl(color = None)
    enter_folder_button = ButtonControl(color = None)
    leave_folder_button = ButtonControl(color = None)
    select_folder_buttons = control_list(ButtonControl, color = None)

    _selected_item_index = 0
    _parent_folder = None
    _folder_items = []

    @listenable_property
    def selected_item(self):
        if len(self.parent_folder.children) > 0:
            return self.parent_folder.children[self._selected_item_index]
        else:
            return None
    
    @listenable_property
    def parent_folder(self):
        return self._parent_folder
    
    @parent_folder.setter
    def parent_folder(self, folder):
        self._parent_folder = folder
        self.notify_parent_folder()

    def __init__(self, name = "Browser", *a, **k):
        super().__init__(name, *a, **k)
        browser = self.application.browser
        self.parent_folder = browser.colors[0]
        for folder in browser.colors:
            logger.info(f"folder = {folder}")
            if len(folder.children) > 0:
                for item in folder.children:
                    logger.info(f"name = {item.name}, children = {item.children}, is_device = {item.is_device}, is_folder = {item.is_folder}, is_loadable = {item.is_loadable}, uri = {item.uri}")

    def reset_iter_state(self):
        self._selected_item_index = 0
        self.notify_selected_item()

    @select_encoder.value
    def _on_select_encoder_value(self, value, encoder):
        new_index = self._selected_item_index + value
        new_index = clamp(new_index, 0, len(self.parent_folder.children))
        self._selected_item_index = new_index
        self.notify_selected_item()
        logger.info(f"Select item {self.selected_item.name if self.selected_item else None}")

    @load_button.pressed
    def _on_load_button_pressed(self, button):
        if self.selected_item != None:
            logger.info(f"Load item {self.selected_item.name}")
            self.application.browser.load_item(self.selected_item)

    @select_folder_buttons.pressed
    def _on_folder_buttons_pressed(self, button):
        self.parent_folder = self.application.browser.colors[button.index]
        logger.info(f"Select folder {self.parent_folder.name}")
        self.reset_iter_state()

        