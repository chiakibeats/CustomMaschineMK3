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

from .logger import logger

# TODO: Change class name to more intuitive one.
class SelectedParameterControlComponent(Component, Renderable):
    """
    Device parameter control with Maschine's touch strip.

    Select one parameter from device chain view or mixer view, and control it with touch strip.
    """
    select_buttons = control_list(ButtonControl, control_count = DEFAULT_BANK_SIZE, color = None)
    """Target parameter select buttons."""
    select_modifier = ButtonControl(color = None, delay_time = 0.6)
    """Modifier button for activating `select_buttons`."""
    reset_value_button = ButtonControl(color = None)
    """Reset parameter value to default button."""
    modulation_encoder = MappedControl()
    """Touchstrip for controlling parameter."""

    _get_knob_mapped_parameter = None
    _show_message = None

    @depends(get_knob_mapped_parameter = None, show_message = None)
    def __init__(self, name = "Selected_Parameter", get_knob_mapped_parameter = None, show_message = None, *a, **k):
        """
        Args:
            name(str):
                Component name. This should keep default.
            get_knob_mapped_parameter:
                Function that is used for retrieve device parameter from button index.
                DI container will supply actual value.
            show_message:
                Function to show up message at the bottom of the Live window.
                DI container will supply actual value.
        """
        super().__init__(name, *a, **k)
        self._get_knob_mapped_parameter = get_knob_mapped_parameter
        self._show_message = show_message

    def set_modulation_encoder(self, encoder):
        """
        Assign `EncoderElement` to `modulation_encoder`.

        This setter exists for showing notification when the component is activated.

        Args:
            encoder(EncoderElement): Element to assign.
        """
        self.modulation_encoder.set_control_element(encoder)
        if encoder != None:
            self._show_selected_parameter_message(self.modulation_encoder.mapped_parameter)

    @select_buttons.pressed
    def _on_select_buttons_pressed(self, button):
        """
        Map specific device parameter to touch strip.

        The target device parameter is determined by the index of `button`.
        For example, if you pressed button 3, touch strip connects to the device parameter connected to 3rd knob.

        Args:
            button(ButtonControl): Button control that is pressed.
        """
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
        """
        Get parameter name and its parent object name.

        Args:
            parameter(Live.DeviceParameter): Device parameter.
        
        Returns:
            tuple[str, str]:
                Name of parent object and `parameter` itself.
                If the parent object is `MixerDevice`, this function returns track name.
        """
        parent = parameter.canonical_parent
        if str.find(str(type(parent)), "MixerDevice") > 0:
            return (parent.canonical_parent.name, parameter.name)
        else:
            return (parent.name, parameter.name)
