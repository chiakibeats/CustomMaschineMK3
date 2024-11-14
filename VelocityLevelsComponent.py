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
from ableton.v3.base import depends, listens

from .Logger import logger

DEFAULT_NOTE = 60

class VelocityLevelsComponent(PlayableComponent):
    _pitch_provider = None
    _velocity_levels = None

    @depends(velocity_levels = None)
    def __init__(self, name = "VelocityLevels", matrix_always_listenable = False, velocity_levels = None, *a, **k):
        super().__init__(name, matrix_always_listenable, *a, **k)
        self._velocity_levels = velocity_levels
        self._velocity_levels.enabled = True
        self._velocity_levels.target_note = DEFAULT_NOTE
        self._velocity_levels.target_channel = 1
        self._velocity_levels.source_channel = 0
        self._velocity_levels.notes = list(range(60, 76))
        logger.info(f"velocity_levels = {self._velocity_levels}")
        logger.info(f"velocity_levels = {self._velocity_levels.__dir__()}")

    def set_pitch_provider(self, provider):
        self._pitch_provider = provider
        self._on_pitches_changed.subject = self._pitch_provider

    def _note_translation_for_button(self, button):
        return super()._note_translation_for_button(button)
    
    def set_matrix(self, matrix):
        super().set_matrix(matrix)
        if matrix != None:
            logger.info("Velocity levels mode enabled")
            #self._velocity_levels.enabled = True
        else:
            logger.info("Velocity levels mode disabled")
            #self._velocity_levels.enabled = False

    def update(self):
        super().update()
        self._velocity_levels.enabled = True
        self._velocity_levels.target_note = DEFAULT_NOTE
        self._velocity_levels.target_channel = 1
        self._velocity_levels.source_channel = 0
        self._velocity_levels.notes = list(range(60, 76))


    @listens("pitches")
    def _on_pitches_changed(self):
        pitches = self._pitch_provider.pitches
        self._velocity_levels.target_note = pitches[0] if len(pitches) > 0 else DEFAULT_NOTE

    