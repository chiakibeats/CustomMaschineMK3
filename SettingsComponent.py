from ableton.v3.control_surface.component import Component
from ableton.v3.control_surface.controls import (
    ButtonControl,
    control_matrix
)
from ableton.v3.base import depends

from .Logger import logger

class SettingsComponent(Component):
    select_button = ButtonControl()
    settings_matrix = control_matrix(ButtonControl)

    def __init__(self, name = "Settings", *a, **k):
        super().__init__(name, *a, **k)