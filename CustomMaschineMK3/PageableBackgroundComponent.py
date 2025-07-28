# ==================================================
#
# This file is part of CustomMaschineMK3.
# CustomMaschineMK3 is free software licensed under GPL-3.0.
# For more details, see "LICENSE" file.
# 
# Copyright (C) 2024-2025 chiaki
#
# ==================================================

from ableton.v3.control_surface.components import (
    BackgroundComponent,
    ScrollComponent
)

from ableton.v3.control_surface.controls import control_list, ButtonControl, EncoderControl, InputControl
from ableton.v3.control_surface.display import Renderable
from ableton.v3.control_surface.elements import ButtonElement, ButtonMatrixElement
from ableton.v3.base import listenable_property
from .Logger import logger

class PageableBackgroundComponent(BackgroundComponent, ScrollComponent, Renderable):
    user_knobs = InputControl
    user_buttons = InputControl
    learn_button = ButtonControl(color = "DefaultButton.Off", on_color = "DefaultButton.On")
    knob_touch_buttons = InputControl

    def __init__(self, name = "Pageable_Background", translation_channel = 2, page_count = 2, *a, **k):
        super().__init__(name, *a, **k)
        self._base_translation_channel = translation_channel
        self._page_count = page_count
        self._page_index = 0
        self._learn_enabled = False

    @listenable_property
    def page_index(self):
        return self._page_index
    
    def can_scroll_up(self):
        return self._page_index > 0
    
    def can_scroll_down(self):
        return self._page_index < self._page_count - 1
    
    def scroll_up(self):
        self._page_index -= 1
        self._set_translation_channel()
        self.notify_page_index()
    
    def scroll_down(self):
        self._page_index += 1
        self._set_translation_channel()
        self.notify_page_index()

    def set_learn_button(self, button):
        if button == None:
            # If user leaves from custom mapping mode, learn mode is disabled automatically
            self._learn_enabled = False
            self.learn_button.is_on = False
        self.learn_button.set_control_element(button)

    @learn_button.pressed
    def _learn_button_pressed(self, button):
        self._learn_enabled = not self._learn_enabled
        self._update_learn_state()

    def _update_learn_state(self):
        self.learn_button.is_on = self._learn_enabled
        element_count = min(len(self.user_knobs.control_element), len(self.knob_touch_buttons.control_element))
        if self._learn_enabled:
            for index in range(element_count):
                touch_element = self.knob_touch_buttons.control_element[index]
                knob_element = self.user_knobs.control_element[index]
                touch_element.set_identifier(knob_element.message_identifier())
        else:
            for index in range(element_count):
                element = self.knob_touch_buttons.control_element[index]
                element.set_identifier(element.original_identifier())
    
    def _setup_control_state(self, name, control_state):
        control_state.channel = self._base_translation_channel + self._page_index

    def _set_translation_channel(self):
        for control_state in self._control_states.values():
            element = control_state.control_element
            if isinstance(element, ButtonElement):
                element.send_value(0, force = True)
            elif isinstance(element, ButtonMatrixElement):
                for child in element:
                    child.send_value(0, force = True)
            control_state.channel = self._base_translation_channel + self._page_index
