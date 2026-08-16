from functools import partial
from itertools import product

from custom_maschine.control_surface import CustomMaschineBaseSpec, CustomTargetTrackComponent
from custom_maschine.display import MaschineDisplay
from custom_maschine.skin import MaschineSkin

from .elements import ControlElements
from .mappings import create_mappings

from custom_maschine.groove_pool import GroovePoolComponent
from custom_maschine.master_volume import MasterVolumeComponent
from custom_maschine.maschine_playable import MaschinePlayableComponent, DEFAULT_NOTE_TRANSLATION_CHANNEL
from custom_maschine.drum_group import CustomDrumGroupComponent
from custom_maschine.misc_control import MiscControlComponent
from custom_maschine.device import (
    CUSTOM_BANK_DEFINITIONS,
    CustomDeviceDecoratorFactory,
    CustomDeviceComponent
)
from custom_maschine.device_navigation import CustomDeviceNavigationComponent
from custom_maschine.mixer import CustomMixerComponent
from custom_maschine.maschine_mixer import MaschineMixerComponent
from custom_maschine.clip_actions import CustomClipActionsComponent
from custom_maschine.sliced_simpler import CustomSlicedSimplerComponent
from custom_maschine.note_repeat import NoteRepeatComponent
from custom_maschine.velocity_levels import VelocityLevelsComponent
from custom_maschine.scale_system import ScaleSystemComponent
from custom_maschine.touchstrip_parameter_control import TouchStripParameterControlComponent
from custom_maschine.note_editor import CustomNoteEditorComponent, CustomStepSequenceComponent
from custom_maschine.clip_editor import ClipEditorComponent
from custom_maschine.browser import BrowserComponent
from custom_maschine.recording import FixedLengthRecordingMethod, CustomViewBasedRecordingComponent
from custom_maschine.encoder_mode_control import EncoderModeControlComponent
from custom_maschine.group_button_mode_control import GroupButtonModeControlComponent
from custom_maschine.transport import CustomTransportComponent
from custom_maschine.settings import SettingsComponent
from custom_maschine.clip_slot import CustomClipSlotComponent
from custom_maschine.pageable_background import PageableBackgroundComponent

from custom_maschine.util import REPEAT_RATE_KEYS

from ableton.v3.control_surface.components import (
    SessionComponent,
    DEFAULT_SIMPLER_TRANSLATION_CHANNEL,
    DEFAULT_DRUM_TRANSLATION_CHANNEL
)

SCHEMA = [
    {
        "key": "automatic_selector_switching",
        "description": "Automatic Rate Selector Switching",
        "type": "bool",
        "default_value": False,
    },
    {
        "key": "repeat_rate_a",
        "description": "Note Repeat Rate A",
        "type": "enum",
        "default_value": "1/4",
        "enum": REPEAT_RATE_KEYS,
    },
    {
        "key": "repeat_rate_b",
        "description": "Note Repeat Rate B",
        "type": "enum",
        "default_value": "1/8",
        "enum": REPEAT_RATE_KEYS,
    },
    {
        "key": "repeat_rate_c",
        "description": "Note Repeat Rate C",
        "type": "enum",
        "default_value": "1/16",
        "enum": REPEAT_RATE_KEYS,
    },
    {
        "key": "repeat_rate_d",
        "description": "Note Repeat Rate D",
        "type": "enum",
        "default_value": "1/32",
        "enum": REPEAT_RATE_KEYS,
    },
    {
        "key": "repeat_rate_e",
        "description": "Note Repeat Rate E",
        "type": "enum",
        "default_value": "1/4T",
        "enum": REPEAT_RATE_KEYS,
    },
    {
        "key": "repeat_rate_f",
        "description": "Note Repeat Rate F",
        "type": "enum",
        "default_value": "1/8T",
        "enum": REPEAT_RATE_KEYS,
    },
    {
        "key": "repeat_rate_g",
        "description": "Note Repeat Rate G",
        "type": "enum",
        "default_value": "1/16T",
        "enum": REPEAT_RATE_KEYS,
    },
    {
        "key": "repeat_rate_h",
        "description": "Note Repeat Rate H",
        "type": "enum",
        "default_value": "1/32T",
        "enum": REPEAT_RATE_KEYS,
    },
    {
        "key": "sequencer_style",
        "description": "Sequencer Style (Reload required)",
        "type": "enum",
        "default_value": "Maschine",
        "enum": ["Maschine", "Push"]
    },
    {
        "key": "mixer_mode",
        "description": "Mixer Mode (Reload required)",
        "type": "enum",
        "default_value": "8Track",
        "enum": ["8Track", "4Track"]
    },
    {
        "key": "__version",
        "description": "CustomMaschineMK3 by chiaki",
        "type": "none",
        "default_value": "Version 1.4",
    },    
]

class CustomMaschineMK3Spec(CustomMaschineBaseSpec):
    elements_type = ControlElements
    control_surface_skin = MaschineSkin
    display_specification = MaschineDisplay
    num_scenes = 4
    num_tracks = 4
    include_returns = True
    include_master = True
    include_auto_arming = True
    target_track_component_type = CustomTargetTrackComponent
    continuous_parameter_sensitivity = 2.0
    quantized_parameter_sensitivity = 0.2
    identity_response_id_bytes = [0x00, 0x00, 0x00]
    create_mappings_function = create_mappings
    recording_method_type = FixedLengthRecordingMethod
    feedback_channels = [DEFAULT_NOTE_TRANSLATION_CHANNEL, DEFAULT_SIMPLER_TRANSLATION_CHANNEL, DEFAULT_DRUM_TRANSLATION_CHANNEL]
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
        "TouchStrip_Parameter": TouchStripParameterControlComponent,
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
    }
    """
    List of components used at control surface.

    Each key value must be equal to a name specified in component's constructor.
    """
    parameter_bank_definitions = CUSTOM_BANK_DEFINITIONS

def init_specification(settings):
    """
    Configure specification class according to setting value.

    Args:
        settings(SettingsRepository): Settings respository.
    """
    spec = CustomMaschineMK3Spec
    spec.settings_repository = settings
    spec.component_map["Device"] = partial(
        CustomDeviceComponent,
        device_decorator_factory = CustomDeviceDecoratorFactory(),
        bank_definitions = spec.parameter_bank_definitions,
        bank_size = spec.parameter_bank_size,
        continuous_parameter_sensitivity = spec.continuous_parameter_sensitivity,
        quantized_parameter_sensitivity = spec.quantized_parameter_sensitivity)

    pad_row_notes = list(range(60, 76, 4))
    if settings.get_value("sequencer_style") == "Push":
        pad_row_notes = pad_row_notes[::-1]
    playhead_notes = [base_note + offset for base_note, offset in product(pad_row_notes, range(4))]
    triplet_playhead_notes = [base_note + offset for base_note, offset in product(pad_row_notes, range(3))]

    spec.component_map["Step_Sequence"] = partial(
        CustomStepSequenceComponent,
        note_editor_component_type = CustomNoteEditorComponent,
        playhead_notes = tuple(playhead_notes),
        playhead_triplet_notes = tuple(triplet_playhead_notes),
        playhead_channels = [1])
    
    mixer_mode = settings.get_value("mixer_mode")
    if mixer_mode == "4Track":
        mixer_component = CustomMixerComponent
    elif mixer_mode == "8Track":
        mixer_component = MaschineMixerComponent

    spec.component_map["Mixer"] = mixer_component
