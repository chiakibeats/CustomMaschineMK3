from ableton.v3.control_surface.component import Component
from ableton.v3.control_surface.controls import (
    ButtonControl,
    SendValueEncoderControl,
    control_list
)
from ableton.v3.base import depends

from .Logger import logger

def beat_ratio(denominator):
    return 4.0 / denominator

REPEAT_RATES = [
    beat_ratio(32),
    beat_ratio(24),
    beat_ratio(16),
    beat_ratio(12),
    beat_ratio(8),
    beat_ratio(6),
    beat_ratio(4),
    beat_ratio(3)
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
class NoteRepeatComponent(Component):
    repeat_button = ButtonControl(color = "DefaultButton.Off", on_color = "DefaultButton.On")
    rate_selector = CustomSendValueEncoderControl()

    _note_repeat = None
    _enabled = False

    @depends(note_repeat = None)
    def __init__(self, name = "NoteRepeat", note_repeat = None, *a, **k):
        super().__init__(name, *a, **k)
        self._note_repeat = note_repeat
        self._note_repeat.enabled = self._enabled

    @repeat_button.pressed
    def _on_repeat_button_pressed(self, button):
        self._enabled = not self._enabled
        self._note_repeat.enabled = self._enabled
        self.repeat_button.is_on = self._enabled

    @rate_selector.value
    def _on_rate_selector_changed(self, value, button):
        logger.info(f"Rate selector = {value}")
        index_value = int(value) >> 11
        self._note_repeat.repeat_rate = REPEAT_RATES[min(len(REPEAT_RATES) - 1, index_value)]
        self.rate_selector.value = (index_value << 11) + (index_value << 8) + (index_value << 5) + (index_value << 2)

    def update(self):
        super().update()
