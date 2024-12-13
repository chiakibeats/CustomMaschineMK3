from functools import partial
from ableton.v3.base import clamp, depends, listens, nop, sign, listenable_property, EventObject
from ableton.v2.control_surface import WrappingParameter, EnumWrappingParameter, IntegerParameter
from ableton.v3.control_surface import ParameterInfo
from ableton.v3.control_surface.component import Component
from ableton.v3.control_surface.components.device import DEFAULT_BANK_SIZE
from ableton.v3.control_surface.controls import (
    ButtonControl,
    EncoderControl,
    MappedButtonControl,
    MappedSensitivitySettingControl,
    control_list
)
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

    short_value_strings = [
        "Trig",
        "Gate",
        "Tgle",
        "Rept",
    ]

    @staticmethod
    def to_string(value):
        index = LaunchModeList.values.index(value)
        return LaunchModeList.value_strings[index]

    @staticmethod
    def to_short_string(value):
        index = LaunchModeList.values.index(value)
        return LaunchModeList.short_value_strings[index]

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

    def set_property_host(self, new_host):
        super().set_property_host(new_host)
        self._parent = new_host
        self.notify_value()

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
    
class CustomEnumWrappingParameter(EnumWrappingParameter):
    def __init__(self,
        index_property_host = None,
        values_host = None,
        values_property = None,
        index_property = None,
        value_type = int,
        to_index_conversion = None,
        from_index_conversion = None, *a, **k):
        super().__init__(
            index_property_host,
            index_property_host,
            values_host,
            values_property,
            index_property,
            value_type,
            to_index_conversion,
            from_index_conversion, *a, **k)

    def set_property_host(self, new_host):
        super().set_property_host(new_host)
        self._parent = new_host
        self.notify_value()
    
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

class CustomValueStepper():
    _step_count = 0
    _step_value = 0.0

    def __init__(self, step_count = 64):
        self._step_count = step_count

    @property
    def step_count(self):
        return self._step_count
    
    @step_count.setter
    def step_count(self, value):
        self._step_count = value

    def update(self, value):
        if sign(value) != sign(self._step_value):
            self.reset()

        new_step_value = self._step_value + value * self._step_count
        if int(new_step_value) != int(self._step_value):
            self.reset()
            return int(new_step_value)
        else:
            self._step_value = new_step_value

        return 0
    
    def reset(self):
        self._step_value = 0.0

class EncoderCallbackSet:
    value_changed = None
    touched = None
    released = None

    def __init__(self, value_changed = nop, touched = nop, released = nop):
        self.value_changed = value_changed
        self.touched = touched
        self.released = released

class ClipEditorComponent(Component):
    bank_size = DEFAULT_BANK_SIZE

    mute_button = MappedButtonControl(color = "DefaultButton.Off", on_color = "DefaultButton.On")
    loop_button = MappedButtonControl(color = "DefaultButton.Off", on_color = "DefaultButton.On")
    crop_button = ButtonControl(color = "DefaultButton.Off", pressed_color = "DefaultButton.On")
    launch_mode_button = MappedButtonControl(color = "DefaultButton.Off", on_color = "DefaultButton.On")
    legato_button = MappedButtonControl(color = "DefaultButton.Off", on_color = "DefaultButton.On")
    warp_button = MappedButtonControl(color = "DefaultButton.Off", on_color = "DefaultButton.On")
    ram_mode_button = MappedButtonControl(color = "DefaultButton.Off", on_color = "DefaultButton.On")

    fine_grain_button = ButtonControl(color = None)
    control_encoders = control_list(EncoderControl, control_count = bank_size)
    encoder_touch_buttons = control_list(ButtonControl, control_count = bank_size, color = None)

    _mute_parameter = None
    _loop_parameter = None
    _launch_mode_parameter = None
    _legato_parameter = None
    _warp_parameter = None
    _warp_mode_parameter = None
    _ram_mode_parameter = None

    _position_value_stepper = CustomValueStepper(8)
    _loop_start_value_stepper = CustomValueStepper(8)
    _loop_end_value_stepper = CustomValueStepper(8)
    _start_marker_value_stepper = CustomValueStepper(8)
    _launch_quantization_value_stepper = CustomValueStepper(4)
    _pitch_value_stepper = CustomValueStepper(8)
    _warp_mode_value_stepper = CustomValueStepper(4)
    _gain_value_stepper = CustomValueStepper(64)

    _nudge_offset_value_stepper = CustomValueStepper(32)
    _note_length_value_stepper = CustomValueStepper(32)
    _note_pitch_value_stepper = CustomValueStepper(16)
    _note_velocity_value_stepper = CustomValueStepper(32)

    _target_track = None
    _clip = None
    _step_sequence = None

    _empty_encoder_callbacks = [EncoderCallbackSet()] * bank_size

    _looped_audio_clip_encoder_callbacks = None
    _nonlooped_audio_clip_encoder_callbacks = None

    _looped_midi_clip_encoder_callbacks = None
    _nonlooped_midi_clip_encoder_callbacks = None

    _encoder_callbacks = _empty_encoder_callbacks

    @depends(target_track = None)
    def __init__(self, name = "Clip_Editor", target_track = None, *a, **k):
        super().__init__(name, *a, **k)
        self._target_track = target_track

        self._mute_parameter = BoolWrappingParameter(None, "muted", bool_on_off, True)
        self._loop_parameter = BoolWrappingParameter(None, "looping", bool_on_off)
        self._launch_mode_parameter = CustomEnumWrappingParameter(None, LaunchModeList, "values", "launch_mode")
        self._legato_parameter = BoolWrappingParameter(None, "legato", bool_on_off)
        self._warp_parameter = BoolWrappingParameter(None, "warping", bool_on_off)
        self._warp_mode_parameter = CustomEnumWrappingParameter(None, self, "available_warp_modes", "warp_mode", int, self._to_warp_mode, self._from_warp_mode)
        self._ram_mode_parameter = BoolWrappingParameter(None, "ram_mode", bool_on_off)

        self.mute_button.mapped_parameter = self._mute_parameter
        self.loop_button.mapped_parameter = self._loop_parameter
        self.launch_mode_button.mapped_parameter = self._launch_mode_parameter
        self.legato_button.mapped_parameter = self._legato_parameter
        self.warp_button.mapped_parameter = self._warp_parameter
        self.ram_mode_button.mapped_parameter = self._ram_mode_parameter

        self._on_target_track_changed.subject = self._target_track
        self._on_target_clip_changed.subject = self._target_track
        self._on_target_track_changed()
        self._on_target_clip_changed()

        self._looped_audio_clip_encoder_callbacks = [
            EncoderCallbackSet(self._change_position),
            EncoderCallbackSet(self._change_loop_end),
            EncoderCallbackSet(self._change_start_marker),
            EncoderCallbackSet(self._change_launch_quantization),
            EncoderCallbackSet(self._change_warp_mode),
            EncoderCallbackSet(self._change_pitch),
            EncoderCallbackSet(self._change_gain),
            EncoderCallbackSet(),
        ]

        self._nonlooped_audio_clip_encoder_callbacks = [
            EncoderCallbackSet(self._change_loop_start),
            EncoderCallbackSet(self._change_loop_end),
            EncoderCallbackSet(),
            EncoderCallbackSet(self._change_launch_quantization),
            EncoderCallbackSet(self._change_warp_mode),
            EncoderCallbackSet(self._change_pitch),
            EncoderCallbackSet(self._change_gain),
            EncoderCallbackSet(),
        ]

        self._looped_midi_clip_encoder_callbacks = [
            EncoderCallbackSet(self._change_position),
            EncoderCallbackSet(self._change_loop_end),
            EncoderCallbackSet(self._change_start_marker),
            EncoderCallbackSet(self._change_launch_quantization),
            EncoderCallbackSet(self._change_note_nudge_offset),
            EncoderCallbackSet(self._change_note_length),
            EncoderCallbackSet(self._change_note_pitch),
            EncoderCallbackSet(self._change_note_velocity),
        ]

        self._nonlooped_midi_clip_encoder_callbacks = [
            EncoderCallbackSet(self._change_loop_start),
            EncoderCallbackSet(self._change_loop_end),
            EncoderCallbackSet(),
            EncoderCallbackSet(self._change_launch_quantization),
            EncoderCallbackSet(self._change_note_nudge_offset),
            EncoderCallbackSet(self._change_note_length),
            EncoderCallbackSet(self._change_note_pitch),
            EncoderCallbackSet(self._change_note_velocity),
        ]

    @listenable_property
    def available_warp_modes(self):
        return self._clip.available_warp_modes if liveobj_valid(self._clip) else []
    
    def _to_warp_mode(self, value):
        return self._clip.available_warp_modes[value]

    def _from_warp_mode(self, mode):
        for index, value in enumerate(self._clip.available_warp_modes):
            if value == mode:
                return index
        return 0
    
    def _get_one_bar_length(self):
        return self._clip.signature_numerator * (4.0 / self._clip.signature_denominator)
    
    def _get_one_beat_length(self):
        return 4.0 / self._clip.signature_denominator
    
    def set_step_sequence(self, step_sequence):
        self._step_sequence = step_sequence

    @crop_button.pressed
    def _on_crop_button_pressed(self, button):
        if liveobj_valid(self._clip):
            self._clip.crop()
    
    @control_encoders.value
    def _on_control_encoders_value_changed(self, value, encoder):
        callback_set = self._encoder_callbacks[encoder.index]
        callback_set.value_changed(value, encoder)

    @encoder_touch_buttons.pressed
    def _on_encoder_touch_buttons_pressed(self, button):
        callback_set = self._encoder_callbacks[button.index]
        callback_set.touched(button)

    @encoder_touch_buttons.released
    def _on_encoder_touch_buttons_released(self, button):
        callback_set = self._encoder_callbacks[button.index]
        callback_set.released(button)

    @listens("target_track")
    def _on_target_track_changed(self):
        pass

    @listens("target_clip")
    def _on_target_clip_changed(self):
        self._clip = self._target_track.target_clip
        self._map_clip_button_parameters()
        self._on_clip_looping_changed.subject = self._clip
        self._on_clip_looping_changed()
        self.notify_available_warp_modes()

    @listens("looping")
    def _on_clip_looping_changed(self):
        self._map_clip_encoder_parameters()

    def _map_clip_button_parameters(self):
        if liveobj_valid(self._clip):
            #self._dump_clip(self._clip)
            is_audio = self._clip.is_audio_clip

            self._mute_parameter.set_property_host(self._clip)
            self._loop_parameter.set_property_host(self._clip)
            self._launch_mode_parameter.set_property_host(self._clip)
            self._legato_parameter.set_property_host(self._clip)
            self._warp_parameter.set_property_host(self._clip if is_audio else None)
            self._warp_mode_parameter.set_property_host(self._clip if is_audio else None)
            self._ram_mode_parameter.set_property_host(self._clip if is_audio else None)
        else:
            self._mute_parameter.set_property_host(None)
            self._loop_parameter.set_property_host(None)
            self._launch_mode_parameter.set_property_host(None)
            self._legato_parameter.set_property_host(None)
            self._warp_parameter.set_property_host(None)
            self._warp_mode_parameter.set_property_host(None)
            self._ram_mode_parameter.set_property_host(None)
    
    def _map_clip_encoder_parameters(self):
        if liveobj_valid(self._clip):
            if self._clip.is_audio_clip:
                if self._clip.looping:
                    self._encoder_callbacks = self._looped_audio_clip_encoder_callbacks
                else:
                    self._encoder_callbacks = self._nonlooped_audio_clip_encoder_callbacks
            else:
                if self._clip.looping:
                    self._encoder_callbacks = self._looped_midi_clip_encoder_callbacks
                else:
                    self._encoder_callbacks = self._nonlooped_midi_clip_encoder_callbacks
        else:
            self._encoder_callbacks = self._empty_encoder_callbacks

    def _change_position(self, value, encoder):
        step = self._position_value_stepper.update(value)
        if step != 0:
            use_fine_grain = self.fine_grain_button.is_pressed
            if self._clip.is_midi_clip or self._clip.warping:
                self._clip.position += step * (self._get_one_beat_length() if use_fine_grain else self._get_one_bar_length())
            else:
                self._clip.position += step * (0.01 if use_fine_grain else 0.1)
            
            self._clip.view.show_loop()

    def _change_loop_start(self, value, encoder):
        step = self._loop_start_value_stepper.update(value)
        if step != 0:
            use_fine_grain = self.fine_grain_button.is_pressed
            if self._clip.is_midi_clip or self._clip.warping:
                self._clip.loop_start += step * (self._get_one_beat_length() if use_fine_grain else self._get_one_bar_length())
            else:
                self._clip.loop_start += step * (0.01 if use_fine_grain else 0.1)
            
            self._clip.view.show_loop()

    def _change_loop_end(self, value, encoder):
        step = self._loop_end_value_stepper.update(value)
        if step != 0:
            use_fine_grain = self.fine_grain_button.is_pressed
            if self._clip.is_midi_clip or self._clip.warping:
                self._clip.loop_end += step * (self._get_one_beat_length() if use_fine_grain else self._get_one_bar_length())
            else:
                self._clip.loop_end += step * (0.01 if use_fine_grain else 0.1)
            
            self._clip.view.show_loop()

    def _change_loop_length(self, value, encoder):
        length = self._clip.loop_end - self._clip.loop_start
        length += value
        length = max(length, 0.0)
        self._clip.loop_end = self._clip.loop_start + length
        self._clip.view.show_loop()

    def _change_start_marker(self, value, encoder):
        step = self._start_marker_value_stepper.update(value)
        if step != 0:
            use_fine_grain = self.fine_grain_button.is_pressed
            if self._clip.is_midi_clip or self._clip.warping:
                self._clip.start_marker += step * (self._get_one_beat_length() if use_fine_grain else self._get_one_bar_length())
            else:
                self._clip.start_marker += step * (0.01 if use_fine_grain else 0.1)

    def _change_launch_quantization(self, value, encoder):
        step = self._launch_quantization_value_stepper.update(value)
        if step != 0:
            new_value = self._clip.launch_quantization + step
            self._clip.launch_quantization = clamp(new_value, 0, len(ClipLaunchQuantizationList.values))

    def _change_pitch(self, value, encoder):
        step = self._pitch_value_stepper.update(value)
        if step != 0:
            if self.fine_grain_button.is_pressed:
                new_value = self._clip.pitch_fine + step
                self._clip.pitch_fine = clamp(new_value, -50, 50)
            else:
                new_value = self._clip.pitch_coarse + step
                self._clip.pitch_coarse = clamp(new_value, -48, 48)

    def _change_warp_mode(self, value, encoder):
        step = self._warp_mode_value_stepper.update(value)
        if step != 0:
            new_value = self._warp_mode_parameter.value + step
            min_value = self._warp_mode_parameter.min
            max_value = self._warp_mode_parameter.max
            self._warp_mode_parameter.value = clamp(new_value, min_value, max_value)

    def _change_gain(self, value, encoder):
        step = self._gain_value_stepper.update(value)
        if step != 0:
            use_fine_grain = self.fine_grain_button.is_pressed
            new_value = self._clip.gain + step * (0.001 if use_fine_grain else 0.005)
            self._clip.gain = clamp(new_value, 0.0, 1.0)

    def _change_note_nudge_offset(self, value, encoder):
        step = self._nudge_offset_value_stepper.update(value)
        if step != 0 and self._step_sequence != None:
            self._step_sequence.note_editor.set_nudge_offset(step / 128.0)

    def _change_note_length(self, value, encoder):
        step = self._note_length_value_stepper.update(value)
        if step != 0 and self._step_sequence != None:
            self._step_sequence.note_editor.set_duration_offset(step / 128.0)

    def _change_note_pitch(self, value, encoder):
        step = self._note_pitch_value_stepper.update(value)
        if step != 0 and self._step_sequence != None:
            self._step_sequence.note_editor.set_pitch_offset(step)

    def _change_note_velocity(self, value, encoder):
        step = self._note_velocity_value_stepper.update(value)
        if step != 0 and self._step_sequence != None:
            self._step_sequence.note_editor.set_velocity_offset(step)
    
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
