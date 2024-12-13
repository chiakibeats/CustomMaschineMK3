from ableton.v3.control_surface.component_map import ComponentMap
from ableton.v3.control_surface.mode import ToggleBehaviour, MomentaryBehaviour, LatchingBehaviour, ImmediateBehaviour

from . import Config

def create_mappings(surface):
    mappings = {}
    mappings["Transport"] = dict(
        stop_button = "stop",
        loop_button = "restart",
        nudge_down_button = "row2_pads_with_shift_raw[2]",
        nudge_up_button = "row2_pads_with_shift_raw[3]"
    )

    mappings["Mixer"] = dict(
        crossfade_cycle_buttons = "upper_group_buttons_with_perform"
    )

    mappings["View_Based_Recording"] = dict(
        overdub_button = "erase_with_shift"
    )

    # mapping names not found in component map are recognized as mode definition
    mappings["Transport_Modes"] = dict(
        default_behaviour = MomentaryBehaviour(),
        shift_button = "shift",
        default = dict(
            component = "Transport",
            play_button = "play",
            tap_tempo_button = "tap",
            record_quantize_button = "follow",
            automation_arm_button = "auto"),
        shift = dict(
            component = "Transport",
            play_pause_button = "play",
            metronome_button = "tap",
            re_enable_automation_button = "auto")
    )

    mappings["Recording_Modes"] = dict(
        default_behaviour = MomentaryBehaviour(),
        shift_button = "shift",
        default = dict(
            component = "View_Based_Recording",
            record_button = "rec"),
        shift = dict(
            component = "Transport",
            capture_midi_button = "rec"),
    )

    mappings["Misc_Control"] = dict(
        new_audio_or_return_track_button = "file",
        new_midi_track_button = "file_with_shift",
        duplicate_track_button = "file_with_duplicate",
        delete_track_button = "file_with_erase"
    )

    mappings["Encoder_Modes"] = dict(
        default_behaviour = ToggleBehaviour(return_to_default = True),
        volume_button = "volume",
        swing_button = "swing",
        position_button = "swing_with_shift",
        tempo_button = "tempo",
        scale_button = "tempo_with_shift",
        default = dict(
            modes = [
                dict(component = "Misc_Control",
                    select_track_encoder = "encoder",
                    exclusive_arm_button = "encoderpush",
                    arm_button = "encoderpush_with_shift"),
                dict(component = "Session_Navigation",
                    up_button = "encoderup",
                    down_button = "encoderdown",
                    left_button = "encoderleft",
                    right_button = "encoderright",
                    page_up_button = "encoderup_with_shift",
                    page_down_button = "encoderdown_with_shift",
                    page_left_button = "encoderleft_with_shift",
                    page_right_button = "encoderright_with_shift",
                )]),
        volume = dict(
            component = "Master_Volume",
            coarse_volume = "encoder",
            fine_volume = "encoder_with_shift",
            reset_button = "encoderpush"),
        swing = dict(
            component = "Groove_Pool",
            coarse_groove_amount = "encoder",
            fine_groove_amount = "encoder_with_shift"),
        position = dict(
            component = "Transport",
            arrangement_position_encoder = "encoder",
            loop_start_encoder = "encoder_with_shift",
            set_cue_button = "encoderpush",
            prev_cue_button = "encoderup",
            next_cue_button = "encoderdown",
            rewind_button = "encoderleft",
            fastforward_button = "encoderright"),
        tempo = dict(
            component = "Transport",
            tempo_coarse_encoder = "encoder",
            tempo_fine_encoder = "encoder_with_shift"),
        scale = dict(
            component = "Scale_System",
            select_encoder = "encoder",
            root_note_encoder = "encoder_with_shift",
            toggle_button = "encoderpush",
            indicator_button_1 = "encoderup",
            indicator_button_2 = "encoderdown",
            indicator_button_3 = "encoderleft",
            indicator_button_4 = "encoderright"),
    )
    
    mappings["TouchStrip_Modes"] = dict(
        default_behaviour = LatchingBehaviour(),
        pitch_button = "pitch",
        mod_button = "mod",
        perform_button = "perform",
        #notes_button = "notes",
        pitch = dict(
            component = "Maschine_Playable",
            pitchbend_encoder = "touchstrip",
            pitchbend_reset = "touchstripcap"
        ),
        mod = dict(
            component = "Selected_Parameter",
            modulation_encoder = "touchstrip",
            select_buttons = "track_buttons_with_mod"
        ),
        perform = dict(
            component = "Mixer",
            crossfader_control = "touchstrip"
        ),
        # notes = dict(
        #     component = "NoteRepeat",
        #     rate_selector = "touchstrip"
        # )
    )

    mappings["Pad_Modes"] = dict(
        default_behaviour = LatchingBehaviour(),
        default_button = "padmode",
        keyboard_button = None,
        drum_rack_button = None,
        simpler_button = None,
        chord_button = "chords",
        step_button = "step",
        default = dict(
            modes = [
                dict(component = "Session",
                    stop_track_clip_buttons = "row3_pads_with_mute",
                    clip_launch_buttons = "pads",
                    scene_launch_buttons = "column3_pads_with_scene",
                    select_button = "select",
                    delete_button = "erase",
                    copy_button = "duplicate"),
                dict(component = "Session_Overview",
                    matrix = "group_buttons"),
                dict(component = "Mixer",
                    clear_all_solo_button = "solo_with_erase",
                    clear_all_mute_button = "mute_with_erase"),
            ]),
        keyboard = dict(
            component = "Maschine_Playable",
            matrix = "pads",
            octave_select_buttons = "group_buttons",
            scroll_down_button = "row0_pads_with_shift_raw[0]",
            scroll_up_button = "row0_pads_with_shift_raw[1]",
            scroll_page_down_button = "row0_pads_with_shift_raw[2]",
            scroll_page_up_button = "row0_pads_with_shift_raw[3]",
            select_button = "select",
            note_select_button = "events"
        ),
        drum_rack = dict(
            component = "Drum_Group",
            matrix = "pads",
            mute_button = "mute",
            solo_button = "solo",
            scroll_down_button = "row0_pads_with_shift_raw[0]",
            scroll_up_button = "row0_pads_with_shift_raw[1]",
            scroll_page_down_button = "row0_pads_with_shift_raw[2]",
            scroll_page_up_button = "row0_pads_with_shift_raw[3]",
            select_buttons = "group_buttons",
            select_button = "select",
            delete_button = "erase",
            copy_button = "duplicate",
            note_select_button = "events",
            clear_all_solo_button = "solo_with_erase",
            clear_all_mute_button = "mute_with_erase"
        ),
        simpler = dict(
            component = "Sliced_Simpler",
            matrix = "pads",
            scroll_down_button = "row0_pads_with_shift_raw[0]",
            scroll_up_button = "row0_pads_with_shift_raw[1]",
            scroll_page_down_button = "row0_pads_with_shift_raw[2]",
            scroll_page_up_button = "row0_pads_with_shift_raw[3]",
            select_buttons = "upper_group_buttons",
            select_button = "select",
            delete_button = "erase",
            note_select_button = "events"
        ),
        chord = dict(
            component = "Velocity_Levels",
            matrix = "pads",
            select_button = "select"
        ),
        step = dict(
            component = "Step_Sequence",
            step_buttons = "pads" if Config.REVERSE_STEP_PADS else "original_order_pads",
            resolution_buttons = "group_buttons_with_pattern",
            loop_buttons = "group_buttons",
            loop_delete_button = "erase",
            prev_page_button = "row0_pads_with_shift_raw[2]",
            next_page_button = "row0_pads_with_shift_raw[3]",
            select_button = "select"
        ),
    )

    mappings["Buttons_And_Knobs_Modes"] = dict(
        default_behaviour = LatchingBehaviour(),
        default_button = "mixer",
        device_button = "plugin",
        clip_button = "sampling",
        browser_button = "browser",
        default = dict(
            component = "Mixer",
            shift_button = "shift",
            pan_or_send_controls = "left_half_knobs",
            prev_control_button = "left",
            next_control_button = "right",
            volume_controls = "right_half_knobs",
            arm_buttons = "left_half_track_buttons",
            mute_buttons = "left_half_track_buttons_with_mute",
            solo_buttons = "left_half_track_buttons_with_solo",
            track_select_buttons = "right_half_track_buttons",
            volume_touch_controls = "right_half_knob_touch_buttons",
            pan_or_send_touch_controls = "left_half_knob_touch_buttons",
            erase_button = "erase"),
        device = dict(
            modes = [
                dict(component = "Device",
                    parameter_controls = "knobs",
                    parameter_touch_controls = "knob_touch_buttons",
                    prev_bank_button = "left",
                    next_bank_button = "right",
                    bank_select_buttons = "track_buttons_with_macro",
                    erase_button = "erase"
                ),
                dict(component = "Device_Navigation",
                    select_buttons = "track_buttons",
                    on_off_buttons = "track_buttons_with_mute",
                    delete_button = "erase",
                    prev_group_button = "left_with_plugin",
                    next_group_button = "right_with_plugin"
                )
            ]),
        clip = dict(
            component = "Clip_Editor",
            #control_buttons = "track_buttons",
            mute_button = "track_buttons_raw[0]",
            loop_button = "track_buttons_raw[1]",
            crop_button = "track_buttons_raw[2]",
            launch_mode_button = "track_buttons_raw[3]",
            legato_button = "track_buttons_raw[4]",
            warp_button = "track_buttons_raw[5]",
            ram_mode_button = "track_buttons_raw[6]",
            fine_grain_button = "macro",
            control_encoders = "knobs",
            encoder_touch_buttons = "knob_touch_buttons"
        ),
        browser = dict(
            component = "Browser",
            select_encoder = "encoder",
            load_button = "encoderpush",
            enter_folder_button = "encoderright",
            leave_folder_button = "encoderleft",
            preview_toggle_button = "track_buttons_raw[0]",
            preview_volume_encoder = "knobs_raw[0]",
            select_folder_buttons = "track_buttons_with_macro"
        )
    )

    mappings["Session"] = dict(stop_all_clips_button = "stop_with_shift")

    mappings["View_Toggle"] = dict(
        main_view_toggle_button = "arranger",
        browser_view_toggle_button = "browser_with_shift",
    )

    mappings["Undo_Redo"] = dict(
        undo_button = "row3_pads_with_shift_raw[0]",
        redo_button = "row3_pads_with_shift_raw[1]"
    )

    mappings["Clip_Actions"] = dict(
        double_button = "duplicate_with_shift",
        quantize_button = "row2_pads_with_shift_raw[0]",
        half_quantize_button = "row2_pads_with_shift_raw[1]"
    )

    mappings["Accent"] = dict(
        accent_button = "fixedvel"
    )

    mappings["Selected_Parameter"] = dict(
        reset_value_button = "mod_with_erase"
    )

    mappings["Target_Track"] = dict(
        lock_button = "lock"
    )

    mappings["Device"] = dict(
        device_lock_button = "lock_with_plugin"
    )

    mappings["Note_Repeat"] = dict(
        repeat_button = "noterep",
        shift_button = "shift",
        rate_select_mode_button = "notes",
        rate_select_buttons = "group_buttons_with_notes"
    )

    return mappings
