# ==================================================
#
# This file is part of CustomMaschineMK3.
# CustomMaschineMK3 is free software licensed under GPL-3.0.
# For more details, see "LICENSE" file.
# 
# Copyright (C) 2024-2025 chiaki
#
# ==================================================

from faulthandler import is_enabled
from math import inf
from Live.Clip import MidiNoteSpecification, GridQuantization # type: ignore
from ableton.v3.base import EventObject, clamp, depends, in_range, listenable_property, listens
from ableton.v3.control_surface.components.note_editor import DEFAULT_STEP_TRANSLATION_CHANNEL
from ableton.v3.live import liveobj_changed, liveobj_valid
from ableton.v3.control_surface import Component
from ableton.v3.control_surface.controls import ButtonControl, control_matrix
from ableton.v3.control_surface.display import Renderable
from ableton.v3.control_surface.skin import LiveObjSkinEntry
from ableton.v3.control_surface.components import NoteEditorComponent, StepSequenceComponent

GRID_RESOLUTION_NAMES = {
    GridQuantization.g_thirtysecond: "1/32",
    GridQuantization.g_sixteenth: "1/16",
    GridQuantization.g_eighth: "1/8",
    GridQuantization.g_quarter: "1/4",
}

class CustomStepSequenceComponent(StepSequenceComponent, Renderable):
    def __init__(
            self,
            name = "Step_Sequence",
            note_editor_component_type = None,
            note_editor_paginator_type = None,
            loop_selector_component_type = None,
            playhead_component_type = None,
            playhead_notes = None,
            playhead_triplet_notes = None,
            playhead_channels = None, *a, **k):
        super().__init__(
            name = name,
            note_editor_component_type = note_editor_component_type,
            note_editor_paginator_type = note_editor_paginator_type,
            loop_selector_component_type = loop_selector_component_type,
            playhead_component_type = playhead_component_type,
            playhead_notes = playhead_notes,
            playhead_triplet_notes = playhead_triplet_notes,
            playhead_channels = playhead_channels, *a, **k)
        
        self.register_slot(self._grid_resolution, self._on_grid_resolution_changed, "index")

    def set_select_button(self, button):
        self._note_editor.select_button.set_control_element(button)

    def set_copy_button(self, button):
        self._loop_selector.set_copy_button(button)

    def _on_grid_resolution_changed(self):
        grid, triplet = self._grid_resolution.clip_grid
        self.notify(self.notifications.StepSequence.grid_resolution, GRID_RESOLUTION_NAMES[grid] + ("T" if triplet else ""))

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
