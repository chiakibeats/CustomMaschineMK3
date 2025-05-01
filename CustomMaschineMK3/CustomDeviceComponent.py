# ==================================================
#
# This file is part of CustomMaschineMK3.
# CustomMaschineMK3 is free software licensed under GPL-3.0.
# For more details, see "LICENSE" file.
# 
# Copyright (C) 2024-2025 chiaki
#
# ==================================================

from ableton.v3.base import listens, listenable_property
from ableton.v2.base.collection import IndexedDict
from ableton.v3.live import find_parent_track, liveobj_valid
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
    DEFAULT_QUANTIZED_PARAMETER_SENSITIVITY,
    create_sensitivities,
    parameter_mapping_sensitivities,
)
import ableton.v3.control_surface.device_decorators as decorators
from ableton.v3.control_surface.device_decorators import (
    DeviceDecoratorFactory,
    DeviceDecorator,
    TransmuteDeviceDecorator,
    DriftDeviceDecorator
)
from ableton.v2.control_surface import (
    DelayDeviceDecorator,
    SimplerDeviceDecorator,
    WavetableDeviceDecorator,
    IntegerParameter
)

from .KnobTouchStateMixin import KnobTouchStateMixin
from .Logger import logger

class Eq8DeviceDecorator(DeviceDecorator):
    def create_additional_parameters(self):
        self._additional_parameters = []
        self._additional_parameters.append(IntegerParameter(
            name = "Band",
            parent = self,
            integer_value_host = self._live_object.view,
            integer_value_property_name = "selected_band",
            min_value = 0,
            max_value = 7,
            show_as_quantized = False,
            display_value_conversion = (lambda x: str(x + 1))))
    
    @property
    def parameters(self):
        return tuple(self._live_object.parameters) + tuple(self._additional_parameters)

# Device decorator is extender for device object
# Usually wrap special parameters (wavetable index, simpler playback mode, etc.) for using them like normal device parameters
# Wavetable device decorator is removed from v3 decorator factory (reason is unknown), so I put all decorators into this class
class CustomDeviceDecoratorFactory(DeviceDecoratorFactory):
    DECORATOR_CLASSES = {
        'Delay': DelayDeviceDecorator,
        'Drift': DriftDeviceDecorator,
        'Eq8': Eq8DeviceDecorator,
        'OriginalSimpler': SimplerDeviceDecorator,
        'Transmute': TransmuteDeviceDecorator,
        'InstrumentVector': WavetableDeviceDecorator
    }

CUSTOM_BANK_DEFINITIONS = BANK_DEFINITIONS.copy()
CUSTOM_BANK_DEFINITIONS["InstrumentVector"]["Oscillator 1"] = {
    BANK_PARAMETERS_KEY: (
        'Osc 1 Category',
        'Osc 1 Table',
        'Osc 1 Pos',
        'Osc 1 Pitch',
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
        'Osc 2 Pos',
        'Osc 2 Pitch',
        'Osc 2 Effect 1',
        'Osc 2 Effect 2',
        'Osc 2 Gain',
        'Osc 2 On'
    )
}

# You can switch bank parameter depends on certain condition by using mini language, also parameter name can be modified. 
# Simpler custom bank definition is a long spaghetti...
CUSTOM_BANK_DEFINITIONS["OriginalSimpler"] = IndexedDict((
    (
        BANK_MAIN_KEY,
        {BANK_PARAMETERS_KEY: (
            use("Ve Attack").if_parameter("Multi Sample").has_value("On")
                .else_use("Mode"),
            use("Ve Decay").if_parameter("Multi Sample").has_value("On")
                .else_use("Start"),
            use("Ve Sustain").if_parameter("Multi Sample").has_value("On")
                .else_use("End"),
            use("Ve Release").if_parameter("Multi Sample").has_value("On")
                .else_use("Fade In").if_parameter("Mode").has_value("One-Shot")
                .else_use("Nudge").if_parameter("Mode").has_value("Slicing")
                .else_use("S Start").if_parameter("Mode").has_value("Classic"),
            use("Pan").if_parameter("Multi Sample").has_value("On")
                .else_use("Fade Out").if_parameter("Mode").has_value("One-Shot")
                .else_use("Playback").if_parameter("Mode").has_value("Slicing")
                .else_use("S Length").if_parameter("Mode").has_value("Classic"),
            use("Transpose").if_parameter("Multi Sample").has_value("On")
                .else_use("Transpose").if_parameter("Mode").has_value("One-Shot")
                .else_use("Slice by").if_parameter("Mode").has_value("Slicing")
                .else_use("S Loop Length").if_parameter("Mode").has_value("Classic"),
            use("Detune").if_parameter("Multi Sample").has_value("On")
                .else_use("Gain").if_parameter("Mode").has_value("One-Shot")
                .else_use("Sensitivity").if_parameter("Slice by").has_value("Transient")
                    .and_parameter("Mode").has_value("Slicing")
                .else_use("Division").if_parameter("Slice by").has_value("Beat")
                    .and_parameter("Mode").has_value("Slicing")
                .else_use("Regions").if_parameter("Slice by").has_value("Region")
                    .and_parameter("Mode").has_value("Slicing")
                .else_use("Pad Slicing").if_parameter("Slice by").has_value("Manual")
                    .and_parameter("Mode").has_value("Slicing")
                .else_use("Sensitivity").if_parameter("Mode").has_value("Slicing")
                .else_use("S Loop Fade").if_parameter("Mode").has_value("Classic")
                    .and_parameter("Warp").has_value("Off")
                .else_use("Detune"),
            use("Volume"))}
    ),
    (
        "Filter",
        {BANK_PARAMETERS_KEY: (
            "F On",
            use("Filter Type").if_parameter("Filter Type").is_available(True)
                .else_use("Filter Type (Legacy)"),
            "Filter Freq",
            use("Filter Res").if_parameter("Filter Res").is_available(True)
                .else_use("Filter Res (Legacy)"),
            use("Filter Circuit - LP/HP").if_parameter("Filter Type").has_value("Lowpass")
                .else_use("Filter Circuit - LP/HP").if_parameter("Filter Type").has_value("Highpass")
                .else_use("Filter Circuit - BP/NO/Morph"),
            use("Filter Morph").if_parameter("Filter Type").has_value("Morph")
                .else_use("").if_parameter("Filter Type").has_value("Lowpass")
                    .and_parameter("Filter Circuit - LP/HP").has_value("Clean")
                .else_use("").if_parameter("Filter Type").has_value("Highpass")
                    .and_parameter("Filter Circuit - LP/HP").has_value("Clean")
                .else_use("").if_parameter("Filter Type").has_value("Bandpass")
                    .and_parameter("Filter Circuit - BP/NO/Morph").has_value("Clean")
                .else_use("").if_parameter("Filter Type").has_value("Notch")
                    .and_parameter("Filter Circuit - BP/NO/Morph").has_value("Clean")
                .else_use("Filter Drive"),
            "Filt < Vel",
            "Filt < LFO")}
    ),
    (
        "LFO",
        {BANK_PARAMETERS_KEY: (
            "L Wave",
            "L Sync",
            use("L Rate").if_parameter("L Sync").has_value("Free")
                .else_use("L Sync Rate"),
            "L Attack",
            "L R < Key",
            "Vol < LFO",
            "L Retrig",
            "L Offset")}
    ),
    (
        "Global",
        {BANK_PARAMETERS_KEY: (
            "Glide Mode",
            "Glide Time",
            use("").if_parameter("Mode").has_value("One-Shot")
                .else_use("Voices").if_parameter("Mode").has_value("Classic")
                .else_use("Voices").if_parameter("Mode").has_value("Slicing")
                    .and_parameter("Playback").has_value("Poly"),
            "Transpose",
            "Detune",
            "Vol < Vel",
            'Pan',
            'Spread')}
    ),
    (
        "Amplitude",
        {BANK_PARAMETERS_KEY: (
            use("Ve Attack").if_parameter("Mode").has_value("Classic")
                .else_use("Fade In"),
            use("Ve Decay").if_parameter("Mode").has_value("Classic")
                .else_use("Fade Out"),
            use("Ve Sustain").if_parameter("Mode").has_value("Classic")
                .else_use("Volume"),
            use("Ve Release").if_parameter("Mode").has_value("Classic"),
            use("Ve Mode"),
            use("Ve Retrig").if_parameter("Ve Mode").has_value("Beat")
                    .or_parameter("Ve Mode").has_value("Sync")
                .else_use("Ve Loop").if_parameter("Ve Mode").has_value("Loop"),
            'Pan < Rnd',
            'Pan < LFO')}
    ),
    (
        "Filter Envelope",
        {BANK_PARAMETERS_KEY: (
            "Fe On",
            "Fe Attack",
            "Fe Decay",
            "Fe Sustain",
            "Fe Release",
            "Fe < Env",
            "",
            "")}
    ),
    (
        "Pitch Modifiers",
        {BANK_PARAMETERS_KEY: (
            use("Pe On"),
            use("Pe Attack"),
            use("Pe Decay"),
            use("Pe Sustain"),
            use("Pe Release"),
            use("Pe < Env"),
            "Pe < LFO",
            'PB Range')}
    ),
    (
        "Sample & Warp",
        {BANK_PARAMETERS_KEY: (
            use("").if_parameter("Multi Sample").has_value("On")
                .else_use("Gain"),
            use("").if_parameter("Multi Sample").has_value("On")
                .else_use("Start"),
            use("").if_parameter("Multi Sample").has_value("On")
                .else_use("End"),
            use("").if_parameter("Multi Sample").has_value("On")
                .else_use("Warp"),
            use("").if_parameter("Multi Sample").has_value("On")
                .else_use("").if_parameter("Warp").has_value("Off")
                .else_use("Warp Mode"),
            use("").if_parameter("Multi Sample").has_value("On")
                .else_use("").if_parameter("Warp").has_value("Off")
                .else_use("Preserve").if_parameter("Warp Mode").has_value("Beats")
                .else_use("Grain Size Tones").if_parameter("Warp Mode").has_value("Tones")
                .else_use("Grain Size Texture").if_parameter("Warp Mode").has_value("Texture")
                .else_use("Formants").if_parameter("Warp Mode").has_value("Pro"),
            use("").if_parameter("Multi Sample").has_value("On")
                .else_use("").if_parameter("Warp").has_value("Off")
                .else_use("Loop Mode").if_parameter("Warp Mode").has_value("Beats")
                .else_use("Flux").if_parameter("Warp Mode").has_value("Texture")
                .else_use("Envelope Complex Pro").if_parameter("Warp Mode").has_value("Pro"),
            use("").if_parameter("Multi Sample").has_value("On")
                .else_use("").if_parameter("Warp").has_value("Off")
                .else_use("Envelope").if_parameter("Warp Mode").has_value("Beats"))}
    ),
))

CUSTOM_BANK_DEFINITIONS["Eq8"][BANK_MAIN_KEY] = {
    BANK_PARAMETERS_KEY: (
        'Band',
        use("1 Filter On A").if_parameter("Band").has_value("1")
            .else_use("2 Filter On A").if_parameter("Band").has_value("2")
            .else_use("3 Filter On A").if_parameter("Band").has_value("3")
            .else_use("4 Filter On A").if_parameter("Band").has_value("4")
            .else_use("5 Filter On A").if_parameter("Band").has_value("5")
            .else_use("6 Filter On A").if_parameter("Band").has_value("6")
            .else_use("7 Filter On A").if_parameter("Band").has_value("7")
            .else_use("8 Filter On A").if_parameter("Band").has_value("8"),
        use("1 Filter Type A").if_parameter("Band").has_value("1")
            .else_use("2 Filter Type A").if_parameter("Band").has_value("2")
            .else_use("3 Filter Type A").if_parameter("Band").has_value("3")
            .else_use("4 Filter Type A").if_parameter("Band").has_value("4")
            .else_use("5 Filter Type A").if_parameter("Band").has_value("5")
            .else_use("6 Filter Type A").if_parameter("Band").has_value("6")
            .else_use("7 Filter Type A").if_parameter("Band").has_value("7")
            .else_use("8 Filter Type A").if_parameter("Band").has_value("8"),
        use("1 Frequency A").if_parameter("Band").has_value("1")
            .else_use("2 Frequency A").if_parameter("Band").has_value("2")
            .else_use("3 Frequency A").if_parameter("Band").has_value("3")
            .else_use("4 Frequency A").if_parameter("Band").has_value("4")
            .else_use("5 Frequency A").if_parameter("Band").has_value("5")
            .else_use("6 Frequency A").if_parameter("Band").has_value("6")
            .else_use("7 Frequency A").if_parameter("Band").has_value("7")
            .else_use("8 Frequency A").if_parameter("Band").has_value("8"),
        use("1 Resonance A").if_parameter("Band").has_value("1")
            .else_use("2 Resonance A").if_parameter("Band").has_value("2")
            .else_use("3 Resonance A").if_parameter("Band").has_value("3")
            .else_use("4 Resonance A").if_parameter("Band").has_value("4")
            .else_use("5 Resonance A").if_parameter("Band").has_value("5")
            .else_use("6 Resonance A").if_parameter("Band").has_value("6")
            .else_use("7 Resonance A").if_parameter("Band").has_value("7")
            .else_use("8 Resonance A").if_parameter("Band").has_value("8"),
        use("1 Gain A").if_parameter("Band").has_value("1")
            .else_use("2 Gain A").if_parameter("Band").has_value("2")
            .else_use("3 Gain A").if_parameter("Band").has_value("3")
            .else_use("4 Gain A").if_parameter("Band").has_value("4")
            .else_use("5 Gain A").if_parameter("Band").has_value("5")
            .else_use("6 Gain A").if_parameter("Band").has_value("6")
            .else_use("7 Gain A").if_parameter("Band").has_value("7")
            .else_use("8 Gain A").if_parameter("Band").has_value("8"),
        "Scale",
        "Output Gain"
    )
}

def custom_mapping_sensitivities(original):
    def inner(parameter, device):
        default = original(parameter, device)
        if liveobj_valid(parameter):
            if device.class_name == "OriginalSimpler" and parameter.name == "Mode":
                default = tuple(x * 6 for x in default)
        
        return default
    
    return inner

class CustomDeviceComponent(DeviceComponent):
    knob_touch_buttons = control_list(ButtonControl, color = None)
    erase_button = ButtonControl(color = None)
    
    def __init__(self, name = "Device", *a, **k):
        if self.application.get_major_version() == 12:
            CustomDeviceDecoratorFactory.DECORATOR_CLASSES['Roar'] = decorators.RoarDeviceDecorator

        super().__init__(name, *a, **k)
        self._parameter_mapping_sensitivities = custom_mapping_sensitivities(self._parameter_mapping_sensitivities)
        self.register_slot(self, self.notify_current_parameters, "parameters")

    @listenable_property
    def current_parameters(self):
        return self._provided_parameters

    @knob_touch_buttons.double_clicked
    def _on_knob_touch_double_clicked(self, button):
        if self.erase_button.is_pressed:
            if button.index < len(self.parameters):
                parameter = self.parameters[button.index].parameter
                if liveobj_valid(parameter) and not parameter.is_quantized:
                    parameter.value = parameter.default_value
