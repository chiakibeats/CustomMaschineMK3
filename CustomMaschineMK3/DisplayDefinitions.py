# ==================================================
#
# This file is part of CustomMaschineMK3.
# CustomMaschineMK3 is free software licensed under GPL-3.0.
# For more details, see "LICENSE" file.
# 
# Copyright (C) 2024-2025 chiaki
#
# ==================================================

from dataclasses import dataclass
from ableton.v2.control_surface import InternalParameterBase
from ableton.v3.control_surface.components.sliced_simpler import BASE_SLICING_NOTE
from ableton.v3.control_surface.display import DefaultNotifications, DisplaySpecification
from ableton.v3.control_surface.display.view import View, CompoundView, NotificationView
from ableton.v3.control_surface.display.text import adjust_string
from ableton.v3.control_surface.display.notifications.type_decl import Fn, Notification
from ableton.v3.live import liveobj_name, liveobj_valid, parameter_owner
from ableton.v3.base import pitch_index_to_string

from Live.DeviceParameter import DeviceParameter # type: ignore
from Live.Base import Timer # type: ignore

from .ClipEditorComponent import LaunchModeList, ClipLaunchQuantizationList, WarpModeList
from .Logger import logger

LCD_LINES = 4
LCD_LINE_LENGTH = 28
NO_ITEM = "---"
PITCH_NAMES = ["C", "C#/Db", "D", "D#/Db", "E", "F", "F#/Gb", "G", "G#/Ab", "A", "A#/Bb", "B"]

SESSION_RING = "default"
MASTER_VOLUME = "volume"
GROOVE_AMOUNT = "swing"
ARRANGE_POSITION = "position"
SONG_TEMPO = "tempo"
CLIP_SCALE = "scale"
ENCODER_MODES = (SESSION_RING, MASTER_VOLUME, GROOVE_AMOUNT, ARRANGE_POSITION, SONG_TEMPO, CLIP_SCALE)

TRACK_MIXER = "default"
DEVICE_CONTROL = "device"
CLIP_CONTROL = "clip"
BROWSER = "browser"

def make_mcu_display_header(line):
    return (0xF0, 0x00, 0x00, 0x66, 0x17, 0x12, 28 * min(line, LCD_LINES - 1))

def make_display_sysex_message(line, message):
    return make_mcu_display_header(line) + message + (0xF7,)

def try_get_attr(obj, attr, default = None):
    if obj != None:
        return getattr(obj, attr)
    else:
        return default
    
def adjust_gain_string(gain_string):
    if str.find(gain_string, "dB") != -1:
        gain_string = gain_string[:-3]
        if len(gain_string) > 6:
            gain_string = gain_string[:6]

    return gain_string

def get_display_value(parameter):
    if isinstance(parameter, InternalParameterBase):
        return parameter.display_value
    elif isinstance(parameter, DeviceParameter):
        return parameter.str_for_value(parameter.value)
    else:
        return ""

def to_pan_or_send_value(knob):
    if str.startswith(knob.parameter_name, "Pan"):
        return knob.parameter_value
    else:
        return adjust_gain_string(knob.parameter_value)

class Content:
    lines = [""] * 4

class TouchStates:
    def __init__(self, release_delay = 0.4, knob_count = 8):
        self._knob_count = knob_count
        self._knobs = [False] * self._knob_count
        self._encoder = False
        self._active_index = -1
        self._encoder_active = False
        self._delay_time = release_delay * 1000
        self._knob_timer = Timer(callback = self.delayed_knob_release, interval = int(self._delay_time), start = False)
        self._encoder_timer = Timer(callback = self.delayed_encoder_release, interval = int(self._delay_time), start = False)

    @property
    def active_index(self):
        return self._active_index
        
    @active_index.setter
    def active_index(self, value):
        self._active_index = value

    @property
    def encoder_active(self):
        return self._encoder_active

    @encoder_active.setter
    def encoder_active(self, value):
        self._encoder_active = value

    def update(self, knobs_touched, encoder_touched):
        for index in range(min(self._knob_count, len(knobs_touched))):
            result = (1 if knobs_touched[index] else 0) - (1 if self._knobs[index] else 0)
            self._knobs[index] = knobs_touched[index]

            if result > 0:
                self.on_knob_touched(index)
            elif result < 0:
                self.on_knob_released(index)

        result = (1 if encoder_touched else 0) - (1 if self._encoder else 0)
        self._encoder = encoder_touched

        if result > 0:
            self._encoder_timer.stop()
            self.encoder_active = True
        elif result < 0:
            self._encoder_timer.restart()

    def on_knob_touched(self, index):
        if self.active_index == -1 or self._knob_timer.running:
            self._knob_timer.stop()
            self.active_index = index

    def on_knob_released(self, index):
        touched_index = -1
        for index in range(self._knob_count):
            if self._knobs[index]:
                touched_index = index

        if touched_index != -1:
            self.active_index = touched_index
        else:
            self._knob_timer.restart()

    def delayed_knob_release(self):
        self._knob_timer.stop()
        self.active_index = -1

    def delayed_encoder_release(self):
        self._encoder_timer.stop()
        self.encoder_active = False

TOUCH_STATES = TouchStates()

class Notifications(DefaultNotifications):

    class Device(DefaultNotifications.Device):
        lock = DefaultNotifications.DefaultText()
        select = DefaultNotifications.DefaultText()
        bank = DefaultNotifications.DefaultText()

    class Track(DefaultNotifications.Track):
        lock = DefaultNotifications.DefaultText()

    class Clip(DefaultNotifications.Clip):
        select = lambda clip: f"{clip[:LCD_LINE_LENGTH]}\nselected"
        select: "Notification[Fn[str]]"

    class Recording(DefaultNotifications.Recording):
        fixed_length = "Fixed length rec\n{}".format
        fixed_length: "Notification[Fn[str]]"

    class SelectedParameterControl:
        select = lambda device, param: f"Select {device[:LCD_LINE_LENGTH - 7]}\n{param}"
        select: "Notification[Fn[str, str]]"

    class NoteRepeat:
        repeat_rate = "Note repeat rate\n{}".format
        repeat_rate: "Notification[Fn[str]]"

    class VelocityLevels:
        select = "Sequencer velocity\n{}".format
        select: "Notification[Fn[int]]"
    
    class DrumGroup(DefaultNotifications.DrumGroup):
        class Pad(DefaultNotifications.DrumGroup.Pad):
            select = DefaultNotifications.DefaultText()

    class Simpler(DefaultNotifications.Simpler):
        class Slice(DefaultNotifications.Simpler.Slice):
            select = lambda index: f"Slice {index}({pitch_index_to_string(int(index) - 1 + BASE_SLICING_NOTE, PITCH_NAMES)})\n selected"
            select: "Notification[Fn[str]]"
            
    class Keyboard:
        select = lambda note: f"Note {pitch_index_to_string(note, PITCH_NAMES)}\nselected"
        select: "Notification[Fn[int]]"

    class StepSequence:
        grid_resolution = "Step sequence grid\n{}".format
        grid_resolution: "Notification[Fn[str]]"

def create_root_view():
    logger.info("Init display")

    def mixer_view(state, content):
        control_name = state.mixer.control_name
        content.lines[0] = f"Param:{control_name}"
        content.lines[2] = "{:<6}|{:<6}|{:<6}|{:<6}".format(*[to_pan_or_send_value(knob) for knob in state.elements.knobs[:4]])

        content.lines[1] = f"{'Lock' if state.target_track.is_locked_to_track else 'Track'}:"
        content.lines[1] += state.target_track.target_track.name[:LCD_LINE_LENGTH - len(content.lines[1])]
        content.lines[3] = "{:<6}|{:<6}|{:<6}|{:<6}".format(*[adjust_gain_string(knob.parameter_value) for knob in state.elements.knobs[4:]])

    def device_view(state, content):
        if liveobj_valid(state.device.device):
            names = [info.parameter.name if liveobj_valid(info.parameter) else "" for info in state.device.current_parameters]
            values = [get_display_value(info.parameter) if liveobj_valid(info.parameter) else "" for info in state.device.current_parameters]

            content.lines[0] = "{:<6}|{:<6}|{:<6}|{:<6}".format(*[adjust_string(x, 6) for x in names[:4]])
            content.lines[1] = "{:<6}|{:<6}|{:<6}|{:<6}".format(*[adjust_string(x, 6) for x in names[4:]])
            content.lines[2] = "{:<6}|{:<6}|{:<6}|{:<6}".format(*[adjust_string(x, 6) for x in values[:4]])
            content.lines[3] = "{:<6}|{:<6}|{:<6}|{:<6}".format(*[adjust_string(x, 6) for x in values[4:]])
        else:
            content.lines[0] = "No device selected"
            content.lines[1] = ""
            content.lines[2] = ""
            content.lines[3] = ""
        
    def clip_view(state, content):
        clip = state.target_track.target_clip

        if liveobj_valid(clip):
            name = clip.name[:13]
            if clip.looping:
                content.lines[0] = f"{name:<13}|Off:{state.clip_editor.start_marker:<10}"
                content.lines[2] = f"S:{state.clip_editor.loop_offset:<11}|Len:{state.clip_editor.loop_length}"
            else:
                content.lines[0] = f"{name:<13}|Non-looped"
                content.lines[2] = f"S:{state.clip_editor.loop_start:<11}|E:{state.clip_editor.loop_end:<11}"

            launch_mode = adjust_string(LaunchModeList.to_string(clip.launch_mode), 6)
            quantize = ClipLaunchQuantizationList.to_string(clip.launch_quantization)
            #quantization = ClipLaunchQuantizationList.to_string(clip.launch_quantization)
            if clip.is_audio_clip:
                content.lines[1] = f"{launch_mode:<6}|{quantize:<6}|Legato|Warp"
                warp = WarpModeList.to_string(clip.warp_mode) if clip.warping else "No Warp"
                pitch = f"{clip.pitch_coarse + clip.pitch_fine * 0.01:+.2f}st"
                gain = adjust_gain_string(clip.gain_display_string)
                # 7 + 9 + 9 = 25
                content.lines[3] = f"{gain:<6}|{pitch:>8}|{warp:<8}"
            else:
                content.lines[1] = f"{launch_mode:<6}|{quantize:<6}|Legato|"
                content.lines[3] = "Nudge |Steps |Fine  |Vel"
        else:
            content.lines[0] = "No clip selected"
            content.lines[1] = ""
            content.lines[2] = ""
            content.lines[3] = ""

    def browser_view(state, content):
        content.lines[0] = ""
        folder_name = state.browser.parent_folder_name or NO_ITEM
        item_name = state.browser.selected_item_name or NO_ITEM

        content.lines[0] = f"In:{folder_name}"
        content.lines[1] = ""
        content.lines[2] = f">{item_name[:LCD_LINE_LENGTH - 1]}"
        content.lines[3] = f"{item_name[LCD_LINE_LENGTH - 1:]}"

    def knob_control_view(state, content):
        #logger.info(f"index = {TOUCH_STATES.active_index}")
        display_mode = state.buttons_and_knobs_modes.selected_mode
        if display_mode == DEVICE_CONTROL and liveobj_valid(state.device.device):
            index = TOUCH_STATES.active_index
            if index != -1:
                info = state.device.current_parameters[index]
                if liveobj_valid(info.parameter):
                    name = info.parameter.name[:LCD_LINE_LENGTH]
                    value = get_display_value(info.parameter)
                    content.lines[0 if index < 4 else 1] = name
                    content.lines[2 if index < 4 else 3] = value
        elif display_mode == TRACK_MIXER:
            index = TOUCH_STATES.active_index
            if index != -1:
                parameter = state.elements.knob_touch_buttons[index].controlled_parameter
                if liveobj_valid(parameter):
                    track_name = liveobj_name(parameter_owner(parameter))[:LCD_LINE_LENGTH]
                    param_name = liveobj_name(parameter)
                    value = get_display_value(parameter)
                    content.lines[0 if index < 4 else 1] = f"{track_name}"
                    content.lines[2 if index < 4 else 3] = f"{param_name}:{value}"
        elif display_mode == CLIP_CONTROL:
            clip = state.target_track.target_clip
            index = TOUCH_STATES.active_index
            if liveobj_valid(clip):
                if clip.looping:
                    if index == 0:
                        content.lines[0] = "Loop start"
                        content.lines[2] = f"{state.clip_editor.loop_offset}"
                    elif index == 1:
                        content.lines[0] = "Loop length"
                        content.lines[2] = f"{state.clip_editor.loop_length}"
                    elif index == 2:
                        content.lines[0] = "Play start"
                        content.lines[2] = f"{state.clip_editor.start_marker}"
                else:
                    if index == 0:
                        content.lines[0] = "Clip start"
                        content.lines[2] = f"{state.clip_editor.loop_start}"
                    elif index == 1:
                        content.lines[0] = "Clip end"
                        content.lines[2] = f"{state.clip_editor.loop_end}"
                
                if clip.is_audio_clip:
                    if index == 4:
                        content.lines[1] = "Gain"
                        content.lines[3] = f"{clip.gain_display_string}"
                    elif index == 5:
                        content.lines[1] = "Pitch"
                        content.lines[3] = f"{clip.pitch_coarse + clip.pitch_fine * 0.01:+.2f}st"
                    elif index == 6:
                        content.lines[1] = "Warp mode"
                        content.lines[3] = WarpModeList.to_string(clip.warp_mode) if clip.warping else "No Warp"

        if TOUCH_STATES.encoder_active:
            encoder_mode = state.encoder_modes.selected_mode
            if encoder_mode == MASTER_VOLUME:
                content.lines[0] = "Master Volume"
                content.lines[2] = f"{state.master_volume.gain_string}"
            elif encoder_mode == GROOVE_AMOUNT:
                content.lines[0] = "Groove Amount"
                content.lines[2] = f"{state.groove_pool.amount_string}"
            elif encoder_mode == ARRANGE_POSITION:
                content.lines[0] = "Song Time"
                content.lines[2] = f"{state.transport.current_song_time_in_bars}({state.transport.current_song_time})"
            elif encoder_mode == SONG_TEMPO:
                content.lines[0] = "Song Tempo"
                content.lines[2] = f"{state.transport.song_tempo:.2f} BPM"
            elif encoder_mode == CLIP_SCALE:
                content.lines[0] = f"Scale({'On' if state.scale_system.scale_mode else 'Off'}):{state.scale_system.scale_name}"
                content.lines[2] = f"Root Note:{PITCH_NAMES[state.scale_system.root_note]}"

    @View
    def main_view(state):
        TOUCH_STATES.update([k.is_pressed for k in state.elements.knob_touch_buttons], state.elements.encodercap.is_pressed)
        content = Content()
        display_mode = state.buttons_and_knobs_modes.selected_mode
        if display_mode == TRACK_MIXER:
            mixer_view(state, content)
        elif display_mode == DEVICE_CONTROL:
            device_view(state, content)
        elif display_mode == CLIP_CONTROL:
            clip_view(state, content)
        elif display_mode == BROWSER:
            browser_view(state, content)

        knob_control_view(state, content)

        if state.elements.setting.is_pressed:
            content.lines[0] = "CustomMaschineMK3 by chiaki"
            content.lines[2] = "Version 1.00"
        
        return content    

    def notification_content(state, event):
        logger.debug(f"notification: {event}")
        content = main_view(state)
        messages = str.splitlines(event)
        content.lines[0] = messages[0]
        if len(messages) > 1:
            content.lines[2] = messages[1]
 
        return content

    return CompoundView(
        NotificationView(notification_content, duration = 1.5, supports_new_line = True),
        main_view)

def protocol(elements):

    def display(content: Content):
        if content:
            elements.display_line_0.display_message(content.lines[0])
            elements.display_line_1.display_message(content.lines[1])
            elements.display_line_2.display_message(content.lines[2])
            elements.display_line_3.display_message(content.lines[3])

    return display

MaschineDisplay = DisplaySpecification(
    create_root_view = create_root_view,
    protocol = protocol,
    notifications = Notifications)
