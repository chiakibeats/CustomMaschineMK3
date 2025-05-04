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
    _display_modes = None
    _selected_encoder_mode = None

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
        if selected_mode != "browser" and selected_mode != "settings":
            shift = self.shift_button.is_pressed
            if len(modes) > 1:
                # If a mode button has two modes and press mode button with shift when non-shift mode is selected, don't return to default
                do_return = (selected_mode == modes[0] and not shift) or selected_mode == modes[1]
            else:
                do_return = selected_mode == modes[0]
        
            if do_return:
                display_mode = self._display_modes.selected_mode
                if display_mode == "device":
                    self._encoder_modes.selected_mode = "device"
                else:
                    self._encoder_modes.selected_mode = "default"
                self._selected_encoder_mode = None
            else:
                # Otherwise push mode chosen by shift button state
                self._selected_encoder_mode = modes[1 if self.shift_button.is_pressed and len(modes) > 1 else 0]
                self._encoder_modes.selected_mode = self._selected_encoder_mode
                
        self._update_led_feedback()

    def set_encoder_modes(self, modes):
        self._encoder_modes = modes

    def set_display_modes(self, modes):
        self._display_modes = modes
        self._on_display_mode_changed.subject = modes
        if modes != None:
            self._on_display_mode_changed(modes)

    @listens("selected_mode")
    def _on_display_mode_changed(self, component):
        display_mode = self._display_modes.selected_mode
        if display_mode == "browser":
            self._encoder_modes.selected_mode = "browser"
        elif display_mode == "settings":
            self._encoder_modes.selected_mode = "settings"
        else:
            if self._selected_encoder_mode != None:
                self._encoder_modes.selected_mode = self._selected_encoder_mode
            elif display_mode == "device":
                self._encoder_modes.selected_mode = "device"
            else:
                self._encoder_modes.selected_mode = "default"

        self._update_led_feedback()

    def _update_led_feedback(self):
        mode = self._encoder_modes.selected_mode if self._encoder_modes != None else ""
        self.volume_button.is_on = mode in self.volume_modes
        self.swing_button.is_on = mode in self.swing_modes
        self.tempo_button.is_on = mode in self.tempo_modes

    def update(self):
        super().update()
        self._update_led_feedback()
