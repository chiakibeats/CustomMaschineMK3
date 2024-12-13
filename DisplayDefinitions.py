from dataclasses import dataclass
from ableton.v3.control_surface.display import DefaultNotifications, DisplaySpecification
from ableton.v3.control_surface.display.view import View, CompoundView, NotificationView
from ableton.v3.live import liveobj_name, liveobj_valid
from ableton.v3.control_surface.display.text import adjust_string

from .ClipEditorComponent import LaunchModeList, ClipLaunchQuantizationList, WarpModeList
from .Logger import logger

LCD_LINES = 4
LCD_LINE_LENGTH = 28

def make_mcu_display_header(line):
    return (0xF0, 0x00, 0x00, 0x66, 0x17, 0x12, 28 * min(line, LCD_LINES - 1))

def make_display_sysex_message(line, message):
    return make_mcu_display_header(line) + message + (0xF7,)

class Content:
    selected_mode = None
    selected_track = None
    selected_device = None
    selected_parameter_bank = None
    current_tracks_in_ring = []
    selected_clip = None
    selected_folder = None
    selected_browser_item = None
    selected_pitches = []
    tempo = 0.0
    is_scale_enabled = False
    scale_name = "Chromatic"
    scale_root_note = "C"
    groove_amount = 0.0
    selected_grid = None
    display_mode = None

class Notifications(DefaultNotifications):

    class Device(DefaultNotifications.Device):
        bank = DefaultNotifications.DefaultText()

def try_get_attr(obj, attr, default = None):
    if obj != None:
        return getattr(obj, attr)
    else:
        return default

def create_root_view():
    logger.info("Init display")
    @View
    def main_view(state):
        content = Content()

        content.selected_track = state.target_track.target_track.name
        content.selected_clip = state.target_track.target_clip
        content.selected_device = try_get_attr(state.device.device, "name", "---")
        content.selected_folder = try_get_attr(state.browser.parent_folder, "name", "---")
        content.selected_browser_item = state.browser.selected_item
        content.display_mode = state.buttons_and_knobs_modes.selected_mode

        return content

    def notification_content(state, event):
        logger.info(f"View notification event {event}")
        main_content = main_view(state)
        return main_content

    return CompoundView(NotificationView(notification_content), main_view)

def protocol(elements):

    def display_clip_info(content: Content):
        clip =  content.selected_clip
        name = " "
        loop_offset = " "
        loop_length = " "
        start_marker = " "
        mute = " "
        loop = "  "
        launch_mode = " "
        quantize = " "
        legato = "   "
        warp = " "
        pitch = " "
        gain = " "
        clip_type = 0

        if liveobj_valid(clip):
            name = adjust_string(clip.name, 13)
            loop_offset = str(clip.position)
            loop_length = str(clip.loop_end - clip.loop_start)
            start_marker = str(clip.start_marker)
            mute = "M" if clip.muted else " "
            loop = "LP" if clip.looping else "  "
            launch_mode = LaunchModeList.to_short_string(clip.launch_mode)
            quantize = ClipLaunchQuantizationList.to_string(clip.launch_quantization)
            legato = "LEG" if clip.legato else "   "
            #quantization = ClipLaunchQuantizationList.to_string(clip.launch_quantization)
            if clip.is_audio_clip:
                warp = WarpModeList.to_string(clip.warp_mode) if clip.warping else "No Warp"
                pitch = f"{clip.pitch_coarse:-}"
                gain = clip.gain_display_string
                clip_type = 1
            else:
                clip_type = 2

        elements.display_line_0.display_message(f"{name:<13}|Off:{start_marker:<10}")
        elements.display_line_2.display_message(f"S:{loop_offset:<11}|Len:{loop_length:<10}")
        # 2 + 3 + 5 + 7 + 3 = 20
        elements.display_line_1.display_message(f"{mute}|{loop}|{launch_mode:<4}|{quantize:<6}|{legato}|")
        if clip_type == 1:
            # 9 + 6 + 9 = 24
            message = f"{warp:<8}|{pitch:>3}st|{gain:>8}"
        elif clip_type == 2:
            message = "Nudge |Length|Pitch |Vel"
        else:
            message = ""
        
        elements.display_line_3.display_message(message)

    def display_browser(content: Content):
        item = content.selected_browser_item
        name = item.name if item != None else "---"
        elements.display_line_0.display_message(f"In:{content.selected_folder}")
        elements.display_line_1.display_message("")
        elements.display_line_2.display_message(f">{name[:LCD_LINE_LENGTH - 1]}")
        elements.display_line_3.display_message(f"{name[LCD_LINE_LENGTH - 1:]}")

    def display(content: Content):
        if content:
            # elements.display_line_0.display_message("CustomMaschineMK3 by chiaki")
            # elements.display_line_2.display_message("Version 0.8")
            if content.display_mode == "default":
                pass
            elif content.display_mode == "device":
                pass
            elif content.display_mode == "clip":
                display_clip_info(content)
            elif content.display_mode == "browser":
                #logger.info(f"folder = {content.selected_folder}, type = {type(content.selected_folder)}")
                # elements.display_line_0.display_message(f"In:{content.selected_folder}")
                # elements.display_line_2.display_message(f">{content.selected_browser_item.name}")
                display_browser(content)
            else:
                elements.display_line_0.display_message(f"Track:{content.selected_track}")
                elements.display_line_2.display_message(f"Clip:{content.selected_clip}")

    return display

MaschineDisplay = DisplaySpecification(
    create_root_view = create_root_view,
    protocol = protocol,
    notifications = Notifications)
