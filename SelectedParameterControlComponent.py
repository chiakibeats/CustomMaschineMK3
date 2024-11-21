from ableton.v3.control_surface.component import Component
from ableton.v3.control_surface.controls import (
    ButtonControl,
    MappedControl,
    control_list
)

from ableton.v3.control_surface import (
    DEFAULT_BANK_SIZE,
    ScriptForwarding
)

from ableton.v3.base import depends
from ableton.v3.live import liveobj_valid

from .Logger import logger

class SelectedParameterControlComponent(Component):
    select_buttons = control_list(ButtonControl, control_count = DEFAULT_BANK_SIZE)
    modulation_encoder = MappedControl()

    _get_knob_mapped_parameter = None

    @depends(get_knob_mapped_parameter = None)
    def __init__(self, name = "SelectedParameter", get_knob_mapped_parameter = None, *a, **k):
        super().__init__(name, *a, **k)
        self._get_knob_mapped_parameter = get_knob_mapped_parameter

    @select_buttons.pressed
    def _on_select_buttons_pressed(self, button):
        parameter = self._get_knob_mapped_parameter(button.index)
        logger.info(f"Parameter select {parameter}")
        if liveobj_valid(parameter):
            logger.info(f"Parameter name = {parameter.name}")
        self.modulation_encoder.mapped_parameter = parameter

    