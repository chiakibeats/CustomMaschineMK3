from ableton.v3.control_surface.component_map import ComponentMap
from ableton.v3.control_surface.mode import ToggleBehaviour, MomentaryBehaviour, LatchingBehaviour, ImmediateBehaviour

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

    mappings["MiscControl"] = dict(
        new_audio_or_return_track_button = "file",
        new_midi_track_button = "file_with_shift",
        duplicate_track_button = "file_with_duplicate",
        delete_track_button = "file_with_erase"
    )

    mappings["Encoder_Modes"] = dict(
        default_behaviour = ToggleBehaviour(return_to_default = True),
        volume_button = "volume",
        swing_button = "swing",
        #position_button = None,
        tempo_button = "tempo",
        #scale_button = None,
        default = dict(
            modes = [
                dict(component = "MiscControl",
                    select_track_encoder = "encoder",
                    exclusive_arm_button = "encoderpush",
                    arm_button = "encoderpush_with_shift"),
                dict(component = "Session_Navigation",
                    up_button = "encoderup",
                    down_button = "encoderdown",
                    left_button = "encoderleft",
                    right_button = "encoderright")]),
        volume = dict(
            component = "MasterVolume",
            coarse_volume = "encoder",
            fine_volume = "encoder_with_shift",
            reset_button = "encoderpush"),
        swing = dict(
            component = "GroovePool",
            coarse_groove_amount = "encoder",
            fine_groove_amount = "encoder_with_shift"),
        #position = dict(),
        tempo = dict(
            component = "Transport",
            tempo_coarse_encoder = "encoder",
            tempo_fine_encoder = "encoder_with_shift"),
        #scale = dict(),
    )
    
    mappings["TouchStrip_Modes"] = dict(
        default_behaviour = LatchingBehaviour(),
        pitch_button = "pitch",
        mod_button = "mod",
        perform_button = "perform",
        notes_button = "notes",
        pitch = dict(
            component = "MaschinePlayable",
            pitchbend_encoder = "touchstrip",
            pitchbend_reset = "touchstripcap"
        ),
        mod = dict(
            component = "MaschinePlayable",
            modulation_encoder = "touchstrip"
        ),
        perform = dict(
            component = "Mixer",
            crossfader_control = "touchstrip"
        ),
        notes = dict(
            component = "NoteRepeat",
            rate_selector = "touchstrip"
        )
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
                    stop_all_clips_button = "stop_with_scene",
                    stop_track_clip_buttons = "row3_pads_with_mute",
                    clip_launch_buttons = "pads",
                    scene_launch_buttons = "column3_pads_with_scene",
                    select_button = "select",
                    delete_button = "erase",
                    duplicate_button = "duplicate"),
                dict(component = "Session_Overview",
                    matrix = "group_buttons")
            ]),
        keyboard = dict(
            component = "MaschinePlayable",
            matrix = "pads",
            octave_select_buttons = "group_buttons",
            semitone_down_button = "row0_pads_with_shift_raw[0]",
            semitone_up_button = "row0_pads_with_shift_raw[1]",
            octave_down_button = "row0_pads_with_shift_raw[2]",
            octave_up_button = "row0_pads_with_shift_raw[3]",
            select_button = "select"
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
            delete_button = "erase"
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
            delete_button = "erase"
        ),
        chord = dict(
            component = "VelocityLevels",
            matrix = "pads"
        ),
        step = dict(
            component = "Step_Sequence",
            step_buttons = "pads",
            loop_buttons = "group_buttons"
        ),
    )
    #mappings["Session"] = dict(clip_launch_buttons = "pads")

    mappings["ButtonsAndKnobs_Modes"] = dict(
        default_behaviour = LatchingBehaviour(),
        default_button = "mixer",
        device_button = "plugin",
        default = dict(
            component = "Mixer",
            shift_button = "shift",
            pan_or_send_controls = "left_half_knobs",
            pan_controls = "left_half_knobs",
            volume_controls = "right_half_knobs",
            arm_buttons = "left_half_track_buttons",
            mute_buttons = "left_half_track_buttons_with_mute",
            solo_buttons = "left_half_track_buttons_with_solo",
            track_select_buttons = "right_half_track_buttons"),
        device = dict(
            modes = [
                dict(component = "Device",
                    parameter_controls = "knobs",
                    parameter_touch_controls = "knob_touch_buttons",
                    prev_bank_button = "left",
                    next_bank_button = "right",
                    bank_select_buttons = "track_buttons_with_macro",
                    # prev_device_button = "left_with_plugin",
                    # next_device_button = "right_with_plugin",
                    # quick_jump_buttons = "track_buttons"
                ),
                dict(component = "Device_Navigation",
                    device_select_buttons = "track_buttons",
                    device_on_off_buttons = "track_buttons_with_mute",
                    prev_group_button = "left_with_plugin",
                    next_group_button = "right_with_plugin"
                )
            ])
    )

    # mappings["MixerKnobs_Modes"] = dict(
    #     default_behaviour = ImmediateBehaviour(),
    #     default_button = "left",
    #     send_a_button = None,
    #     send_b_button = None,
    #     send_c_button = None,
    #     send_d_button = None,
    #     send_e_button = None,
    #     send_f_button = None,
    #     send_g_button = None,
    #     send_h_button = None,
    #     send_i_button = None,
    #     send_j_button = None,
    #     send_k_button = None,
    #     send_l_button = None,
    #     default = dict(
    #         component = "Mixer",
    #         pan_controls = "left_half_knobs"
    #     ),
    #     send_a = dict(),
    #     send_b = dict(),
    #     send_c = dict(),
    #     send_d = dict(),
    #     send_e = dict(),
    #     send_f = dict(),
    #     send_g = dict(),
    #     send_h = dict(),
    #     send_i = dict(),
    #     send_j = dict(),
    #     send_k = dict(),
    #     send_l = dict(),
    # )

    mappings["Device"] = dict(device_lock_button = "lock")

    mappings["View_Toggle"] = dict(
        main_view_toggle_button = "arranger",
        clip_view_toggle_button = "sampling",
        browser_view_toggle_button = "browser"
    )

    mappings["Undo_Redo"] = dict(
        undo_button = "row3_pads_with_shift_raw[0]",
        redo_button = "row3_pads_with_shift_raw[1]"
    )

    mappings["Clip_Actions"] = dict(
        quantize_button = "row2_pads_with_shift_raw[0]",
        half_quantize_button = "row2_pads_with_shift_raw[1]"
    )

    mappings["Accent"] = dict(
        accent_button = "fixedvel"
    )

    mappings["NoteRepeat"] = dict(
        repeat_button = "noterep"
    )

    # mapping names not found in component map are recognized as mode definition
    #mappings["Transport_Modes"] = dict()
    return mappings