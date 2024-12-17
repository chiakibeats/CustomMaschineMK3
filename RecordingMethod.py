from ableton.v3.control_surface.component import Component
from ableton.v3.control_surface.components import RecordingMethod, ViewBasedRecordingComponent
from ableton.v3.control_surface.controls import ButtonControl, FixedRadioButtonGroup
from ableton.v3.control_surface.display import Renderable

# Record length in beats
RECORD_LENGTH_LIST = [
    1.0,
    2.0,
    4.0,
    8.0,
    16.0,
    32.0,
    64.0,
    128.0
]

DEFAULT_LENGTH_INDEX = 3

class FixedLengthRecordingMethod(RecordingMethod):
    _record_length = RECORD_LENGTH_LIST[DEFAULT_LENGTH_INDEX]
    _fixed_length_enabled = False

    def trigger_recording(self):
        if not self.stop_recording():
            self.start_recording()

    def start_recording(self, *_):
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
    fixed_button = ButtonControl(color = "RecordLength.FixedOff", on_color = "RecordLength.FixedOn")
    length_select_buttons = FixedRadioButtonGroup(
        unchecked_color = "RecordLength.Length",
        checked_color = "RecordLength.LengthSelected",
        control_count = len(RECORD_LENGTH_LIST))

    _record_length = RECORD_LENGTH_LIST[DEFAULT_LENGTH_INDEX]

    def __init__(self, name = "View_Based_Recording", *a, **k):
        super().__init__(name, *a, **k)
        self.length_select_buttons.checked_index = DEFAULT_LENGTH_INDEX

    @length_select_buttons.checked
    def _on_length_select_buttons_checked(self, button):
        self._record_length = RECORD_LENGTH_LIST[button.index]
        self._recording_method.set_record_length(self._record_length)

    @fixed_button.value
    def _on_fixed_button_value_changed(self, value, button):
        self._recording_method.set_fixed_length_enabled(value)
