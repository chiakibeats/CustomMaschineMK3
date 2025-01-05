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

from .ClipEditorComponent import LaunchModeList, ClipLaunchQuantizationList, WarpModeList
from .Logger import logger

LCD_LINES = 4
LCD_LINE_LENGTH = 28
NO_ITEM = "---"
NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

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
        if gain_string[0] != "-":
            gain_string = " " + gain_string
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

class Notifications(DefaultNotifications):

    class Device(DefaultNotifications.Device):
        lock = DefaultNotifications.DefaultText()
        select = DefaultNotifications.DefaultText()
        bank = DefaultNotifications.DefaultText()

    class Track(DefaultNotifications.Track):
        lock = DefaultNotifications.DefaultText()

    class Clip(DefaultNotifications.Clip):
        select = DefaultNotifications.DefaultText()

    class Recording(DefaultNotifications.Recording):
        fixed_length = "Fixed length rec\n{}".format
        fixed_length: "Notification[Fn[str]]"

    class SelectedParameterControl:
        select = "Select {}\n{}".format
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
            select = lambda index: f"Slice {index}({pitch_index_to_string(int(index) - 1 + BASE_SLICING_NOTE, NOTES)})\n selected"
            select: "Notification[Fn[str]]"
            
    class Keyboard:
        select = lambda note: f"Note {pitch_index_to_string(note, NOTES)}\nselected"
        select: "Notification[Fn[int]]"

def create_root_view():
    logger.info("Init display")

    def mixer_view(state, content):
        control_name = state.mixer.control_name
        content.lines[0] = f"Parameter:{control_name}"
        content.lines[2] = "{:<6}|{:<6}|{:<6}|{:<6}".format(*[to_pan_or_send_value(knob) for knob in state.elements.knobs[:4]])

        content.lines[1] = f"{'Locked' if state.target_track.is_locked_to_track else 'Target'}:{state.target_track.target_track.name}"
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
            name = adjust_string(clip.name, 13)
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
                content.lines[1] = f"{launch_mode:<6}|{quantize:>6}|Legato|Warp"
                warp = WarpModeList.to_string(clip.warp_mode) if clip.warping else "No Warp"
                pitch = f"{clip.pitch_coarse + clip.pitch_fine * 0.01:+.2f}st"
                gain = adjust_gain_string(clip.gain_display_string)
                # 7 + 9 + 9 = 25
                content.lines[3] = f"{gain:<6}|{pitch:>8}|{warp:<8}"
            else:
                content.lines[1] = f"{launch_mode:<6}|{quantize:>6}|Legato|"
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
        #logger.info(f"index = {state.knob_touch_state.active_index}")
        display_mode = state.buttons_and_knobs_modes.selected_mode
        if display_mode == DEVICE_CONTROL and liveobj_valid(state.device.device):
            index = state.device.active_index
            if index != -1:
                info = state.device.current_parameters[index]
                if liveobj_valid(info.parameter):
                    name = info.parameter.name
                    value = get_display_value(info.parameter)
                    content.lines[0 if index < 4 else 1] = name
                    content.lines[2 if index < 4 else 3] = value
        elif display_mode == TRACK_MIXER:
            index = state.mixer.active_index
            if index != -1:
                parameter = state.elements.knob_touch_buttons[index].controlled_parameter
                if liveobj_valid(parameter):
                    track_name = liveobj_name(parameter_owner(parameter))
                    param_name = liveobj_name(parameter)
                    value = get_display_value(parameter)
                    content.lines[0 if index < 4 else 1] = f"{track_name}"
                    content.lines[2 if index < 4 else 3] = f"{param_name}:{value}"

        if state.elements.encodercap.is_pressed:
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
                content.lines[2] = f"Root Note:{NOTES[state.scale_system.root_note]}"

    @View
    def main_view(state):
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
