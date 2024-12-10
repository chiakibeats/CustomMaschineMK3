from ableton.v3.control_surface.component import Component
from ableton.v3.control_surface.display import Renderable
from ableton.v2.control_surface.internal_parameter import InternalParameter
from ableton.v3.control_surface.controls import (
    StepEncoderControl,
    ButtonControl,
    control_list
)
from ableton.v3.live.util import liveobj_valid
from ableton.v3.base import sign, listens, listenable_property
from ableton.v3.live import application
from Live import Song # type: ignore

from .Logger import logger

class ScaleSystemComponent(Component):
    select_encoder = StepEncoderControl(num_steps = 64)
    root_note_encoder = StepEncoderControl(num_steps = 64)
    toggle_button = ButtonControl()
    # Just for LED feedback
    indicator_button_1 = ButtonControl(color = "Scale.Off", on_color = "Scale.On")
    indicator_button_2 = ButtonControl(color = "Scale.Off", on_color = "Scale.On")
    indicator_button_3 = ButtonControl(color = "Scale.Off", on_color = "Scale.On")
    indicator_button_4 = ButtonControl(color = "Scale.Off", on_color = "Scale.On")

    _all_scales_list = [name for name, intervals in Song.get_all_scales_ordered()]
    _selected_scale_index = 0
    _is_internal = False
    _internal_scale_mode = False

    def __init__(self, name = "Scale_System", *a, **k):
        super().__init__(name, *a, **k)
        if application().get_major_version() == 11:
            # Live 11 don't have access to scale mode state.
            # Manage scale mode internally for matching behaviour with Live 12.
            self._is_internal = True
        else:
            self._is_internal = False
            self.register_slot(self.song, self._on_scale_mode_changed, "scale_mode")
        
        self.register_slot(self.song, self._on_scale_name_changed, "scale_name")
        self.register_slot(self.song, self._on_root_note_changed, "root_note")
        logger.info(f"Scales = {self._all_scales_list}")

    @listenable_property
    def scale_mode(self):
        if self._is_internal:
            return self._internal_scale_mode
        else:
            return self.song.scale_mode

    @scale_mode.setter
    def scale_mode(self, mode):
        if self._is_internal:
            self._internal_scale_mode = mode
            self.notify_scale_mode()
        else:
            self.song.scale_mode = mode

    @toggle_button.pressed
    def _on_toggle_button_pressed(self, button):
        logger.info(f"Scale mode toggle before = {self.scale_mode}, after = {not self.scale_mode}")
        self.scale_mode = not self.scale_mode
        self._update_led_feedback()

    @select_encoder.value
    def _on_select_encoder_value_changed(self, value, encoder):
        new_scale_index = self._selected_scale_index + int(sign(value))
        if new_scale_index < 0:
            new_scale_index = len(self._all_scales_list) - 1
        elif new_scale_index >= len(self._all_scales_list):
            new_scale_index = 0

        self.song.scale_name = self._all_scales_list[new_scale_index]

    @root_note_encoder.value
    def _on_root_note_encoder_value_changed(self, value, encoder):
        new_root_note = self.song.root_note + int(sign(value))
        if new_root_note < 0:
            new_root_note = 11
        elif new_root_note >= 12:
            new_root_note = 0

        self.song.root_note = new_root_note

    def _on_scale_mode_changed(self):
        self.notify_scale_mode()
        self._update_led_feedback()

    def _on_scale_name_changed(self):
        for index, scale in enumerate(self._all_scales_list):
            if scale == self.song.scale_name:
                self._selected_scale_index = index
                logger.info(f"Selected scale name = {scale}, index = {index}")
                break

    def _on_root_note_changed(self):
        # Update renderable state
        pass

    def _update_led_feedback(self):
        buttons = [
            self.indicator_button_1,
            self.indicator_button_2,
            self.indicator_button_3,
            self.indicator_button_4
        ]

        for button in buttons:
            button.is_on = self.scale_mode

    def update(self):
        super().update()
        self._on_scale_mode_changed()
        self._on_scale_name_changed()
        self._on_root_note_changed()
