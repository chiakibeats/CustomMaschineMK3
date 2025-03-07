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
from ableton.v3.control_surface.controls import ButtonControl
from ableton.v3.control_surface.mode import pop_last_mode
from ableton.v3.base import listens

from .Logger import logger

class EncoderModeControlComponent(Component):
    volume_button = ButtonControl(color = "DefaultButton.Off", on_color = "DefaultButton.On")
    swing_button = ButtonControl(color = "DefaultButton.Off", on_color = "DefaultButton.On")
    tempo_button = ButtonControl(color = "DefaultButton.Off", on_color = "DefaultButton.On")
    shift_button = ButtonControl(color = None)

    volume_modes = ("volume",)
    swing_modes = ("swing", "position")
    tempo_modes = ("tempo", "scale")

    _encoder_modes = None
    _buttons_and_knobs_modes = None
    _last_selected_mode = None

    def __init__(self, name = "Encoder_Mode_Control", *a, **k):
        super().__init__(name, *a, **k)

    @volume_button.pressed
    def _on_volume_button_pressed(self, button):
        self._handle_mode_button_pressed(self.volume_modes)

    @swing_button.pressed
    def _on_swing_button_pressed(self, button):
        self._handle_mode_button_pressed(self.swing_modes)

    @tempo_button.pressed
    def _on_tempo_button_pressed(self, button):
        self._handle_mode_button_pressed(self.tempo_modes)

    def _handle_mode_button_pressed(self, modes):
        if self._encoder_modes == None:
            return
        
        selected_mode = self._encoder_modes.selected_mode
        # In browser mode, encoder mode buttons do nothing to avoid confusing 
        if selected_mode != "browser":
            shift = self.shift_button.is_pressed
            if len(modes) > 1:
                # If a mode button has two modes and press mode button with shift when non-shift mode is selected, don't return to default
                do_return = (selected_mode == modes[0] and not shift) or selected_mode == modes[1]
            else:
                do_return = selected_mode == modes[0]
        
            if do_return:
                self._encoder_modes.push_mode(self._encoder_modes.modes[0])
                self._encoder_modes.pop_unselected_modes()
            else:
                # Otherwise push mode chosen by shift button state
                self._encoder_modes.push_mode(modes[1 if self.shift_button.is_pressed and len(modes) > 1 else 0])

        self._update_led_feedback()

    def set_encoder_modes(self, modes):
        self._encoder_modes = modes

    def set_buttons_and_knobs_modes(self, modes):
        self._buttons_and_knobs_modes = modes
        self._on_buttons_and_knobs_mode_changed.subject = modes
        if modes != None:
            self._on_buttons_and_knobs_mode_changed(modes)

    @listens("selected_mode")
    def _on_buttons_and_knobs_mode_changed(self, component):
        new_selected_mode = self._buttons_and_knobs_modes.selected_mode
        if self._last_selected_mode != "browser" and new_selected_mode == "browser":
            # Push "browser" mode to encoder modes stack
            if self._encoder_modes != None:
                self._encoder_modes.push_mode("browser")
        elif self._last_selected_mode == "browser" and new_selected_mode != "browser":
            if self._encoder_modes != None:
                pop_last_mode(self._encoder_modes, "browser")

        self._last_selected_mode = new_selected_mode
        self._update_led_feedback()

    def _update_led_feedback(self):
        mode = self._encoder_modes.selected_mode if self._encoder_modes != None else ""
        self.volume_button.is_on = mode in self.volume_modes
        self.swing_button.is_on = mode in self.swing_modes
        self.tempo_button.is_on = mode in self.tempo_modes

    def update(self):
        super().update()
        self._update_led_feedback()
