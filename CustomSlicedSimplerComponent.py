from ableton.v3.base import listens
from ableton.v3.live.util import liveobj_valid
from ableton.v3.control_surface.components import SlicedSimplerComponent
from ableton.v3.control_surface.components.sliced_simpler import DEFAULT_SIMPLER_TRANSLATION_CHANNEL
from ableton.v3.control_surface.controls import (
    ButtonControl,
    control_list
)

from .Logger import logger

class CustomSlicedSimplerComponent(SlicedSimplerComponent):
    _select_buttons = control_list(ButtonControl, control_count = 4, color = None)
    _has_slice_list = [False] * 4

    select_modifier = ButtonControl()

    def __init__(self, *a, **k):
        super().__init__(*a, translation_channel = 1, **k)

    def set_select_buttons(self, matrix):
        self._select_buttons.set_control_element(matrix)
        self._update_slice_group()
        self._update_led_feedback()

    @_select_buttons.pressed
    def _on_select_buttons_pressed(self, target_button):
        for button in self._select_buttons:
            if button == target_button:
                self.position = button.index * 4
                logger.info(f"Slice group selected index = {button.index}")


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

            start_position = button.index * 4
            intersects = any([pos >= start_position and pos < start_position + 4 for pos in [self.position, self.position + 3]])
            if intersects:
                new_color += "Selected"

            button.color = new_color

    def _update_slice_group(self):
        slices = self._slices()
        logger.info(f"Update slice group slices = {slices}, length = {len(slices)}")
        for index in range(self._select_buttons.control_count):
            self._has_slice_list[index] = len(slices) > index * 16

    @listens("slices")
    def _on_slices_changed(self):
        self._update_slice_group()
        self._update_led_feedback()
