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
    reset_value_button = ButtonControl(color = None)
    modulation_encoder = MappedControl()

    _get_knob_mapped_parameter = None
    _show_message = None

    @depends(get_knob_mapped_parameter = None, show_message = None)
    def __init__(self, name = "Selected_Parameter", get_knob_mapped_parameter = None, show_message = None, *a, **k):
        super().__init__(name, *a, **k)
        self._get_knob_mapped_parameter = get_knob_mapped_parameter
        self._show_message = show_message

    def set_modulation_encoder(self, encoder):
        self.modulation_encoder.set_control_element(encoder)
        if encoder != None:
            self._show_selected_parameter_message(self.modulation_encoder.mapped_parameter)

    @select_buttons.pressed
    def _on_select_buttons_pressed(self, button):
        parameter = self._get_knob_mapped_parameter(button.index)
        logger.info(f"Parameter select {parameter}")
        if liveobj_valid(parameter):
            logger.info(f"Parameter name = {parameter.name}")
        self._show_selected_parameter_message(parameter)
        self.modulation_encoder.mapped_parameter = parameter

    @reset_value_button.pressed
    def _on_value_reset_button_pressed(self, button):
        parameter = self.modulation_encoder.mapped_parameter
        if liveobj_valid(parameter) and not parameter.is_quantized:
            parameter.value = parameter.default_value

    def _show_selected_parameter_message(self, parameter):
        if parameter != None:
            self._show_message(f"Touch Strip Parameter: {self._get_parameter_path(parameter)}")
        else:
            self._show_message(f"Touch Strip Parameter: None")

    def _get_parameter_path(self, parameter):
        parent = parameter.canonical_parent
        if str.find(str(type(parent)), "MixerDevice") > 0:
            return f"{parent.canonical_parent.name} > {parameter.name}"
        else:
            return f"{parent.name} > {parameter.name}"


    