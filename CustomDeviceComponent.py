from itertools import product
from ableton.v3.control_surface.components import (
    DeviceComponent,
    DeviceBankNavigationComponent,
    ScrollComponent,
    Scrollable
)

from ableton.v3.control_surface.controls import (
    ButtonControl,
    EncoderControl,
    TouchControl,
    MappedControl,
    SendValueInputControl,
    SendValueEncoderControl,
    control_matrix,
    control_list
)

from ableton.v2.control_surface.control import (
    MatrixControl
)

from ableton.v2.control_surface import (
    WrappingParameter
)

from ableton.v3.control_surface import (
    DEFAULT_BANK_SIZE,
    ScriptForwarding
)

from ableton.v3.base import (
    listens,
    listenable_property,
)

from ableton.v3.live.util import find_parent_track, liveobj_valid

from ableton.v3.control_surface.parameter_mapping_sensitivities import DEFAULT_CONTINUOUS_PARAMETER_SENSITIVITY, DEFAULT_QUANTIZED_PARAMETER_SENSITIVITY

from .Logger import logger


class CustomDeviceComponent(DeviceComponent):
    _parameter_touch_controls = control_list(ButtonControl, DEFAULT_BANK_SIZE)
    _current_touched_index = -1
    
    def __init__(self, name="Device", *a, **k):
        super().__init__(name, *a, **k)

    def set_parameter_touch_controls(self, controls):
        self._parameter_touch_controls.set_control_element(controls)
        
    @_parameter_touch_controls.pressed
    def _on_parameter_touch_pressed(self, button):
        if self._current_touched_index == -1:
            for x in range(DEFAULT_BANK_SIZE):
                if self._parameter_touch_controls[x] == button:
                    self._current_touched_index = x
                    touched_parameter = self.parameters[x]

                    if touched_parameter is not None:
                        name = touched_parameter.name
                        self._show_message(f"Knob {x + 1} Parameter Name: {name}")

                    break
    
    @_parameter_touch_controls.released
    def _on_parameter_touch_released(self, button):
        if button == self._parameter_touch_controls[self._current_touched_index]:
            self._current_touched_index = -1