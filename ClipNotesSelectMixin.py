from ableton.v3.control_surface.component import Component
from ableton.v3.control_surface.controls import (
    ButtonControl,
    control_matrix
)
from ableton.v3.base import depends

from .Logger import logger

class ClipNotesSelectMixin():
    note_select_button = ButtonControl(color = None)

    _sequencer_clip = None
    _trigger_deselect = True

    @depends(sequencer_clip = None)
    def __init__(self, sequencer_clip = None, *a, **k):
        super().__init__(*a, **k)
        self._sequencer_clip = sequencer_clip

    def select_notes(self, pitch):
        clip = self._sequencer_clip.clip
        if clip != None:
            notes = clip.get_notes_extended(
                from_time = 0,
                from_pitch = pitch,
                time_span = clip.length,
                pitch_span = 1)
            
            note_ids = [note.note_id for note in notes]
            if self._trigger_deselect:
                clip.deselect_all_notes()
                self._trigger_deselect = False
            clip.select_notes_by_id(note_ids)

    @note_select_button.value
    def _on_note_select_button_changed(self, value, button):
        self._set_control_pads_from_script(button.is_pressed)
        if not button.is_pressed:
            self._trigger_deselect = True

    @note_select_button.double_clicked
    def _on_note_select_double_clicked(self, button):
        clip = self._sequencer_clip.clip
        if clip != None:
            clip.deselect_all_notes()

    def _set_control_pads_from_script(self, takeover_pads):
        super()._set_control_pads_from_script(takeover_pads or self.note_select_button.is_pressed)

    def process_pad_pressed(self, button):
        if self.note_select_button.is_pressed:
            pitch, _ = self._note_translation_for_button(button)
            self.select_notes(pitch)
    