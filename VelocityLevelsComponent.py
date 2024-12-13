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



class VelocityLevelsComponent(PlayableComponent):
    _pitch_provider = None
    _target_track = None
    _velocity_levels = None
    _source_notes = list(range(60, 76))
    # Simulate Live's internal velocity calculation
    _levels = list(range(127, 0, -8))[::-1]
    _selected_level = 0
    _selected_coordinate = (-1, -1)

    @property
    def selected_velocity(self):
        return self._selected_level

    @depends(velocity_levels = None, target_track = None)
    def __init__(self, name = "Velocity_Levels", matrix_always_listenable = True, velocity_levels = None, target_track = None, *a, **k):
        super().__init__(name, matrix_always_listenable, *a, **k)
        self._velocity_levels = velocity_levels
        self._on_played_level_changed.subject = self._velocity_levels
        self._selected_level = self._levels[12]
        self._selected_coordinate = (0, 0)
        self._target_track = target_track
        self._on_target_track_changed.subject = self._target_track
        self._on_target_track_changed()
        self.register_slot(self.select_button, self._on_select_button_pressed, "is_pressed")

    def set_pitch_provider(self, provider):
        self._pitch_provider = provider
        self._on_pitches_changed.subject = self._pitch_provider

    def _note_translation_for_button(self, button):
        return super()._note_translation_for_button(button)
    
    def set_matrix(self, matrix):
        super().set_matrix(matrix)
        if matrix != None:
            logger.info("Velocity levels mode enabled")
            self._velocity_levels.enabled = True
        else:
            logger.info("Velocity levels mode disabled")
            self._velocity_levels.enabled = False

    def _on_matrix_pressed(self, button):
        self._selected_coordinate = button.coordinate
        row, column = button.coordinate
        index = (self.height - row - 1) * self.matrix.width + column
        if len(self._velocity_levels.levels) > 0:
            self._selected_level = self._velocity_levels.levels[index]
        else:
            self._selected_level = self._levels[index]

    def _on_select_button_pressed(self):
        self._update_led_feedback()

    def update(self):
        super().update()
        self._velocity_levels.enabled = self.is_enabled()
        if self._pitch_provider != None:
            self._on_pitches_changed(self._pitch_provider.pitches)
        else:
            self._velocity_levels.target_note = DEFAULT_NOTE
        self._velocity_levels.target_channel = 1
        self._velocity_levels.source_channel = 0
        self._velocity_levels.notes = self._source_notes

    def _update_button_color(self, button):
        row, column = button.coordinate
        level = self.height - row

        if self.select_button.is_pressed and button.coordinate == self._selected_coordinate:
            color_name = "VelocityLevels.Selected"
        else:
            color_name = f"VelocityLevels.Level{level}"

        button.color = LiveObjSkinEntry(color_name, self._target_track.target_track)
        button.pressed_color = LiveObjSkinEntry("VelocityLevels.Pressed", self._target_track.target_track)

    @listens("pitches")
    def _on_pitches_changed(self, pitches):
        pitches = self._pitch_provider.pitches
        self._velocity_levels.target_note = pitches[0] if len(pitches) > 0 else DEFAULT_NOTE

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
