# ==================================================
#
# This file is part of CustomMaschineMK3.
# CustomMaschineMK3 is free software licensed under GPL-3.0.
# For more details, see "LICENSE" file.
# 
# Copyright (C) 2024-2025 chiaki
#
# ==================================================


from functools import partial
from itertools import product
from ableton.v3.control_surface.elements_base import (
    ElementsBase,
    MapMode,
    create_matrix_identifiers
)

from ableton.v3.control_surface.elements import (
    ButtonElement,
    EncoderElement,
    TouchElement,
    ButtonMatrixElement,
    DisplayLineElement,
)

from ableton.v3.control_surface.display import Text

from ableton.v3.control_surface import (
    MIDI_CC_TYPE,
    MIDI_NOTE_TYPE,
    MIDI_PB_TYPE,
    MIDI_SYSEX_TYPE,
    PrioritizedResource
)

from ableton.v2.control_surface.elements.encoder import ENCODER_VALUE_NORMALIZER
from ableton.v3.base import in_range
import Live # type: ignore

from .Logger import logger
from .SysexShiftButton import SysexShiftButton
from . import Config
from .DisplayDefinitions import (
    LCD_LINES,
    LCD_LINE_LENGTH,
    make_mcu_display_header,
    make_display_sysex_message
)

# There's a miscalculation in signed_bit_delta function.
# The original version chooses different acceleration factor between increment and decrement side.
# To fix problem, replace function to correct one.
SIGNED_BIT_DEFAULT_DELTA = 20.0
SIGNED_BIT_VALUE_MAP = (1, 2, 3, 4, 5, 8, 10, 20, 50)

def fixed_signed_bit_delta(value):
    delta = SIGNED_BIT_DEFAULT_DELTA
    is_increment = value <= 64
    index = (value if is_increment else value - 64) - 1 # Original subtracts 1 only increment side
    if in_range(index, 0, len(SIGNED_BIT_VALUE_MAP)):
        delta = SIGNED_BIT_VALUE_MAP[index]
    if is_increment:
        return delta
    return -delta

ENCODER_VALUE_NORMALIZER[Live.MidiMap.MapMode.relative_signed_bit] = fixed_signed_bit_delta

class ForceToggleButtonElement(ButtonElement):
    _internal_received_value = 0
    
    def receive_value(self, value):
        logger.debug(f"ForceToggle receive_value value = {value}")
        prev_value = int(self._internal_received_value) > 0
        self._internal_received_value = value
        if not prev_value and int(self._internal_received_value) > 0:
            value = 0 if int(self._last_received_value) > 0 else 1
            logger.debug(f"Trigger toggle value = {value}")
            super().receive_value(value)

class HookedButtonElement(ButtonElement):
    button_id = 0

    def __init__(self, *a, **k):
        super().__init__(*a, **k)

    def send_value(self, value, force = False, channel = None):
        logger.debug(f"button {self.button_id} value = {value}, force = {force}, channel = {channel}")
        return super().send_value(value, force, channel)

class ControlElements(ElementsBase):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        logger.info("Create elements")

        if Config.LCD_ENABLED:
            default_channel = 1
        else:
            default_channel = 0

        # Definition of control
        # Control element represents actual hardware button, knob or other MIDI control.
        # Use "add_xxx" methods to add control elements.
        # These methods create elements and contain as attribute at specified name.
        # There're some rules related to naming likely to forget.
        # 1. UPPER CASE LETTERS convert to lower case letters.
        # 2. Spaces replace to underscore(_).
        # 3. Matrix control's name must be ends with 's'. (does it means plural form?)

        add_button = partial(self.add_button, channel = default_channel)
        add_encoder = partial(self.add_encoder, channel = default_channel)
        add_button_matrix = partial(self.add_button_matrix, channels = default_channel)
        # Modifier buttons can bind to multiple combo elements
        add_modifier_button = partial(self.add_modifier_button, channel = default_channel)

        add_modifier_button(119, "Shift")

        add_encoder(64, "PedalTip", map_mode = MapMode.Absolute)
        add_encoder(65, "PedalRing", map_mode = MapMode.Absolute)

        add_button(34, "Channel")
        add_modifier_button(35, "Plugin")

        add_button(36, "Arranger")
        add_button(37, "Mixer")

        add_button(38, "Browser")
        add_button(39, "Sampling")

        add_button(110, "Left")
        add_button(111, "Right")

        add_button(40, "File")
        add_button(41, "Setting")

        add_button(42, "Auto")
        add_modifier_button(43, "Macro")

        add_encoder(7, "Encoder", map_mode = MapMode.LinearTwoCompliment, is_feedback_enabled = False)
        add_button(8, "EncoderPush", is_feedback_enabled = False)
        self.add_element(
            "EncoderCap",
            TouchElement,
            identifier = 9,
            channel = default_channel,
            is_feedback_enabled = False,
            encoder = self.encoder)
        add_button(30, "EncoderUp")
        add_button(31, "EncoderRight")
        add_button(32, "EncoderDown")
        add_button(33, "EncoderLeft")

        add_button(44, "Volume")
        add_button(45, "Swing")
        add_modifier_button(46, "NoteRep")
        add_button(47, "Tempo")
        add_button(48, "Lock")

        add_button(49, "Pitch")
        add_modifier_button(50, "Mod")
        add_modifier_button(51, "Perform")
        add_button(52, "Notes")
        # self.add_element(
        #     "Notes",
        #     ForceToggleButtonElement,
        #     identifier = 52,
        #     channel = default_channel,
        #     resource_type = PrioritizedResource)

        # For simulating pitch bend behaviour, touch strip controls use some trick.
        # Touch strip movement("Touchstrip") is mapped to channel 1 pitch bend.
        # It works as sending pitch bend value normally.
        # Touch strip proximity("TouchstripCap") is mapped to channel 2 pitch bend, It sends fixed value(8191) when finger released
        # Proximity part works as "cleanup" for pitch bend value change.
        # So these settings enable returning to original pitch automatically.
        # (Most of modern soft synths apply last sent value and don't care about which channel used, but if you trouble with pitch bend, refer to this comment.)

        self.add_encoder(
            1,
            "Touchstrip",
            msg_type = MIDI_PB_TYPE,
            map_mode = MapMode.Absolute14Bit,
            is_feedback_enabled = True,
            feedback_delay = -1,
            send_should_depend_on_forwarding = False)
        self.add_encoder(
            2,
            "TouchstripCap",
            msg_type = MIDI_PB_TYPE,
            is_feedback_enabled = False,
            channel = 1)
        
        add_button_matrix(
            create_matrix_identifiers(100, 108, 4),
            "group_buttons",
            is_rgb = True)

        add_button(53, "Restart")
        add_modifier_button(54, "Erase")
        add_button(55, "Tap")
        add_button(56, "Follow")

        add_button(57, "Play")
        add_button(58, "Rec")
        add_button(59, "Stop")

        add_button(80, "FixedVel")
        add_button(81, "PadMode")
        add_button(82, "Keyboard")
        add_button(83, "Chords")
        add_button(84, "Step")

        add_modifier_button(85, "Scene")
        add_modifier_button(86, "Pattern")
        add_button(87, "Events")
        add_button(88, "Variation")
        add_modifier_button(89, "Duplicate")
        add_button(90, "Select")
        add_modifier_button(91, "Solo")
        add_modifier_button(92, "Mute")

        add_button_matrix([list(range(0, 8))], "track_buttons", msg_type = MIDI_NOTE_TYPE)

        # Another weird hack used for enabling Maschine display.
        # After some investigation, I found these facts:
        # 1. To enable maschine display, at least one knob or button around display is mapped to MCU control.
        # 2. Display protocol is same to MCU one. Send sysex message to update.
        #    (If you want to know details, read "Mackie Control Protocol" (unofficial) document by Nicolas Jarnoux)
        # 3. Display area is 4 x 28 characters.
        # 
        # Transport layer of MCU protocol is plain MIDI. Manufacturers define usage of each CCs and Notes.
        # MCU V-Pots(1 to 8) are mapped to CC 16 to CC 23 at channel 1.
        # The reason of changing MIDI channel is avoid conflict with MCU protocol(MCU uses MIDI channel 1)
        if Config.LCD_ENABLED:
            self.add_encoder_matrix(
                [list(range(16, 24))],
                "Knobs",
                map_mode = MapMode.AccelSignedBit,
                sensitivity_modifier = self.macro,
                is_feedback_enabled = False)
        else:
            self.add_encoder_matrix(
                [list(range(70, 78))],
                "Knobs",
                map_mode = MapMode.AccelTwoCompliment,
                sensitivity_modifier = self.macro,
                is_feedback_enabled = False)

        knobs_iterator = iter(self.knobs_raw)

        self.add_matrix(
            [list(range(10, 18))],
            "knob_touch_buttons",
            channels = default_channel,
            element_factory = lambda *a, **k: TouchElement(*a, encoder = next(knobs_iterator), **k),
            is_feedback_enabled = False)

        self.add_matrix(
            create_matrix_identifiers(60, 76, 4, True),
            "pads",
            element_factory = ButtonElement,
            msg_type = MIDI_NOTE_TYPE,
            is_rgb = True)
        
        # Maschine MK3 and Plus "SHIFT" button send sysex message when button is pushed or released.
        # Base format: 0xF0, 0x00, 0x21, 0x09, {2 bytes device ID}, 0x4D, 0x50, 0x00, 0x01, 0x4D, {button state}, 0xF7
        # Maschine MK3 device ID: 0x16, 0x00
        # Maschine Plus device ID: 0x18, 0x20
        # Button states: 0x01 is button pushed and 0x00 is released

        self.add_element(
            "shift_sysex",
            element_factory = SysexShiftButton,
            sysex_identifier = (0xF0, 0x00, 0x21, 0x09, 0x16, 0x00, 0x4D, 0x50, 0x00, 0x01, 0x4D),
            use_first_byte_as_value = True,
            target_button = self.shift)

        # I just copy-paste definition to minimize structure changes...
        # These constants will be consolidated into one file.
        self.add_element(
            "shift_sysex_plus",
            element_factory = SysexShiftButton,
            sysex_identifier = (0xF0, 0x00, 0x21, 0x09, 0x18, 0x20, 0x4D, 0x50, 0x00, 0x01, 0x4D),
            use_first_byte_as_value = True,
            target_button = self.shift)
        
        if Config.LCD_ENABLED:
            for line in range(LCD_LINES):
                self.add_sysex_display_line(
                    make_mcu_display_header(line),
                    f"display_line_{line}",
                    partial(make_display_sysex_message, line),
                    Text(max_width = LCD_LINE_LENGTH))

        self.add_submatrix(self.knobs, "left_half_knobs", columns = (0, 4))
        self.add_submatrix(self.knobs, "right_half_knobs", columns = (4, 8))
        self.add_submatrix(self.knob_touch_buttons, "left_half_knob_touch_buttons", columns = (0, 4))
        self.add_submatrix(self.knob_touch_buttons, "right_half_knob_touch_buttons", columns = (4, 8))
        self.add_submatrix(self.track_buttons, "left_half_track_buttons", columns = (0, 4))
        self.add_submatrix(self.track_buttons, "right_half_track_buttons", columns = (4, 8))
        self.add_submatrix(self.group_buttons, "upper_group_buttons", rows = (0, 1))
        self.add_submatrix(self.pads, "row0_pads", rows = (0, 1), columns = (0, 4))
        self.add_submatrix(self.pads, "row2_pads", rows = (2, 3), columns = (0, 4))
        self.add_submatrix(self.pads, "row3_pads", rows = (3, 4), columns = (0, 4))
        self.add_submatrix(self.pads, "column3_pads", rows = (0, 4), columns = (3, 4))
        self.original_order_pads = self.pads.submatrix[(slice(0, 4), slice(None, None, -1))]
        self.original_order_pads.name = "original_order_pads"
        self.original_order_pads.is_private = True


        # Modified control consists with 2 control elements.
        # One is modifier, which needs to press first to notify control is to modified.
        # Other one is control, this is button or knob to be modified.
        # Name of modified control is "{control_name}_with_{modifier_name}"
        # Modified control behaves like separate control element along side with original element.
        # LED feedback(message to hardware) and value change(incoming message) process properly depend on modifier state.
        #self.add_modified_control(self.tempo, self.shift)
        self.add_modified_control(self.browser, self.shift)
        self.add_modified_control(self.left, self.plugin)
        self.add_modified_control(self.right, self.plugin)
        self.add_modified_control(self.encoder, self.plugin)
        self.add_modified_control(self.file, self.shift)
        self.add_modified_control(self.file, self.duplicate)
        self.add_modified_control(self.file, self.erase)
        self.add_modified_control(self.encoder, self.shift)
        self.add_modified_control(self.encoderpush, self.shift)
        self.add_modified_control(self.encoderup, self.shift)
        self.add_modified_control(self.encoderright, self.shift)
        self.add_modified_control(self.encoderdown, self.shift)
        self.add_modified_control(self.encoderleft, self.shift)
        self.add_modified_control(self.track_buttons, self.macro)
        self.add_modified_control(self.track_buttons, self.mute)
        self.add_modified_control(self.track_buttons, self.mod)
        self.add_modified_control(self.left_half_track_buttons, self.mute)
        self.add_modified_control(self.left_half_track_buttons, self.solo)
        self.add_modified_control(self.upper_group_buttons, self.perform)
        # self.add_modified_control(self.group_buttons, self.notes)
        self.add_modified_control(self.group_buttons, self.pattern)
        self.add_modified_control(self.mod, self.erase)
        self.add_modified_control(self.lock, self.plugin)
        self.add_modified_control(self.lock, self.noterep)
        self.add_modified_control(self.events, self.erase)
        self.add_modified_control(self.duplicate, self.shift)
        self.add_modified_control(self.solo, self.erase)
        self.add_modified_control(self.mute, self.erase)
        self.add_modified_control(self.row0_pads, self.shift)
        self.add_modified_control(self.row2_pads, self.shift)
        self.add_modified_control(self.row3_pads, self.shift)
        self.add_modified_control(self.row3_pads, self.mute)
        self.add_modified_control(self.column3_pads, self.scene)
        self.add_modified_control(self.stop, self.shift)
        self.add_modified_control(self.erase, self.shift)
