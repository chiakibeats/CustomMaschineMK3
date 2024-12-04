from functools import partial
from ableton.v2.base import nop
from ableton.v2.control_surface import WrappingParameter, EnumWrappingParameter, IntegerParameter
from ableton.v3.control_surface import ParameterInfo
from ableton.v3.control_surface.component import Component
from ableton.v3.control_surface.components.device import DEFAULT_BANK_SIZE
from ableton.v3.control_surface.controls import (
    ButtonControl,
    MappedButtonControl,
    MappedSensitivitySettingControl,
    control_list
)
from ableton.v3.base import depends, listens, listenable_property, EventObject
from ableton.v3.live.util import liveobj_valid

from Live.Clip import ( # type: ignore
    ClipLaunchQuantization,
    LaunchMode,
    WarpMode,
    WarpMarker
)

from .Logger import logger

class ClipLaunchQuantizationList():
    values = [
        ClipLaunchQuantization.q_global,
        ClipLaunchQuantization.q_none,
        ClipLaunchQuantization.q_8_bars,
        ClipLaunchQuantization.q_4_bars,
        ClipLaunchQuantization.q_2_bars,
        ClipLaunchQuantization.q_bar,
        ClipLaunchQuantization.q_half,
        ClipLaunchQuantization.q_half_triplet,
        ClipLaunchQuantization.q_quarter,
        ClipLaunchQuantization.q_quarter_triplet,
        ClipLaunchQuantization.q_eighth,
        ClipLaunchQuantization.q_eighth_triplet,
        ClipLaunchQuantization.q_sixteenth,
        ClipLaunchQuantization.q_sixteenth_triplet,
        ClipLaunchQuantization.q_thirtysecond,
    ]

    value_strings = [
        "Global",
        "None",
        "8 Bars",
        "4 Bars",
        "2 Bars",
        "1 Bar",
        "1/2",
        "1/2T",
        "1/4",
        "1/4T",
        "1/8",
        "1/8T",
        "1/16",
        "1/16T",
        "1/32",
    ]

    @staticmethod
    def to_string(value):
        index = ClipLaunchQuantizationList.values.index(value)
        return ClipLaunchQuantizationList.value_strings[index]

class LaunchModeList():
    values = [
        LaunchMode.trigger,
        LaunchMode.gate,
        LaunchMode.toggle,
        LaunchMode.repeat,
    ]

    value_strings = [
        "Trigger",
        "Gate",
        "Toggle",
        "Repeat",
    ]

    @staticmethod
    def to_string(value):
        index = LaunchModeList.values.index(value)
        return LaunchModeList.value_strings[index]

class WarpModeList():
    values = [
        WarpMode.beats,
        WarpMode.tones,
        WarpMode.texture,
        WarpMode.repitch,
        WarpMode.complex,
        WarpMode.rex,
        WarpMode.complex_pro,
    ]

    value_strings = [
        "Beats",
        "Tones",
        "Texture",
        "Re-Pitch",
        "Complex",
        "Rex",
        "Pro",
    ]

    @staticmethod
    def to_string(value):
        index = WarpModeList.values.index(value)
        return WarpModeList.value_strings[index]

def bool_to_display_value(value, off_value, on_value):
    return on_value if value else off_value

bool_on_off = partial(bool_to_display_value, off_value = "Off", on_value = "On")

class BoolWrappingParameter(WrappingParameter):
    is_enabled = True
    is_quantized = True

    def __init__(self,
        property_host,
        source_property,
        display_value_conversion,
        invert = False, *a, **k):
        super().__init__(
            property_host,
            source_property,
            self._from_bool_invert if invert else self._from_bool,
            self._to_bool_invert if invert else self._to_bool,
            display_value_conversion,
            [], *a, **k)
        self._parent = property_host

    def _to_bool(self, value, parent):
        return bool(value)
    
    def _from_bool(self, value, parent):
        return int(value)
    
    def _to_bool_invert(self, value, parent):
        return not bool(value)
    
    def _from_bool_invert(self, value, parent):
        return int(not value)

    @property
    def min(self):
        return 0

    @property
    def max(self):
        return 1
    
# Max clip length is 1 year in 120BPM (taken from Push 2)
MAX_CLIP_LENGTH = 365 * 24 * 3600 * 2.0
    
class BeatOrTimeWrappingParameter(WrappingParameter):
    min = -MAX_CLIP_LENGTH
    max = MAX_CLIP_LENGTH

    def __init__(self, property_host, source_property, display_value_conversion, *a, **k):
        super().__init__(
            property_host = property_host,
            source_property = source_property,
            display_value_conversion = display_value_conversion, *a, **k)
        self._parent = property_host

    @listens("signature_denominator")
    def _on_denominator_changed(self):
        pass

    @listens("signature_numerator")
    def _on_numerator_changed(self):
        pass

    @listens("warping")
    def _on_warping_changed(self):
        pass

    
def make_index_value_converter(values):
    def to_index(x):
        return values[x]
    
    def from_index(x):
        for index, value in enumerate(values):
            if x == value:
                return index
        return 0
        
    return to_index, from_index

def make_bool_wrapper(name, converter = None, invert = False, *a, **k):
    return lambda obj: BoolWrappingParameter(
        property_host = obj,
        source_property = name,
        display_value_conversion = converter,
        invert = invert,
        parent = obj, *a, **k)

def make_enum_wrapper(name, values_name, values_host = None, make_converter = False, *a, **k):
    def make_wrapper(obj):
        to_index, from_index = make_index_value_converter(getattr(values_host or obj, values_name)) if make_converter else (None, None)
        return EnumWrappingParameter(
            parent = obj,
            index_property_host = obj,
            index_property = name,
            values_host = values_host or obj,
            values_property = values_name,
            value_type = int,
            to_index_conversion = to_index,
            from_index_conversion = from_index, *a, **k)
    
    return make_wrapper

def make_int_wrapper(name, min, max, *a, **k):
    return lambda obj: IntegerParameter(
        integer_value_host = obj,
        integer_value_property_name = name,
        min_value = min,
        max_value = max,
        show_as_quantized = True, *a, **k)

def make_beat_or_time_wrapper(name, converter = nop):
    def make_wrapper(obj):
        return BeatOrTimeWrappingParameter(obj, name, converter)
    
    return make_wrapper

TEST_CLIP_BUTTON_MAPPINGS = [
    make_bool_wrapper("muted", bool_on_off, True),
    make_bool_wrapper("looping", bool_on_off),
    None,
    make_bool_wrapper("legato", bool_on_off),
    None,
    None,
    None,
    None,
]


AUDIO_CLIP_BUTTON_MAPPINGS = [
    make_bool_wrapper("muted", bool_on_off, True),
    make_bool_wrapper("looping", bool_on_off),
    None,
    make_enum_wrapper("launch_mode", "values", LaunchModeList),
    make_bool_wrapper("legato", bool_on_off),
    make_bool_wrapper("warping", bool_on_off),
    make_bool_wrapper("ram_mode", bool_on_off),
    None,
    None,
]

TEST_CLIP_ENCODER_MAPPINGS = [
    make_beat_or_time_wrapper("position"),
    make_beat_or_time_wrapper("loop_start"),
    make_beat_or_time_wrapper("loop_end"),
    make_enum_wrapper("launch_quantization", "values", ClipLaunchQuantizationList),
    make_int_wrapper("pitch_coarse", -48, 48),
    make_int_wrapper("pitch_fine", -50, 50),
    make_enum_wrapper("warp_mode", "available_warp_modes", None, True),
    None,
]

AUDIO_CLIP_ENCODER_MAPPINGS = [
    "start_marker",
    "end_marker",
    "loop_start",
    "loop_end",
    "launch_mode",
    "launch_quantization",
    "pitch_coarse",
    "warp_mode",

    "signature_numerator",
    "signature_denominator",
    "gain",
    "pitch_fine",
    None,
    None,
    None,
    None,
]

MIDI_CLIP_BUTTON_MAPPINGS = [
    make_bool_wrapper("muted", bool_on_off, True),
    make_bool_wrapper("looping", bool_on_off),
    None,
    make_enum_wrapper("launch_mode", "values", LaunchModeList),
    make_bool_wrapper("legato", bool_on_off),
    None,
    None,
    None,
]
MIDI_CLIP_ENCODER_MAPPINGS = [
    "start_marker",
    "end_marker",
    "loop_start",
    "loop_end",
    "launch_mode",
    "launch_quantization",
    None,
    None,

    "signature_numerator",
    "signature_denominator",
    None,
    None,
    None,
    None,
    None,
    None,
]

class ClipWrapper(EventObject):
    _clip = None
    _loop_length = 0.0

    @property
    def clip(self):
        return self._clip
    
    @clip.setter
    def clip(self, new_clip):
        self._clip = new_clip

    @listenable_property
    def loop_length(self):
        return self._loop_length
    
    @loop_length.setter
    def loop_length(self, value):
        self._loop_length = value
        self._clip.loop_end = self._clip.loop_start + self._loop_length
    




class ClipEditorComponent(Component):
    bank_size = DEFAULT_BANK_SIZE
    control_buttons = control_list(MappedButtonControl, control_count = bank_size, color = "DefaultButton.Off", on_color = "DefaultButton.On")
    control_encoders = control_list(MappedSensitivitySettingControl, control_count = bank_size)

    _target_track = None

    @depends(target_track = None)
    def __init__(self, name = "ClipEditor", target_track = None, *a, **k):
        super().__init__(name, *a, **k)
        self._target_track = target_track
        self._on_target_track_changed.subject = self._target_track
        self._on_target_clip_changed.subject = self._target_track
        self._on_target_track_changed()
        self._on_target_clip_changed()

    @listens("target_track")
    def _on_target_track_changed(self):
        pass

    @listens("target_clip")
    def _on_target_clip_changed(self):
        self._map_clip_parameters()
    
    def _map_clip_parameters(self):
        clip = self._target_track.target_clip
        if liveobj_valid(clip):
            if clip.is_audio_clip:
                #logger.info(f"Warp modes = {[mode for mode in clip.available_warp_modes]}")
                self._map_parameters_to_control(clip, self.control_buttons, AUDIO_CLIP_BUTTON_MAPPINGS)
                self._map_parameters_to_control(clip, self.control_encoders, TEST_CLIP_ENCODER_MAPPINGS)
            else:
                self._map_parameters_to_control(clip, self.control_buttons, MIDI_CLIP_BUTTON_MAPPINGS)
                #self._map_parameters_to_control(clip, self.control_encoders, MIDI_CLIP_ENCODER_MAPPINGS)
            self._dump_clip(clip)
        else:
            self._map_parameters_to_control(clip, self.control_buttons, [None] * self.bank_size)
            self._map_parameters_to_control(clip, self.control_encoders, [None] * self.bank_size)
    
    def _map_parameters_to_control(self, liveobj, controls, mappings):
        for control in controls:
            wrapper_factory = mappings[control.index]
            if wrapper_factory != None:
                control.mapped_parameter = wrapper_factory(liveobj)
            else:
                control.mapped_parameter = None

    def _dump_clip(self, clip):
        for attr in dir(clip):
            if not attr.startswith("__"):
                try:
                    value = getattr(clip, attr)
                    if not callable(value):
                            logger.info(f"clip.{attr} = {value}, type = {type(value)}")
                    if type(value) is not str and hasattr(value, "__iter__"):
                        for index, item in enumerate(value):
                            if type(item) is WarpMarker:
                                logger.info(f"clip.{attr}[{index}]: beat_time = {item.beat_time}, sample_time = {item.sample_time}")
                            else:
                                logger.info(f"clip.{attr}[{index}] = {item}, type = {type(item)}")
                except Exception as ex:
                    logger.error(f"Exception ex = {ex}")
