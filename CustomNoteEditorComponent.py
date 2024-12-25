from faulthandler import is_enabled
from math import inf
from Live.Clip import MidiNoteSpecification # type: ignore
from ableton.v3.base import EventObject, clamp, depends, in_range, listenable_property, listens
from ableton.v3.control_surface.components.note_editor import DEFAULT_STEP_TRANSLATION_CHANNEL
from ableton.v3.live import liveobj_changed, liveobj_valid
from ableton.v3.control_surface import Component
from ableton.v3.control_surface.controls import ButtonControl, control_matrix
from ableton.v3.control_surface.skin import LiveObjSkinEntry

from ableton.v3.control_surface.components import NoteEditorComponent, StepSequenceComponent

class CustomStepSequenceComponent(StepSequenceComponent):
    def set_select_button(self, button):
        self._note_editor.select_button.set_control_element(button)

    def set_copy_button(self, button):
        self._loop_selector.set_copy_button(button)

class CustomNoteEditorComponent(NoteEditorComponent):
    select_button = ButtonControl(color = None)

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
        
    def _on_pad_released(self, pad, **k):
        if self.select_button.is_pressed:
            if self.is_enabled() and self._has_clip() and self._can_edit() and self._can_press_or_release_step(pad):
                row, column = pad.coordinate
                index = row * self.matrix.width + column
                visible_steps = self._visible_steps()
                step_notes = visible_steps[index].filter_notes(self._clip_notes)
                self._clip.select_notes_by_id([note.note_id for note in step_notes])
            k["can_add_or_remove"] = False
        
        super()._on_pad_released(pad, **k)
    
    @select_button.double_clicked
    def _on_select_button_double_clicked(self, button):
        if self.is_enabled() and self._has_clip() and self._can_edit():
            self._clip.deselect_all_notes()
