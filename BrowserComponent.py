from ableton.v3.control_surface.component import Component
from ableton.v3.control_surface.display import Renderable
from ableton.v3.control_surface.controls import (
    StepEncoderControl,
    ButtonControl,
    control_list
)
from ableton.v3.base import depends, listenable_property

from .Logger import logger

class BrowserComponent(Component, Renderable):
    select_encoder = StepEncoderControl(num_steps = 64)
    load_button = ButtonControl(color = None)
    shift_button = ButtonControl(color = None)
    enter_folder_button = ButtonControl(color = None)
    leave_folder_button = ButtonControl(color = None)
    select_folder_buttons = control_list(ButtonControl, color = None)

    _selected_item = None
    _parent_folder = None

    @listenable_property
    def selected_item(self):
        return self._selected_item
    
    @selected_item.setter
    def selected_item(self, item):
        self._selected_item = item

    @listenable_property
    def parent_folder(self):
        return self._parent_folder
    
    @parent_folder.setter
    def parent_folder(self, folder):
        self._parent_folder = folder

    def __init__(self, name = "Browser", *a, **k):
        super().__init__(name, *a, **k)
        browser = self.application.browser
        for folder in browser.colors:
            logger.info(f"folder = {folder}")
            if len(folder.children) > 0:
                for item in folder.children:
                    logger.info(f"name = {item.name}, chilren = {item.children}, is_device = {item.is_device}, is_folder = {item.is_folder}, is_loadable = {item.is_loadable}, uri = {item.uri}")

    @select_encoder.value
    def _on_select_encoder_value(self, value, encoder):
        pass