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
from ableton.v3.control_surface.controls import (
    ButtonControl,
    SendValueEncoderControl,
    control_matrix
)
from ableton.v3.control_surface.display import Renderable
from ableton.v3.base import depends

from .Logger import logger

def beat_ratio(denominator):
    return 4.0 / denominator

# Upper group buttons mapped to normal repeat rates
# Lower group buttons mapped to triplet repeat rates 
REPEAT_RATES = [
    (beat_ratio(4), "1/4"),
    (beat_ratio(8), "1/8"),
    (beat_ratio(16), "1/16"),
    (beat_ratio(32), "1/32"),
    (beat_ratio(6), "1/4T"),
    (beat_ratio(12), "1/8T"),
    (beat_ratio(24), "1/16T"),
    (beat_ratio(48), "1/32T"),
]

class CustomSendValueEncoderControl(SendValueEncoderControl):
    class State(SendValueEncoderControl.State):
        def _notify_encoder_value(self, value, *a, **k):
            normalized_value = value
            self._call_listener("value", normalized_value)
            self.connected_property_value = normalized_value

        def set_control_element(self, control_element):
            super().set_control_element(control_element)
            if control_element != None:
                self.control_element.send_value(self.value, True)

# Note repeat fuction works via note_repeat object inside c_instance (special object comes from ableton live app)
# This object has 2 property, "enabled" and "repeat_rate"
# enabled: Enable or disable note repeat function, type is boolean
# repeat_rate: Interval of repetition, type is float, 1.0 means 1/4 synced length in ableton
class NoteRepeatComponent(Component, Renderable):
    repeat_button = ButtonControl(color = "NoteRepeat.Off", on_color = "NoteRepeat.On")
    lock_button = ButtonControl(color = "NoteRepeat.LockOff", on_color = "NoteRepeat.LockOn")
    rate_select_mode_button = ButtonControl(color = "DefaultButton.Off", on_color = "DefaultButton.On")
    rate_select_buttons = control_matrix(ButtonControl, color = "NoteRepeat.Rate", on_color = "NoteRepeat.RateSelected")

    _note_repeat = None
    _enabled = False
    _selected_index = 0
    _lock_enabled = False

    @depends(note_repeat = None)
    def __init__(self, name = "Note_Repeat", note_repeat = None, *a, **k):
        super().__init__(name, *a, **k)
        self._note_repeat = note_repeat
        self.update()

    @repeat_button.pressed
    def _on_repeat_button_pressed(self, button):
        if not self._enabled:
            self._enabled = True
        else:
            self._lock_enabled = False
            self._enabled = False
        self._update_note_repeat_state()
        self._update_led_feedback()

    @repeat_button.released
    def _on_repeat_button_released(self, button):
        if not self._lock_enabled:
            self._enabled = False
            self._update_note_repeat_state()
        self._update_led_feedback()
        
    @lock_button.pressed
    def _on_lock_button_pressed(self, button):
        if self._enabled:
            self._lock_enabled = True
        self._update_led_feedback()

    @rate_select_mode_button.pressed
    def _on_rate_select_mode_button_pressed(self, button):
        self.rate_select_mode_button.is_on = True

    @rate_select_mode_button.released
    def _on_rate_select_mode_button_released(self, button):
        self.rate_select_mode_button.is_on = False

    @rate_select_buttons.pressed
    def _on_rate_selector_changed(self, button):
        row, column = button.coordinate
        index = min(row * self.rate_select_buttons.width + column, len(REPEAT_RATES) - 1)
        rate = REPEAT_RATES[index]
        self._note_repeat.repeat_rate = rate[0]
        self._selected_index = index
        self._update_led_feedback()
        self.notify(self.notifications.NoteRepeat.repeat_rate, rate[1])

    def _update_led_feedback(self):
        self.repeat_button.is_on = self._enabled
        self.lock_button.is_on = self._lock_enabled

        for button in self.rate_select_buttons:
            row, column = button.coordinate
            index = row * self.rate_select_buttons.width + column
            button.is_on = index == self._selected_index

    def _update_note_repeat_state(self):
        self._note_repeat.enabled = self._enabled

    def update(self):
        super().update()
        self._note_repeat.enabled = self._enabled
        self._note_repeat.repeat_rate = REPEAT_RATES[self._selected_index][0]
        self._update_led_feedback()
