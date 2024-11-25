from functools import partial
from re import S
from ableton.v2.base import nop
from ableton.v2.control_surface import WrappingParameter, EnumWrappingParameter
from ableton.v3.control_surface.component import Component
from ableton.v3.control_surface.components.device import DEFAULT_BANK_SIZE
from ableton.v3.control_surface.controls import (
    ButtonControl,
    MappedButtonControl,
    MappedSensitivitySettingControl,
    control_list
)
from ableton.v3.base import depends, listens
from ableton.v3.live.util import liveobj_valid

from .Logger import logger

def bool_to_display_value(value, off_value, on_value):
    return on_value if value else off_value

bool_on_off = partial(bool_to_display_value, off_value = "Off", on_value = "On")

class BoolWrappingParameter(WrappingParameter):
    is_enabled = True
    is_quantized = True

    def __init__(self,
        property_host = None,
        source_property = None,
        display_value_conversion = None,
        invert = False, *a, **k):
        super().__init__(
            property_host,
            source_property,
            self._from_bool_invert if invert else self._from_bool,
            self._to_bool_invert if invert else self._to_bool,
            display_value_conversion,
            [], *a, **k)

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

def make_bool_wrapper(name, converter = None, invert = False, *a, **k):
    return lambda obj: BoolWrappingParameter(
        property_host = obj,
        source_property = name,
        display_value_conversion = converter,
        invert = invert,
        parent = obj, *a, **k)

def make_enum_wrapper(name):
    return lambda obj: EnumWrappingParameter(
        parent = obj,
        index_property_host = obj,
        index_property = name,
        values_host = None,
        values_property = None,
        value_type = int,

        
    )

TEST_CLIP_BUTTON_MAPPINGS = [
    make_bool_wrapper("muted", bool_on_off, True),
    make_bool_wrapper("looping", bool_on_off),
    make_bool_wrapper("legato", bool_on_off),
    None,
    None,
    None,
    None,
    None,
]


AUDIO_CLIP_BUTTON_MAPPINGS = [
    make_bool_wrapper("muted", bool_on_off, True),
    make_bool_wrapper("looping", bool_on_off),
    make_bool_wrapper("legato", bool_on_off),
    make_bool_wrapper("ram_mode", bool_on_off),
    None,
    None,
    None,
    make_bool_wrapper("warping", bool_on_off),
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
    make_bool_wrapper("legato", bool_on_off),
    None,
    None,
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
    "pitch_coarse",
    "warp_mode",

    "signature_numerator",
    "signature_denominator",
    None,
    None,
    None,
    None,
    None,
    None,
]

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
                self._map_parameters_to_control(clip, self.control_buttons, AUDIO_CLIP_BUTTON_MAPPINGS)
                #self._map_parameters_to_control(clip, self.control_encoders, AUDIO_CLIP_ENCODER_MAPPINGS)
            else:
                self._map_parameters_to_control(clip, self.control_buttons, MIDI_CLIP_BUTTON_MAPPINGS)
                #self._map_parameters_to_control(clip, self.control_encoders, MIDI_CLIP_ENCODER_MAPPINGS)
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
