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

from custom_maschine.logger import logger
from custom_maschine.util import install_signed_bit_delta_patch

class MaschineMikroMK3Elements(ElementsBase):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        logger.info("Create elements")
        install_signed_bit_delta_patch()

        # Definition of control
        # Control element represents actual hardware button, knob or other MIDI control.
        # Use "add_xxx" methods to add control elements.
        # These methods create elements and contain as attribute at specified name.
        # There're some rules related to naming likely to forget.
        # 1. UPPER CASE LETTERS convert to lower case letters.
        # 2. Spaces replace to underscore(_).
        # 3. Matrix control's name must be ends with 's'. (does it means plural form?)

        add_button = partial(self.add_button, channel = 0)
        add_encoder = partial(self.add_encoder, channel = 0)
        # Modifier buttons can bind to multiple combo elements
        add_modifier_button = partial(self.add_modifier_button, channel = 0)

        # Maschine Mikro MK3 doesn't have access to SHIFT button.
        # This script uses FOLLOW button as shift.
        add_modifier_button(56, "Shift")

        add_button(38, "Maschine")
        add_button(39, "Star")
        add_button(40, "Browser")

        add_encoder(7, "Encoder", map_mode = MapMode.LinearTwoCompliment, is_feedback_enabled = False)
        add_button(8, "EncoderPush", is_feedback_enabled = False)
        self.add_element(
            "EncoderCap",
            TouchElement,
            identifier = 9,
            channel = 0,
            is_feedback_enabled = False,
            encoder = self.encoder)

        add_button(44, "Volume")
        add_modifier_button(45, "Plugin")
        add_button(46, "Swing")
        add_button(47, "Sampling")
        add_button(48, "Tempo")

        add_button(49, "Pitch")
        add_modifier_button(50, "Mod")
        add_modifier_button(51, "Perform")
        add_button(52, "Notes")

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

        add_modifier_button(34, "Group")
        add_button(35, "Auto")
        add_button(36, "Lock")
        add_modifier_button(37, "NoteRep")

        add_button(53, "Restart")
        add_modifier_button(54, "Erase")
        add_button(55, "Tap")
        # This is original FOLLOW button.
        # add_button(56, "Follow")

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
        add_modifier_button(90, "Select")
        add_modifier_button(91, "Solo")
        add_modifier_button(92, "Mute")

        self.add_matrix(
            create_matrix_identifiers(60, 76, 4, True),
            "pads",
            element_factory = ButtonElement,
            msg_type = MIDI_NOTE_TYPE,
            is_rgb = True)

        self.add_submatrix(self.pads, "upper_half_pads", rows = (0, 2), columns = (0, 4))
        self.add_submatrix(self.pads, "lower_half_pads", rows = (2, 4), columns = (0, 4))
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
        self.add_modified_control(self.encoder, self.plugin)
        self.add_modified_control(self.encoder, self.shift)
        self.add_modified_control(self.encoderpush, self.shift)
        # TODO: These will be remapped
        # self.add_modified_control(self.track_buttons, self.macro)
        # self.add_modified_control(self.track_buttons, self.mute)
        # self.add_modified_control(self.track_buttons, self.solo)
        # self.add_modified_control(self.track_buttons, self.select)
        # self.add_modified_control(self.track_buttons, self.mod)
        # self.add_modified_control(self.group_buttons, self.perform)
        # self.add_modified_control(self.group_buttons, self.pattern)
        self.add_modified_control(self.mod, self.erase)
        self.add_modified_control(self.lock, self.plugin)
        self.add_modified_control(self.lock, self.noterep)
        self.add_modified_control(self.events, self.erase)
        self.add_modified_control(self.variation, self.duplicate)
        self.add_modified_control(self.duplicate, self.shift)
        self.add_modified_control(self.solo, self.erase)
        self.add_modified_control(self.mute, self.erase)
        self.add_modified_control(self.upper_half_pads, self.group)
        self.add_modified_control(self.lower_half_pads, self.group)
        self.add_modified_control(self.row0_pads, self.shift)
        self.add_modified_control(self.row2_pads, self.shift)
        self.add_modified_control(self.row3_pads, self.shift)
        self.add_modified_control(self.row3_pads, self.mute)
        self.add_modified_control(self.column3_pads, self.scene)
        self.add_modified_control(self.stop, self.shift)
        self.add_modified_control(self.erase, self.shift)
