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
from ableton.v3.control_surface.components import RecordingMethod, ViewBasedRecordingComponent
from ableton.v3.control_surface.controls import ButtonControl, RadioButtonGroup
from ableton.v3.control_surface.display import Renderable

# Record length in beats
RECORD_LENGTH_LIST = [
    (1.0, "1 Beat"),
    (2.0, "2 Beats"),
    (4.0, "1 Bar"),
    (8.0, "2 Bars"),
    (16.0, "4 Bars"),
    (32.0, "8 Bars"),
    (64.0, "16 Bars"),
    (128.0, "32 Bars"),
]
"""Length choices of fixed length recording."""

DEFAULT_LENGTH_INDEX = 3

class FixedLengthRecordingMethod(RecordingMethod):
    """
    Custom recording procedure in the session view.

    This class enables fixed length recording in the session view.
    """
    _record_length = RECORD_LENGTH_LIST[DEFAULT_LENGTH_INDEX][0]
    _fixed_length_enabled = False

    def trigger_recording(self):
        """
        Handle trigger event of the record button.
        """
        if not self.stop_recording():
            self.start_recording()

    def start_recording(self, *_):
        """
        Start recording normally, or trigger fixed recording.

        Variable length argument `*_` seems to be unused.
        """
        if self._fixed_length_enabled:
            selected_slot = self.song.view.highlighted_clip_slot
            if self.can_record_into_clip_slot(selected_slot):
                if selected_slot.clip == None:
                    selected_slot.fire(self._record_length)
                else:
                    super().start_recording()
        else:
            super().start_recording(*_)
    
    def set_record_length(self, length):
        self._record_length = length

    def set_fixed_length_enabled(self, enabled):
        self._fixed_length_enabled = enabled

class CustomViewBasedRecordingComponent(ViewBasedRecordingComponent):
    """
    View-based recording operations.

    The original `RecordingComponent` has dedicated record and overdub button for both session and arrangement view.
    The meaning of view-based is it automatically changes button assignment depends on current view.

    Custom version has controls for fixed length recording that are intended to use with `FixedLengthRecordingMethod`.
    """
    fixed_button = ButtonControl(color = "RecordLength.FixedOff", on_color = "RecordLength.FixedOn")
    length_select_buttons = RadioButtonGroup(
        unchecked_color = "RecordLength.Length",
        checked_color = "RecordLength.LengthSelected",
        control_count = len(RECORD_LENGTH_LIST))

    def __init__(self, name = "View_Based_Recording", *a, **k):
        super().__init__(name, *a, **k)
        self.length_select_buttons.checked_index = DEFAULT_LENGTH_INDEX

    @length_select_buttons.checked
    def _on_length_select_buttons_checked(self, button):
        self._recording_method.set_record_length(RECORD_LENGTH_LIST[button.index][0])

    @length_select_buttons.pressed
    def _on_length_select_buttons_pressed(self, button):
        self.notify(self.notifications.Recording.fixed_length, RECORD_LENGTH_LIST[button.index][1])

    @fixed_button.value
    def _on_fixed_button_value_changed(self, value, button):
        self._recording_method.set_fixed_length_enabled(value)
