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
from time import sleep
import types

from ableton.v3.base import lazy_attribute, const, listens
from ableton.v3.live import liveobj_valid, scene_index
from ableton.v3.control_surface import (
    ControlSurface,
    ControlSurfaceSpecification,
    IdentificationComponent
)

from ableton.v3.control_surface.component import (
    Component
)

from ableton.v3.control_surface.display import DisplaySpecification

from ableton.v3.control_surface.components import (
    SessionRingComponent,
    PlayableComponent,
    NoteEditorComponent,
    NoteEditorPaginator,
    StepSequenceComponent,
    SequencerClip,
    GridResolutionComponent,
    SessionComponent,
    TargetTrackComponent,
    DEFAULT_SIMPLER_TRANSLATION_CHANNEL,
    DEFAULT_DRUM_TRANSLATION_CHANNEL
)

from ableton.v3.control_surface.components.grid_resolution import GridResolution
from Live.Clip import GridQuantization # type: ignore

from ableton.v3.control_surface.elements import SimpleColor, RgbColor, create_rgb_color

from .elements import ControlElements
from .mappings import create_mappings
from .skin import MaschineSkin
from .display import (
    MaschineDisplay,
    make_mcu_display_header,
    make_display_sysex_message
)
from .groove_pool import GroovePoolComponent
from .master_volume import MasterVolumeComponent
from .maschine_playable import MaschinePlayableComponent, DEFAULT_NOTE_TRANSLATION_CHANNEL
from .drum_group import CustomDrumGroupComponent
from .misc_control import MiscControlComponent
from .device import (
    CUSTOM_BANK_DEFINITIONS,
    CustomDeviceDecoratorFactory,
    CustomDeviceComponent
)
from .device_navigation import CustomDeviceNavigationComponent
from .mixer import CustomMixerComponent
from .maschine_mixer import MaschineMixerComponent
from .clip_actions import CustomClipActionsComponent
from .sliced_simpler import CustomSlicedSimplerComponent
from .note_repeat import NoteRepeatComponent
from .velocity_levels import VelocityLevelsComponent
from .scale_system import ScaleSystemComponent
from .selected_parameter_control import SelectedParameterControlComponent
from .note_editor import CustomNoteEditorComponent, CustomStepSequenceComponent
from .clip_editor import ClipEditorComponent
from .browser import BrowserComponent
from .recording import FixedLengthRecordingMethod, CustomViewBasedRecordingComponent
from .encoder_mode_control import EncoderModeControlComponent
from .group_button_mode_control import GroupButtonModeControlComponent
from .transport import CustomTransportComponent
from .settings import SettingsRepository, SettingsComponent
from .clip_slot import LEDBlinker, CustomClipSlotComponent
from .pageable_background import PageableBackgroundComponent

from .logger import logger
from . import config

# TODO: Reconsider is this modification matters or not.
class CustomTargetTrackComponent(TargetTrackComponent):
    """
    TargetTrackComponent with custom behaviour.

    When the selected track was changed in the session view, TargetTrackComponent update the target clip.
    Target clip is the property of which clip is focused on.
    It is referenced from various components like step sequencer, clip editor, and clip manipulation mix-in.

    The original version always selects playing clip in the clip slots, that is a bit confusing.

    This version selects the clip based on selected scene index to match the selection of Live's UI.
    """
    def _target_clip_from_session(self):
        slot_index = scene_index()
        if slot_index < len(self._target_track.clip_slots):
            clip_slot = self._target_track.clip_slots[slot_index]
        else:
            clip_slot = None

        self._on_clip_slot_state_changed.subject = clip_slot
        if clip_slot:
            if clip_slot.has_clip:
                return clip_slot.clip
    
    @listens("has_clip")
    def _on_clip_slot_state_changed(self):
        self._update_target_clip()


class Specification(ControlSurfaceSpecification):
    """
    Collection of control surface characteristics.
    """
    elements_type = ControlElements
    """Class name of the repository of elements (MIDI button / knob representation)."""
    control_surface_skin = MaschineSkin
    """Instance of `Skin` class, that contains a definition of LED feedback."""
    display_specification = MaschineDisplay if config.LCD_ENABLED else None
    """Instance of `DisplaySpecification` class, that contains procedures of composing views."""
    num_scenes = 4
    """Height of the session box."""
    num_tracks = 4
    """Width of the session box."""
    include_returns = True
    """If the session box can intersect with return tracks, set to `True`."""
    include_master = True
    """If the session box can intersect with the master track, set to `True`."""
    include_auto_arming = True
    """Related to auto arm, but it seems to be not used."""
    target_track_component_type = CustomTargetTrackComponent
    """Class that manages the behaviour of selecting and changing the target track."""
    continuous_parameter_sensitivity = 2.0
    """Continuous parameter sensitivity (e.g. filter frequency, delay feedback)."""
    quantized_parameter_sensitivity = 0.2
    """Quantized parameter sensitivity (e.g. filter type, delay length in beats)."""
    identity_response_id_bytes = [0x00, 0x00, 0x00]
    """
    Response data of identification process.

    This process is usually done by sending MIDI identity request of the MIDI specification.
    Unfortunately, maschine controllers don't respond to this message, so it's just a placeholder.
    
    Note: You can use custom identification process by changing `identity_request` and `custom_identity_response` value.
    """
    create_mappings_function = create_mappings
    """Function to build mappings between components and control elements."""
    recording_method_type = FixedLengthRecordingMethod
    """Class that manages behaviour of the recording mode in session view."""
    feedback_channels = [DEFAULT_NOTE_TRANSLATION_CHANNEL, DEFAULT_SIMPLER_TRANSLATION_CHANNEL, DEFAULT_DRUM_TRANSLATION_CHANNEL]
    """MIDI channels used in playing note feedback."""
    component_map = {
        "Pageable_Background": PageableBackgroundComponent,
        "Settings": SettingsComponent,
        "Transport": CustomTransportComponent,
        "Session": partial(SessionComponent, clip_slot_component_type = CustomClipSlotComponent),
        "Encoder_Mode_Control": EncoderModeControlComponent,
        "Group_Button_Mode_Control": GroupButtonModeControlComponent,
        "View_Based_Recording": partial(CustomViewBasedRecordingComponent, recording_method_type = recording_method_type),
        "Browser": BrowserComponent,
        "Clip_Editor": ClipEditorComponent,
        "Selected_Parameter": SelectedParameterControlComponent,
        "Scale_System": ScaleSystemComponent,
        "Velocity_Levels": VelocityLevelsComponent,
        "Note_Repeat": NoteRepeatComponent,
        "Sliced_Simpler": CustomSlicedSimplerComponent,
        "Drum_Group": CustomDrumGroupComponent,
        "Clip_Actions": CustomClipActionsComponent,
        "Groove_Pool": GroovePoolComponent,
        "Master_Volume": MasterVolumeComponent,
        "Maschine_Playable": MaschinePlayableComponent,
        "Misc_Control": MiscControlComponent,
        "Device_Navigation": CustomDeviceNavigationComponent,
        # TODO: Bring custom component initializations into this class.
    }
    """
    List of components used at control surface.

    Each key value must be equal to a name specified in component's constructor.
    """
    parameter_bank_definitions = CUSTOM_BANK_DEFINITIONS
    """Parameter bank definitions used at DeviceComponent."""

DEFAULT_MODE = "default"
KEYBOARD_MODE = "keyboard"
DRUMRACK_MODE = "drum_rack"
SIMPLER_MODE = "simpler"

CUSTOM_GRID_RESOLUTIONS = (
    GridResolution("1/4", 1.0, GridQuantization.g_quarter, False),
    GridResolution("1/4t", 0.6666666666666666, GridQuantization.g_quarter, True),
    GridResolution("1/8", 0.5, GridQuantization.g_eighth, False),
    GridResolution("1/8t", 0.3333333333333333, GridQuantization.g_eighth, True),
    GridResolution("1/16", 0.25, GridQuantization.g_sixteenth, False),
#    GridResolution("1/16t", 0.16666666666666666, GridQuantization.g_sixteenth, True),
#    GridResolution("1/32", 0.125, GridQuantization.g_thirtysecond, False),
#    GridResolution("1/32t", 0.08333333333333333, GridQuantization.g_thirtysecond, True),
)
GRID_DEFAULT_INDEX = 4 # 1/16

class CustomMaschineBase(ControlSurface):
    """
    Base class of all Maschine control surfaces.
    """
    _grid_resolution = None
    _sequencer_clip = None
    _pad_mode = None
    _step_sequencer = None
    _playable_mode_list = (KEYBOARD_MODE, DRUMRACK_MODE, SIMPLER_MODE)
    _provider_list = {
        KEYBOARD_MODE: "Maschine_Playable",
        DRUMRACK_MODE: "Drum_Group",
        SIMPLER_MODE: "Sliced_Simpler"
    }
    _current_drum_group = None
    _current_sliced_simpler = None
    _display_mode = None
    _settings = None

    def __init__(self, *a, **k):
        """
        Args:
            c_instance: (Keyword argument) Special object came from Live app.
        """
        # Settings must be loaded before initialization
        self._settings = SettingsRepository()
        self._init_specification()
        super().__init__(Specification, *a, **k)
        #logger.info(dir(self._c_instance))

        #self.register_slot(self.elements.variation, self._on_update_triggered, "is_pressed")
        self.register_slot(self.elements.keyboard, self._on_playable_mode_selected, "is_pressed")
        self.register_slot(self.component_map["Pad_Modes"], self._on_pad_mode_changed, "selected_mode")
        self.register_slot(self.component_map["Display_Modes"], self._on_display_mode_changed, "selected_mode")
    
    def _init_specification(self):
        """
        Add components to `Specification` class according to setting value.
        """
        Specification.component_map["Device"] = partial(
            CustomDeviceComponent,
            device_decorator_factory = CustomDeviceDecoratorFactory(),
            bank_definitions = Specification.parameter_bank_definitions,
            bank_size = Specification.parameter_bank_size,
            continuous_parameter_sensitivity = Specification.continuous_parameter_sensitivity,
            quantized_parameter_sensitivity = Specification.quantized_parameter_sensitivity)

        pad_row_notes = list(range(60, 76, 4))
        if self._settings.get_value("sequencer_style") == "Push":
            pad_row_notes = pad_row_notes[::-1]
        playhead_notes = [base_note + offset for base_note, offset in product(pad_row_notes, range(4))]
        triplet_playhead_notes = [base_note + offset for base_note, offset in product(pad_row_notes, range(3))]

        Specification.component_map["Step_Sequence"] = partial(
            CustomStepSequenceComponent,
            note_editor_component_type = CustomNoteEditorComponent,
            playhead_notes = tuple(playhead_notes),
            playhead_triplet_notes = tuple(triplet_playhead_notes),
            playhead_channels = [1])
        
        mixer_mode = self._settings.get_value("mixer_mode")
        if mixer_mode == "4Track":
            mixer_component = CustomMixerComponent
        elif mixer_mode == "8Track":
            mixer_component = MaschineMixerComponent

        Specification.component_map["Mixer"] = mixer_component

    def _on_update_triggered(self):
        """
        Refresh all LED states & component states.

        It takes long time because of recursive process.
        """
        if self.elements.variation.is_pressed:
            logger.info("Display update triggered")
            self.refresh_state()

    def _do_send_midi(self, midi_event_bytes):
        logger.debug(f"_do_send_midi {midi_event_bytes}")
        super()._do_send_midi(midi_event_bytes)
        # Insert super short wait between each send to make sure LED feedback correctly
        # During development, I encountered problem some pads / buttons LEDs not change to current mode value
        # After several investigations, I found a wait inserted on old Maschine Ableton script
        # Maybe 500us or more wait prevents issue.
        # This wait doesn't affect response speed, unless if you can play pads at 999 BPM...
        sleep(0.0005)

    def _create_identification(self, specification):
        """
        Create `IdentificationComponent` and do some patching to disable identification.
        
        Live's session box appears only when the identification process succeeded.
        But Maschine doesn't respond to sysex identification request, so I made it bypassed.
        """

        def bypass_request_identity(self):
            logger.info("Request identity")
            # Toggle the flag to notify being identified to Live.
            self.is_identified = False
            sleep(0.01)
            self.is_identified = True

        identification = super()._create_identification(specification)
        identification.request_identity = types.MethodType(bypass_request_identity, identification)

        return identification

    # lazy_attribute means the function will be called only once, and its return value is cached for subsequent calls.
    @lazy_attribute
    def _create_grid_resolution(self):
        self._grid_resolution = GridResolutionComponent(resolutions = CUSTOM_GRID_RESOLUTIONS, default_index = GRID_DEFAULT_INDEX)
        self._grid_resolution.resolution_buttons.control_count = len(CUSTOM_GRID_RESOLUTIONS)
        return self._grid_resolution

    @lazy_attribute
    def _create_sequencer_clip(self):
        self._sequencer_clip = SequencerClip()
        return self._sequencer_clip
        
    @lazy_attribute
    def _create_blinker(self):
        self._blinker = LEDBlinker()
        return self._blinker
    
    def _get_knob_mapped_parameter(self, index):
        """
        Return `DeviceParameter` object mapped to Maschine's 8x knobs.

        Args:
            index(int): Index of knob.
        
        Returns:
            DeviceParameter | None: A parameter currently mapped to specified knob, or `None` if no parameter is mapped.
        """
        if index >= 0 and index < len(self.elements.knobs_raw):
            return self.elements.knobs_raw[index].mapped_parameter()

    def _get_additional_dependencies(self):
        """
        Create additional objects for DI container.
        
        V3 API has a dependency injection mechanism.
        Each object instance has a specific name.
        Other components can use them by add `@depends` decorator at `__init__` method of components.
        """
        # There's no documentation of this method, probably overriding is a proper way to use. 
        inject_dict = {
            "grid_resolution": lambda: self._create_grid_resolution,
            "sequencer_clip": lambda: self._create_sequencer_clip,
            "note_repeat": const(self._c_instance.note_repeat),
            "velocity_levels": const(self._c_instance.velocity_levels),
            "get_knob_mapped_parameter": const(self._get_knob_mapped_parameter),
            "settings": const(self._settings),
            "blinker": lambda: self._create_blinker,
        }
        
        return inject_dict

    def setup(self):
        """
        Setup components.

        This function is called inside `ControlSurface.__init__()`.
        """
        super().setup()
        # This enables pad note feedback
        self.set_can_update_controlled_track(True)
        self.set_can_auto_arm(True)
        # Connect components
        with self.component_guard():
            self.component_map["Pad_Modes"].selected_mode = DEFAULT_MODE
            self.component_map["Maschine_Playable"].set_scale_system(self.component_map["Scale_System"])
            self.component_map["Step_Sequence"]._note_editor.set_velocity_levels(self.component_map["Velocity_Levels"])
            self.component_map["Clip_Editor"].set_step_sequence(self.component_map["Step_Sequence"])
            encoder_mode_control = self.component_map["Encoder_Mode_Control"]
            encoder_mode_control.set_encoder_modes(self.component_map["Encoder_Modes"])
            display_mode = self.component_map["Display_Modes"]
            encoder_mode_control.set_display_modes(display_mode)
            self.component_map["Browser"].set_display_modes(display_mode)
            group_button_control = self.component_map["Group_Button_Mode_Control"]
            group_button_control.set_pad_modes(self.component_map["Pad_Modes"])
            group_button_control.set_group_button_modes(self.component_map["Group_Button_Modes"])
            self.component_map["Note_Repeat"].set_group_button_control(group_button_control)

    def disconnect(self):
        """
        Perform cleanup.

        This function is called when the control surface is about to dispose.
        After `disconnect` method of super class was called, all components and control elements are disposed.
        """
        super().disconnect()

        # Save settings
        self._settings.save()

        # Clear display
        for line in range(4):
            message = make_display_sysex_message(line, (ord(" "),) * 28)
            self._send_midi(message)
        
        # Clear touchstrip
        self._send_midi((0xE0, 0x00, 0x00))

    def _on_playable_mode_selected(self):
        """
        Dispatch a suitable mode according to the instrument on the device chain.
        """
        logger.info(f"keyboard button state = {self.elements.keyboard.is_pressed}")
        if self.elements.keyboard.is_pressed:
            with self.component_guard():
                if liveobj_valid(self._current_drum_group):
                    self._select_playable_mode(DRUMRACK_MODE)
                elif liveobj_valid(self._current_sliced_simpler):
                    self._select_playable_mode(SIMPLER_MODE)
                else:
                    self._select_playable_mode(KEYBOARD_MODE)

    def _on_pad_mode_changed(self, component):
        is_playable_enabled = self.get_pad_mode() in self._playable_mode_list
        state = "On" if is_playable_enabled else "Off"
        self.elements.keyboard.send_value(MaschineSkin[f"DefaultButton.{state}"].midi_value)

    def _on_display_mode_changed(self, component):
        """
        Perform actions associated with mode changes of upper half of the Maschine controller.
        """
        mode = self.component_map["Display_Modes"].selected_mode
        if self._display_mode == "custom":
            self._refresh_track_buttons_state(mode)
            # self._refresh_task = self._tasks.add(task.sequence(task.wait(0.1), task.run(lambda: self._refresh_upper_button_state(mode))))
        self._display_mode = mode
        if mode == "default":
            return
        elif mode == "device":
            target_view = "Detail/DeviceChain"
        elif mode == "clip":
            target_view = "Detail/Clip"
        else:
            return
        
        if not self.application.view.is_view_visible(target_view):
            self.application.view.show_view(target_view)

        self.application.view.focus_view(target_view)

    def _refresh_track_buttons_state(self, mode):
        """
        Triggering update manually to sync LED state.
        
        LED state sync failure happens when the display mode switched from the MIDI mapping mode to an another mode.
        It only refreshes newly selected mode to avoid frequently update.
        """
        logger.info("Trigger upper button state update")

        with self.component_guard():
            for button in self.elements.track_buttons_raw:
                button.clear_send_cache()

            if mode == "default":
                self.component_map["Mixer"].update()
            elif mode == "device":
                self.component_map["Device_Navigation"].update()
            elif mode == "clip":
                self.component_map["Clip_Editor"].update()
            elif mode == "browser":
                self.component_map["Browser"].update()
            elif mode == "settings":
                self.component_map["Settings"].update()

    def drum_group_changed(self, drum_group):
        logger.info(f"Drum Group = {drum_group}")
        self._current_drum_group = drum_group

        with self.component_guard():
            update_mode = self.get_pad_mode() in self._playable_mode_list
            if liveobj_valid(drum_group):
                self._select_playable_mode(DRUMRACK_MODE, update_mode)
            elif not liveobj_valid(self._current_sliced_simpler):
                self._select_playable_mode(KEYBOARD_MODE, update_mode)

    def sliced_simpler_changed(self, sliced_simpler):
        logger.info(f"Simpler = {sliced_simpler}")
        self._current_sliced_simpler = sliced_simpler
        
        with self.component_guard():
            update_mode = self.get_pad_mode() in self._playable_mode_list
            if liveobj_valid(sliced_simpler):
                self._select_playable_mode(SIMPLER_MODE, update_mode)
            elif not liveobj_valid(self._current_drum_group):
                self._select_playable_mode(KEYBOARD_MODE, update_mode)
    
    def get_pad_mode(self):
        return self.component_map["Pad_Modes"].selected_mode

    def _select_playable_mode(self, mode, update_mode = True):
        if update_mode:
            self.component_map["Pad_Modes"].selected_mode = mode
        self.component_map["Step_Sequence"].set_pitch_provider(self.component_map[self._provider_list[mode]])
        self.component_map["Velocity_Levels"].set_pitch_provider(self.component_map[self._provider_list[mode]])

    def refresh_state(self):
        logger.info("Refresh state")
        super().refresh_state()
