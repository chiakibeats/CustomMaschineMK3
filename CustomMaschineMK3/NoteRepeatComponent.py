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
    control_list
)
from ableton.v3.control_surface.display import Renderable
from ableton.v3.base import (
    depends,
    listens
)

from .SettingsComponent import get_repeat_rate_value
from .Logger import logger

# def beat_ratio(denominator):
#     return 4.0 / denominator

# Upper group buttons mapped to normal repeat rates
# Lower group buttons mapped to triplet repeat rates 
# REPEAT_RATES = [
#     (beat_ratio(4), "1/4"),
#     (beat_ratio(8), "1/8"),
#     (beat_ratio(16), "1/16"),
#     (beat_ratio(32), "1/32"),
#     (beat_ratio(6), "1/4T"),
#     (beat_ratio(12), "1/8T"),
#     (beat_ratio(24), "1/16T"),
#     (beat_ratio(48), "1/32T"),
# ]

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
    rate_select_buttons = control_list(ButtonControl, color = "NoteRepeat.Rate", on_color = "NoteRepeat.RateSelected", control_count = 8)

    _note_repeat = None
    _settings = None
    _enabled = False
    _selected_index = 0
    _lock_enabled = False
    _group_button_control = None

    @depends(note_repeat = None, settings = None)
    def __init__(self, name = "Note_Repeat", note_repeat = None, settings = None, *a, **k):
        super().__init__(name, *a, **k)
        self._note_repeat = note_repeat
        self._settings = settings
        self._automatic_switching = False
        self._repeat_rates = [(1.0, "")] * self.rate_select_buttons.control_count
        self._on_settings_changed.subject = self._settings
        self._on_settings_changed()
        self.update()

    def set_group_button_control(self, control):
        self._group_button_control = control

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

    @rate_select_buttons.pressed
    def _on_rate_selector_changed(self, button):
        self._note_repeat.repeat_rate = self._repeat_rates[button.index][0]
        self._selected_index = button.index
        self._update_led_feedback()
        self.notify(self.notifications.NoteRepeat.repeat_rate, self._repeat_rates[button.index][1])

    def _update_led_feedback(self):
        self.repeat_button.is_on = self._enabled
        self.lock_button.is_on = self._lock_enabled

        for button in self.rate_select_buttons:
            index = button.index
            button.is_on = index == self._selected_index

    def _update_note_repeat_state(self):
        logger.info(f"Note repeat state = {self._enabled}")
        if self._automatic_switching and self._group_button_control != None:
            self._group_button_control.set_note_repeat_selector_state(self._enabled)

        self._note_repeat.enabled = self._enabled

    def update(self):
        super().update()
        self._note_repeat.enabled = self._enabled
        self._note_repeat.repeat_rate = self._repeat_rates[self._selected_index][0]
        self._update_led_feedback()

    @listens("value_changed")
    def _on_settings_changed(self):
        self._update_settings()

    def _update_settings(self):
        self._automatic_switching = self._settings.get_value("automatic_selector_switching")
        for index in range(self.rate_select_buttons.control_count):
            name = self._settings.get_value("repeat_rate_" + chr(ord('a') + index))
            value = get_repeat_rate_value(name)
            self._repeat_rates[index] = (value, name)
