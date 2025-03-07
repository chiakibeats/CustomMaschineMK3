# ==================================================
#
# This file is part of CustomMaschineMK3.
# CustomMaschineMK3 is free software licensed under GPL-3.0.
# For more details, see "LICENSE" file.
# 
# Copyright (C) 2024-2025 chiaki
#
# ==================================================

from ableton.v3.control_surface.component import Component
from ableton.v3.control_surface.display import Renderable
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

class SelectedParameterControlComponent(Component, Renderable):
    select_buttons = control_list(ButtonControl, control_count = DEFAULT_BANK_SIZE, color = None)
    select_modifier = ButtonControl(color = None, delay_time = 0.6)
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
        logger.info(f"Parameter select {parameter.name if liveobj_valid(parameter) else None}")
        self._show_selected_parameter_message(parameter)
        self.modulation_encoder.mapped_parameter = parameter

    @select_modifier.pressed_delayed
    def _on_select_modifier_pressed_delayed(self, _):
        for button in self.select_buttons:
            button.color = "DefaultButton.On"

    @select_modifier.released
    def _on_select_modifier_released(self, _):
        for button in self.select_buttons:
            button.color = None

    @reset_value_button.pressed
    def _on_value_reset_button_pressed(self, button):
        parameter = self.modulation_encoder.mapped_parameter
        if liveobj_valid(parameter) and not parameter.is_quantized:
            parameter.value = parameter.default_value

    def _show_selected_parameter_message(self, parameter):
        if liveobj_valid(parameter):
            self.notify(self.notifications.SelectedParameterControl.select, *self._get_parameter_path(parameter))
        else:
            self.notify(self.notifications.SelectedParameterControl.select, "", "---")

    def _get_parameter_path(self, parameter):
        parent = parameter.canonical_parent
        if str.find(str(type(parent)), "MixerDevice") > 0:
            return (parent.canonical_parent.name, parameter.name)
        else:
            return (parent.name, parameter.name)
