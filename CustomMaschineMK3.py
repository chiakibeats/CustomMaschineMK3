from functools import partial
from itertools import product
from time import sleep

from ableton.v3.base import lazy_attribute, const
from ableton.v3.live.util import liveobj_valid
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
    SessionComponent
)

from ableton.v3.control_surface.components.grid_resolution import GridResolution
from Live.Clip import GridQuantization # type: ignore

from ableton.v3.control_surface.elements import SimpleColor, RgbColor, create_rgb_color

from .ControlElements import ControlElements
from .Mappings import create_mappings
from .ColorSkin import MaschineSkin
from .DisplayDefinitions import (
    MaschineDisplay,
    make_mcu_display_header,
    make_display_sysex_message
)
from .GroovePoolComponent import GroovePoolComponent
from .MasterVolumeComponent import MasterVolumeComponent
from .MaschinePlayableComponent import MaschinePlayableComponent
from .CustomDrumGroupComponent import CustomDrumGroupComponent
from .MiscControlComponent import MiscControlComponent
from .CustomDeviceComponent import CustomDeviceComponent
from .CustomDeviceNavigationComponent import CustomDeviceNavigationComponent
from .CustomMixerComponent import CustomMixerComponent
from .CustomClipActionsComponent import CustomClipActionsComponent
from .CustomSlicedSimplerComponent import CustomSlicedSimplerComponent
from .NoteRepeatComponent import NoteRepeatComponent
from .VelocityLevelsComponent import VelocityLevelsComponent
from .ScaleSystemComponent import ScaleSystemComponent
from .SelectedParameterControlComponent import SelectedParameterControlComponent
from .CustomNoteEditorComponent import CustomNoteEditorComponent, CustomStepSequenceComponent
from .ClipEditorComponent import ClipEditorComponent

from .Logger import logger
from . import Config

pad_row_notes = list(range(60, 76, 4))[::-1]
playhead_notes = [base_note + offset for base_note, offset in product(pad_row_notes, range(4))]
triplet_playhead_notes = [base_note + offset for base_note, offset in product(pad_row_notes, range(3))]

class Specification(ControlSurfaceSpecification):
    elements_type = ControlElements
    control_surface_skin = MaschineSkin
    display_specification = MaschineDisplay if Config.LCD_ENABLED else None
    num_scenes = 4
    num_tracks = 4
    include_returns = True
    include_master = True
    include_auto_arming = True
    link_session_ring_to_track_selection = True
    link_session_ring_to_scene_selection = True
    continuous_parameter_sensitivity = 2.0
    quantized_parameter_sensitivity = 0.2
    identity_response_id_bytes = [0x00, 0x00, 0x00]
    create_mappings_function = create_mappings
    feedback_channels = [1]
    component_map = {
        "ClipEditor": ClipEditorComponent,
        "SelectedParameter": SelectedParameterControlComponent,
        "ScaleSystem": ScaleSystemComponent,
        "VelocityLevels": VelocityLevelsComponent,
        "NoteRepeat": NoteRepeatComponent,
        "Sliced_Simpler": CustomSlicedSimplerComponent,
        "Drum_Group": CustomDrumGroupComponent,
        "Mixer": CustomMixerComponent,
        "Clip_Actions": CustomClipActionsComponent,
        "GroovePool": GroovePoolComponent,
        "MasterVolume": MasterVolumeComponent,
        "MaschinePlayable": MaschinePlayableComponent,
        "MiscControl": MiscControlComponent,
        "Device_Navigation": CustomDeviceNavigationComponent,
        "Step_Sequence": partial(
            CustomStepSequenceComponent,
            note_editor_component_type = CustomNoteEditorComponent,
            playhead_notes = tuple(playhead_notes),
            playhead_triplet_notes = tuple(triplet_playhead_notes),
            playhead_channels = [1])
    }

Specification.component_map["Device"] = partial(
    CustomDeviceComponent,
    bank_definitions = Specification.parameter_bank_definitions,
    bank_size = Specification.parameter_bank_size,
    continuous_parameter_sensitivity = Specification.continuous_parameter_sensitivity,
    quantized_parameter_sensitivity = Specification.quantized_parameter_sensitivity)
    # ,bank_navigation_component_type=CustomDeviceBankNavigationComponent)


class BypassIdentification(IdentificationComponent):
    def request_identity(self):
        self.is_identified = True

DEFAULT_MODE = "default"
KEYBOARD_MODE = "keyboard"
DRUMRACK_MODE = "drum_rack"
SIMPLER_MODE = "simpler"

CUSTOM_GRID_RESOLUTIONS = (
    GridResolution("1/4", 1.0, GridQuantization.g_quarter, False),
    GridResolution("1/8", 0.5, GridQuantization.g_eighth, False),
    GridResolution("1/16", 0.25, GridQuantization.g_sixteenth, False),
    GridResolution("1/32", 0.125, GridQuantization.g_thirtysecond, False),
    GridResolution("1/4t", 0.6666666666666666, GridQuantization.g_quarter, True),
    GridResolution("1/8t", 0.3333333333333333, GridQuantization.g_eighth, True),
    GridResolution("1/16t", 0.16666666666666666, GridQuantization.g_sixteenth, True),
    GridResolution("1/32t", 0.08333333333333333, GridQuantization.g_thirtysecond, True),
)
GRID_DEFAULT_INDEX = 2


class CustomMaschineMK3(ControlSurface):
    _grid_resolution = None
    _sequencer_clip = None
    _pad_mode = None
    _step_sequencer = None
    _playable_mode_list = (KEYBOARD_MODE, DRUMRACK_MODE, SIMPLER_MODE)
    _provider_list = {
        KEYBOARD_MODE: "MaschinePlayable",
        DRUMRACK_MODE: "Drum_Group",
        SIMPLER_MODE: "Sliced_Simpler"
    }
    _current_drum_group = None
    _current_sliced_simpler = None

    def __init__(self, *a, **k):
        super().__init__(Specification, *a, **k)
        logger.info(dir(self._c_instance))
        self.register_slot(self.elements.channel, self._on_update_triggered, "is_pressed")
        self.register_slot(self.elements.keyboard, self._on_playable_mode_selected, "is_pressed")
        self.register_slot(self.component_map["Pad_Modes"], self._on_pad_mode_changed, "selected_mode")
        self.register_slot(self.component_map["ButtonsAndKnobs_Modes"], self._on_upper_section_mode_changed, "selected_mode")
    
    # Sometimes pad leds couldn't update correctly
    # I don't know why this happens now, push "CHANNEL" button for refresh state
    def _on_update_triggered(self):
        if self.elements.channel.is_pressed:
            logger.info("Display update triggered")
            self.update()

    def _do_send_midi(self, midi_event_bytes):
        logger.debug(f"_do_send_midi {midi_event_bytes}")
        super()._do_send_midi(midi_event_bytes)
        # Insert super short wait between each send to make sure LED feedback correctly.
        # During development, I encountered problem some pads / buttons LEDs not change to current mode value.
        # After several investigations, I found a wait inserted on old Maschine Ableton script.
        # Maybe 500us or more wait prevent issue.
        # This wait doesn't affect response speed, unless if you can play pads at 999 BPM...
        sleep(0.0005)

    # Session ring highlight is enabled only if hardware is identified by identity request
    # But maschine didn't respond to this message, so bypass identification process
    def _create_identification(self, specification):
        #return super()._create_identification(specification)
        identification = BypassIdentification(
            identity_request = specification.identity_request,
            identity_request_delay = specification.identity_request_delay,
            identity_response_id_bytes = specification.identity_response_id_bytes,
            custom_identity_response = specification.custom_identity_response)
        self._ControlSurface__on_is_identified_changed.subject = identification

        return identification

    @lazy_attribute
    def _create_grid_resolution(self):
        self._grid_resolution = GridResolutionComponent(resolutions = CUSTOM_GRID_RESOLUTIONS, default_index = GRID_DEFAULT_INDEX)
        return self._grid_resolution

    @lazy_attribute
    def _create_sequencer_clip(self):
        self._sequencer_clip = SequencerClip()
        return self._sequencer_clip
    
    def _get_knob_mapped_parameter(self, index):
        if index >= 0 and index < len(self.elements.knobs_raw):
            return self.elements.knobs_raw[index].mapped_parameter()

    def _get_additional_dependencies(self):
        # Register objects to DI container
        # Dict key name came from @depends decorator of each component classes
        # Registered components pass to appropriate components on demand
        inject_dict = {
            "grid_resolution": lambda: self._create_grid_resolution,
            "sequencer_clip": lambda: self._create_sequencer_clip,
            "note_repeat": const(self._c_instance.note_repeat),
            "velocity_levels": const(self._c_instance.velocity_levels),
            "get_knob_mapped_parameter": const(self._get_knob_mapped_parameter)
        }
        
        return inject_dict

    def setup(self):
        super().setup()
        self.set_can_auto_arm(True)
        with self.component_guard():
            self.component_map["Pad_Modes"].selected_mode = DEFAULT_MODE
            self.component_map["MaschinePlayable"].set_scale_system(self.component_map["ScaleSystem"])
            self.component_map["Step_Sequence"]._note_editor.set_velocity_levels(self.component_map["VelocityLevels"])

    def disconnect(self):
        super().disconnect()

        # Clear display
        for line in range(4):
            message = make_display_sysex_message(line, (ord(" "),) * 28)
            self._send_midi(message)

    def _on_playable_mode_selected(self):
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

    def _on_upper_section_mode_changed(self, component):
        mode = self.component_map["ButtonsAndKnobs_Modes"].selected_mode
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
        self.component_map["VelocityLevels"].set_pitch_provider(self.component_map[self._provider_list[mode]])

    def refresh_state(self):
        logger.info("Refresh state")
        super().refresh_state()

