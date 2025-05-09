# ==================================================
#
# This file is part of CustomMaschineMK3.
# CustomMaschineMK3 is free software licensed under GPL-3.0.
# For more details, see "LICENSE" file.
# 
# Copyright (C) 2024-2025 chiaki
#
# ==================================================

from itertools import product
from ableton.v3.control_surface.components import (
    PlayableComponent,
    ScrollComponent,
    Scrollable,
    PitchProvider
)
from ableton.v3.control_surface.display import Renderable
from ableton.v3.control_surface.controls import (
    ButtonControl,
    EncoderControl,
    TouchControl,
    MappedControl,
    SendValueInputControl,
    SendValueEncoderControl,
    PlayableControl,
    control_matrix
)
from ableton.v3.control_surface.skin import LiveObjSkinEntry
from ableton.v3.base import depends, listens

from .Logger import logger

DEFAULT_NOTE = 60
# Simulate Live's internal velocity calculation
# Levels list in velocity level object is sometimes unavailable
VELOCITY_LEVELS = list(range(127, 0, -8))[::-1]
DEFAULT_LEVEL_INDEX = 12

class VelocityLevelsComponent(PlayableComponent, Renderable):
    _pitch_provider = None
    _target_track = None
    _velocity_levels = None
    _source_notes = list(range(60, 76))
    _selected_level = 0
    _enabled = False

    @property
    def selected_velocity(self):
        return self._selected_level

    @depends(velocity_levels = None, target_track = None)
    def __init__(self, name = "Velocity_Levels", matrix_always_listenable = True, velocity_levels = None, target_track = None, *a, **k):
        super().__init__(name, matrix_always_listenable, *a, **k)
        self._velocity_levels = velocity_levels
        self._on_played_level_changed.subject = self._velocity_levels
        self._select_velocity_level(DEFAULT_LEVEL_INDEX)
        self._selected_level = VELOCITY_LEVELS[DEFAULT_LEVEL_INDEX]
        self._selected_index = DEFAULT_LEVEL_INDEX
        self._target_track = target_track
        self._on_target_track_changed.subject = self._target_track
        self._on_target_track_changed()
        self.register_slot(self.select_button, self._on_select_button_pressed, "is_pressed")

    def set_pitch_provider(self, provider):
        self._pitch_provider = provider
        self._on_pitches_changed.subject = self._pitch_provider

    def _select_velocity_level(self, index):
        if len(self._velocity_levels.levels) > 0:
            self._selected_level = int(self._velocity_levels.levels[index])
        else:
            self._selected_level = VELOCITY_LEVELS[index]
        self._selected_index = index

    def _note_translation_for_button(self, button):
        return super()._note_translation_for_button(button)
    
    def set_matrix(self, matrix):
        logger.info(f"matrix = {matrix}")
        super().set_matrix(matrix)
        self._enabled = matrix != None
        self._update_velocity_levels_state()

    def _on_matrix_pressed(self, button):
        row, column = button.coordinate
        index = (self.height - row - 1) * self.matrix.width + column
        self._select_velocity_level(index)

        if self.select_button.is_pressed:
            self.notify(self.notifications.VelocityLevels.select, self._selected_level)

    def _on_select_button_pressed(self):
        self._update_led_feedback()

    def update(self):
        super().update()
        self._update_velocity_levels_state()

    def _update_button_color(self, button):
        row, column = button.coordinate
        level = self.matrix.height - row
        index = (level - 1) * self.matrix.width + column

        if self.select_button.is_pressed and index == self._selected_index:
            color_name = "VelocityLevels.Selected"
        else:
            color_name = f"VelocityLevels.Level{level}"

        button.color = LiveObjSkinEntry(color_name, self._target_track.target_track)
        button.pressed_color = LiveObjSkinEntry("VelocityLevels.Pressed", self._target_track.target_track)

    def _update_velocity_levels_state(self):
        self._velocity_levels.enabled = self._enabled
        pitch = self._pitch_provider.pitches[0] if len(self._pitch_provider.pitches) else DEFAULT_NOTE
        self._velocity_levels.target_note = pitch
        self._velocity_levels.target_channel = 1
        self._velocity_levels.source_channel = 0
        self._velocity_levels.notes = self._source_notes
        logger.info(f"Fixed velocity state = {self._velocity_levels.enabled}, note = {self._velocity_levels.target_note}")

    @listens("pitches")
    def _on_pitches_changed(self, pitches):
        pitch = pitches[0] if len(pitches) else DEFAULT_NOTE
        logger.info(f"Selected note = {pitch}")
        if self._velocity_levels.target_note != pitch:
            # Reset velocity level if target note is changed
            self._select_velocity_level(DEFAULT_LEVEL_INDEX)
        self._update_velocity_levels_state()

    @listens("target_track")
    def _on_target_track_changed(self):
        self._on_track_color_changed.subject = self._target_track.target_track
        self._update_led_feedback()

    @listens("color_index")
    def _on_track_color_changed(self):
        self._update_led_feedback()

    @listens("last_played_level")
    def _on_played_level_changed(self):
        self._selected_level = self._velocity_levels.last_played_level
