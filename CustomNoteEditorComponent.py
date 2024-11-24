from math import inf
from Live.Clip import MidiNoteSpecification # type: ignore
from ableton.v3.base import EventObject, clamp, depends, in_range, listenable_property, listens
from ableton.v3.control_surface.components.note_editor import DEFAULT_STEP_TRANSLATION_CHANNEL
from ableton.v3.live import liveobj_changed, liveobj_valid
from ableton.v3.control_surface import Component
from ableton.v3.control_surface.controls import ButtonControl, control_matrix
from ableton.v3.control_surface.skin import LiveObjSkinEntry

from ableton.v3.control_surface.components import NoteEditorComponent

class CustomNoteEditorComponent(NoteEditorComponent):
    def __init__(self, name = "Note_Editor", *a, **k):
        super().__init__(name, *a, **k)