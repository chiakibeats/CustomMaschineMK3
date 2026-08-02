# ==================================================
#
# This file is part of CustomMaschineMK3.
# CustomMaschineMK3 is free software licensed under GPL-3.0.
# For more details, see "LICENSE" file.
# 
# Copyright (C) 2024-2025 chiaki
#
# ==================================================

from ableton.v3.base import listens
from ableton.v3.live.util import liveobj_valid
from ableton.v3.control_surface.components import SlicedSimplerComponent
from ableton.v3.control_surface.components.sliced_simpler import DEFAULT_SIMPLER_TRANSLATION_CHANNEL
from ableton.v3.control_surface.controls import (
    ButtonControl,
    PlayableControl,
    control_list
)
from ableton.v3.control_surface.skin import LiveObjSkinEntry

from .logger import logger
from .clip_notes_select import ClipNotesSelectMixin

class CustomSlicedSimplerComponent(ClipNotesSelectMixin, SlicedSimplerComponent):
    """
    Playable component for the Simpler device with slicing mode.
    
    Like the `CustomDrumGroupComponent`, this component has page jump buttons to access the all 64 slices.
    """
    _select_buttons = control_list(ButtonControl, control_count = 4, color = None)
    _has_slice_list = [False] * 4

    def __init__(self, *a, **k):
        super().__init__(*a, **k, matrix_always_listenable = True)

    def set_select_buttons(self, matrix):
        """
        Assign matrix element to the internal control. 
        Calculation of slice group depends on size of this control, so it triggers updates.

        Args:
            matrix(ButtonMatrixElement): Matrix element to assign.
        """
        self._select_buttons.set_control_element(matrix)
        self._update_slice_group()
        self._update_led_feedback()

    @_select_buttons.pressed
    def _on_select_buttons_pressed(self, target_button):
        """
        Jump to specific slice page.
        
        Args:
            target_button(ButtonControl): Button that triggered event.
        """
        for button in self._select_buttons:
            if button == target_button:
                # SlicedSimplersComponent arranges 64 slices in a 4 * 16 grid.
                # To implement page jump, the scroll position moves by multiple of 4.
                self.position = button.index * 4
                logger.info(f"Slice group selected index = {button.index}")

    def _on_matrix_pressed(self, button):
        self.process_pad_pressed(button)
        return super()._on_matrix_pressed(button)

    def set_simpler_device(self, simpler_device):
        sample = self._simpler_device.sample if liveobj_valid(self._simpler_device) else None
        self._on_slices_changed.subject = sample
        super().set_simpler_device(simpler_device)

    def update(self):
        self._update_slice_group()
        super().update()

    def _update_led_feedback(self):
        super()._update_led_feedback()
        for button in self._select_buttons:
            if self._has_slice_list[button.index]:
                new_color = "SlicedSimpler.GroupHasSlice"
            else:
                new_color = "SlicedSimpler.Group"

            # Highlight page buttons that intersect with current slice view.
            start_position = button.index * 4
            intersects = any([pos >= start_position and pos < start_position + 4 for pos in [self.position, self.position + 3]])
            if intersects:
                new_color += "Selected"

            button.color = LiveObjSkinEntry(new_color, self._target_track.target_track)

    def _update_button_color(self, button):
        super()._update_button_color(button)
        button.pressed_color = LiveObjSkinEntry("SlicedSimpler.SlicePressed", self._target_track.target_track)

    def _update_slice_group(self):
        """Update slice page availability."""
        slices = self._slices()
        logger.debug(f"Update slice group slices = {slices}, length = {len(slices)}")
        for index in range(self._select_buttons.control_count):
            self._has_slice_list[index] = len(slices) > index * 16

    @listens("slices")
    def _on_slices_changed(self):
        self._update_slice_group()
        self._update_led_feedback()
