from dataclasses import dataclass
from ableton.v3.control_surface.display import DefaultNotifications, DisplaySpecification
from ableton.v3.control_surface.display.view import View, CompoundView, NotificationView
from ableton.v3.live import liveobj_name

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
        content.selected_clip = try_get_attr(state.target_track.target_clip, "name", "---")
        content.selected_device = try_get_attr(state.device.device, "name", "---")
        content.selected_folder = try_get_attr(state.browser.parent_folder, "name", "---")
        content.selected_browser_item = try_get_attr(state.browser.selected_item, "name", "---")
        content.display_mode = state.buttonsandknobs_modes.selected_mode

        return content

    def notification_content(state, event):
        logger.info(f"View notification event {event}")
        main_content = main_view(state)
        return main_content

    return CompoundView(NotificationView(notification_content), main_view)


def protocol(elements):

    def display(content: Content):
        if content:
            elements.display_line_0.display_message("CustomMaschineMK3 by chiaki")
            elements.display_line_2.display_message("Version 0.8")
            if content.display_mode == "browser":
                #logger.info(f"folder = {content.selected_folder}, type = {type(content.selected_folder)}")
                elements.display_line_1.display_message(f"In:{content.selected_folder}")
                elements.display_line_3.display_message(f">{content.selected_browser_item}")
            else:
                elements.display_line_1.display_message(f"Track:{content.selected_track}")
                elements.display_line_3.display_message(f"Clip:{content.selected_clip}")

    return display


MaschineDisplay = DisplaySpecification(
    create_root_view = create_root_view,
    protocol = protocol,
    notifications = Notifications)
