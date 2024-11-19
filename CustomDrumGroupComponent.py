from itertools import zip_longest
from ableton.v3.base import listens, listens_group
from ableton.v3.control_surface.components import DrumGroupComponent
from ableton.v3.control_surface.controls import (
    control_matrix,
    PlayableControl,
    ButtonControl
)

from .Logger import logger

DEFAULT_GROUP_SIZE = 16

class CustomDrumGroupComponent(DrumGroupComponent):
    _select_buttons = control_matrix(ButtonControl, color = None)
    _group_start_notes = list(range(4, 128, DEFAULT_GROUP_SIZE))
    _has_chain_list = []

    select_modifier = ButtonControl()

    def __init__(self, *a, **k):
        super().__init__(translation_channel = 1, *a, **k, matrix_always_listenable = True)

    def set_select_buttons(self, matrix):
        self._select_buttons.set_control_element(matrix)
        self._has_chain_list = [False] * self._select_buttons.control_count
        if matrix is not None:
            self._update_group_info()
            self._update_led_feedback()

    def set_drum_group_device(self, drum_group_device):
        super().set_drum_group_device(drum_group_device)
        self._on_chains_changed.replace_subjects(self._all_drum_pads)

    def set_matrix(self, matrix):
        super().set_matrix(matrix)
        # for button in self.matrix:
        #     button.set_mode(PlayableControl.Mode.playable_and_listenable)

    def _update_led_feedback(self):
        super()._update_led_feedback()
        for button, has_chain in zip(self._select_buttons, self._has_chain_list):
            row, column = button.coordinate

            # check visible pads window intersects each group regions
            # testing lower row (position) and upper row (position + 3) 
            start_position = int(self._group_start_notes[row * self.width + column] / 4)
            position = self._drum_group_scroller.position
            intersects = any([pos >= start_position and pos < start_position + 4 for pos in [position, position + 3]])

            if has_chain:
                new_color = "DrumGroup.GroupHasFilledPad"
            else:
                new_color = "DrumGroup.Group"

            if intersects:
                new_color += "Selected"

            button.color = new_color

    def _update_button_color(self, button):
        super()._update_button_color(button)
        button.pressed_color = "DrumGroup.PadPressed"

    def _update_group_info(self):
        button_count = self._select_buttons.control_count
        groups = list(zip(range(button_count), self._group_start_notes))
        has_chain_list = [False] * button_count
        logger.info(f"Update group info groups = {groups}")

        for pad in self._all_drum_pads:
            if pad is not None:
                logger.debug(f"pad note {pad.note}, chain len = {len(pad.chains)}")
                for index, start_note in groups:
                    if pad.note < start_note + DEFAULT_GROUP_SIZE and len(pad.chains):
                        logger.debug(f"pad note {pad.note} group {index} has chain")
                        has_chain_list[index] = True
                        break
        
        logger.info(f"has_chain_list = {has_chain_list}")
        self._has_chain_list = has_chain_list


    @_select_buttons.pressed
    def _on_group_select_buttons_pressed(self, target_button):
        for button in self._select_buttons:
            if button == target_button:
                logger.info(f"Drum group select index = {button.coordinate}")
                row, column = button.coordinate
                position = self._get_actual_group_scroll_position(row * self.width + column)
                logger.info(f"Scroll position = {position}")
                self._drum_group_scroller.position = position

    @listens_group("chains")
    def _on_chains_changed(self, subject):
        self._update_group_info()
        self._update_led_feedback()

    def _get_actual_group_scroll_position(self, group_index):
        # make sure not exceeding max scroll position when selecting last group
        start_note = min(self._group_start_notes[group_index], 128 - self.matrix.control_count)
        return int(start_note / 4)
