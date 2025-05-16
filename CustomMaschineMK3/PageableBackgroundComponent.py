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

from ableton.v3.control_surface.controls import control_list, ButtonControl
from ableton.v3.control_surface.display import Renderable
from ableton.v3.control_surface.elements import ButtonElement, ButtonMatrixElement
from ableton.v3.base import listenable_property
from .Logger import logger

class PageableBackgroundComponent(BackgroundComponent, ScrollComponent, Renderable):
    def __init__(self, name = "Pageable_Background", translation_channel = 2, page_count = 2, *a, **k):
        super().__init__(name, *a, **k)
        self._base_translation_channel = translation_channel
        self._page_count = page_count
        self._page_index = 0

    @listenable_property
    def page_index(self):
        return self._page_index
    
    def set_scroll_up_button(self, button):
        super().set_scroll_up_button(button)

    def set_scroll_down_button(self, button):
        super().set_scroll_down_button(button)

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
