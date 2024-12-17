from itertools import product
from re import L
from ableton.v3.base import listens, listenable_property
from ableton.v3.live.util import find_parent_track, liveobj_valid
from ableton.v3.control_surface import DEFAULT_BANK_SIZE, use
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
from ableton.v3.control_surface.default_bank_definitions import (
    BANK_DEFINITIONS,
    BANK_MAIN_KEY,
    BANK_PARAMETERS_KEY
)
from ableton.v3.control_surface.parameter_mapping_sensitivities import (
    DEFAULT_CONTINUOUS_PARAMETER_SENSITIVITY,
    DEFAULT_QUANTIZED_PARAMETER_SENSITIVITY
)
from ableton.v3.control_surface.device_decorators import (
    DeviceDecoratorFactory,
    TransmuteDeviceDecorator,
    DriftDeviceDecorator,
    RoarDeviceDecorator
)
from ableton.v2.control_surface import (
    DelayDeviceDecorator,
    SimplerDeviceDecorator,
    WavetableDeviceDecorator
)

from .Logger import logger

# Device decorator is extender for device object
# Usually wrap special parameters (wavetable index, simpler playback mode, etc.) for using them like normal device parameters
# Wavetable device decorator is removed from v3 decorator factory (reason is unknown), so I put all decorators into this class
class CustomDeviceDecoratorFactory(DeviceDecoratorFactory):
    DECORATOR_CLASSES = {
     'Delay': DelayDeviceDecorator, 
     'Drift': DriftDeviceDecorator, 
     'OriginalSimpler': SimplerDeviceDecorator, 
     'Roar': RoarDeviceDecorator, 
     'Transmute': TransmuteDeviceDecorator,
     'InstrumentVector': WavetableDeviceDecorator}

CUSTOM_BANK_DEFINITIONS = BANK_DEFINITIONS.copy()
CUSTOM_BANK_DEFINITIONS["InstrumentVector"]["Oscillator 1"] = {
    BANK_PARAMETERS_KEY: (
        'Osc 1 Category',
        'Osc 1 Table',
        'Osc 1 Pitch',
        'Osc 1 Pos',
        'Osc 1 Effect 1',
        'Osc 1 Effect 2',
        'Osc 1 Gain',
        'Osc 1 On'
    )
}

CUSTOM_BANK_DEFINITIONS["InstrumentVector"]["Oscillator 2"] = {
    BANK_PARAMETERS_KEY: (
        'Osc 2 Category',
        'Osc 2 Table',
        'Osc 2 Pitch',
        'Osc 2 Pos',
        'Osc 2 Effect 1',
        'Osc 2 Effect 2',
        'Osc 2 Gain',
        'Osc 2 On'
    )
}

# You can switch bank parameter depends on certain condition by using mini language, also parameter name can be modified. 
# Simpler custom bank definition is a long spaghetti...
CUSTOM_BANK_DEFINITIONS["OriginalSimpler"][BANK_MAIN_KEY] = {
    BANK_PARAMETERS_KEY: (
        "Mode",
        use("Start").if_parameter("Mode").has_value("Classic")
            .else_use("Trigger Mode").with_name("Trigger").if_parameter("Mode").has_value_in(("One-Shot", "Slicing")),
        use("End").if_parameter("Mode").has_value("Classic")
            .else_use("Snap").if_parameter("Mode").has_value("One-Shot")
            .else_use("Slice by").with_name("Slice Mode").if_parameter("Mode").has_value("Slicing"),
        use("S Loop Length").with_name("Loop Length").if_parameter("Mode").has_value("Classic")
            .else_use("").if_parameter("Mode").has_value("One-Shot")
            .else_use("Sensitivity").if_parameter("Mode").has_value("Slicing").and_parameter("Slice by").has_value("Transient")
            .else_use("Division").if_parameter("Mode").has_value("Slicing").and_parameter("Slice by").has_value("Beat")
            .else_use("Regions").if_parameter("Mode").has_value("Slicing").and_parameter("Slice by").has_value("Region")
            .else_use("").if_parameter("Mode").has_value("Slicing").and_parameter("Slice by").has_value("Manual"),
        use("S Loop On").with_name("Loop").if_parameter("Mode").has_value("Classic")
            .else_use("").if_parameter("Mode").has_value("One-Shot")
            .else_use("Playback").if_parameter("Mode").has_value("Slicing"),
        use("Voices").if_parameter("Mode").has_value_in(("Classic", "Slicing")),
        "Warp",
        "Warp Mode"
    )
}

class CustomDeviceComponent(DeviceComponent):
    _parameter_touch_controls = control_list(ButtonControl, DEFAULT_BANK_SIZE)
    erase_button = ButtonControl(color = None)
    _current_touched_index = -1
    
    def __init__(self, name = "Device", *a, **k):
        super().__init__(name, *a, **k)

    def set_parameter_touch_controls(self, controls):
        self._parameter_touch_controls.set_control_element(controls)
        
    @_parameter_touch_controls.pressed
    def _on_parameter_touch_pressed(self, button):
        if self._current_touched_index == -1:
            self._current_touched_index = button.index
            touched_parameter = self.parameters[button.index]

            if touched_parameter is not None:
                name = touched_parameter.name
                self._show_message(f"Knob {button.index + 1} Parameter Name: {name}")
    
    @_parameter_touch_controls.released
    def _on_parameter_touch_released(self, button):
        if button == self._parameter_touch_controls[self._current_touched_index]:
            self._current_touched_index = -1

    @_parameter_touch_controls.double_clicked
    def _on_parameter_touch_double_clicked(self, button):
        if self.erase_button.is_pressed:
            if button.index < len(self.parameters):
                parameter = self.parameters[button.index].parameter
                if liveobj_valid(parameter) and not parameter.is_quantized:
                    parameter.value = parameter.default_value
