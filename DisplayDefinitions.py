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
    selected_pitches = []
    tempo = 0.0
    is_scale_enabled = False
    scale_name = "Chromatic"
    scale_root_note = "C"
    groove_amount = 0.0
    selected_grid = None

class Notifications(DefaultNotifications):

    class Device(DefaultNotifications.Device):
        bank = DefaultNotifications.DefaultText()


def create_root_view():
    logger.info("Init display")
    @View
    def main_view(state):
        content = Content()

        content.selected_track = state.target_track.target_track
        content.selected_device = state.device.device or "-"

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

    return display


MaschineDisplay = DisplaySpecification(
    create_root_view = create_root_view,
    protocol = protocol,
    notifications = Notifications)
