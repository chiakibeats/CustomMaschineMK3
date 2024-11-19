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

    @depends(velocity_levels = None, target_track = None)
    def __init__(self, name = "VelocityLevels", matrix_always_listenable = True, velocity_levels = None, target_track = None, *a, **k):
        super().__init__(name, matrix_always_listenable, *a, **k)
        self._velocity_levels = velocity_levels
        self._target_track = target_track
        self._on_target_track_changed.subject = self._target_track

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
        #super()._on_matrix_pressed(button)
        pass

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

        button.color = LiveObjSkinEntry(f"VelocityLevels.Level{level}", self.song.view.selected_track)
        button.pressed_color = LiveObjSkinEntry("VelocityLevels.Pressed", self.song.view.selected_track)

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

    