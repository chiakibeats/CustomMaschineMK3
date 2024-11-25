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
    _velocity_levels = None

    def __init__(self, name = "Note_Editor", *a, **k):
        super().__init__(name, *a, **k)

    def set_velocity_levels(self, velocity_levels):
        self._velocity_levels = velocity_levels

    def _add_new_note_in_step(self, pitch, time):
        #return super()._add_new_note_in_step(pitch, time)
        velocity = 127 if self._full_velocity.enabled else self._get_current_velocity()
        note = MidiNoteSpecification(
            pitch = pitch,
            start_time = time,
            duration = self.step_length,
            velocity = velocity,
            mute = False)
        self._clip.add_new_notes((note,))
        self._clip.deselect_all_notes()

    def _get_current_velocity(self):
        if self._velocity_levels != None:
            return self._velocity_levels.selected_velocity
        else:
            return 100
