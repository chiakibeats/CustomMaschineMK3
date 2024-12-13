from ableton.v3.control_surface.elements import SysexElement
from .Logger import logger

# relay sysex button message to normal button

class SysexShiftButton(SysexElement):
    def __init__(self, target_button, *a, **k):
        super().__init__(*a, **k)
        self._target_button = target_button
        self._last_receive_value = None

    @property
    def target_button(self):
        return self._target_button
    
    @target_button.setter
    def target_button(self, value):
        self._target_button = value
        self._last_receive_value = None

    def receive_value(self, value):
        super().receive_value(value)
        value = value[0]
        logger.info(f"Shift = {value}")
        self._last_receive_value = value

        if self.target_button:
            self.target_button.receive_value(value)
