# ==================================================
#
# This file is part of CustomMaschineMK3.
# CustomMaschineMK3 is free software licensed under GPL-3.0.
# For more details, see "LICENSE" file.
# 
# Copyright (C) 2024-2025 chiaki
#
# ==================================================

from ableton.v3.control_surface.components import LoopSelectorComponent, ClipboardComponent
from ableton.v3.control_surface.controls import ButtonControl
from ableton.v3.live import liveobj_valid, liveobj_changed
from ableton.v3.base import listens

from .Logger import logger

class ClipRegion:
    def __init__(self, time, length):
        self.time = time
        self.length = length

class ClipRegionClipboardComponent(ClipboardComponent):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self._clip = None

    def set_clip(self, new_clip):
        self._clip = new_clip
        self.clear()
    
    def _do_paste(self, obj):
        logger.info(f"source = {self._source_obj}, dest = {obj}")
        if self._source_obj.time == obj.time:
            self._did_paste = True
        else:
            self._clip.duplicate_region(self._source_obj.time, self._source_obj.length, obj.time)
            self._did_paste = super()._do_paste(obj)

        return self._did_paste
    
    def _is_source_valid(self):
        return liveobj_valid(self._clip) and self._source_obj != None

class CustomLoopSelectorComponent(LoopSelectorComponent):
    copy_button = ButtonControl(color = "Clipboard.Empty", on_color = "Clipboard.Filled")

    _custom_clipboard = None

    def __init__(self, name = "Loop_Selector", custom_clipboard_component_type = None, paginator = None, *a, **k):
        super().__init__(name = name, paginator = paginator, *a, **k)
        custom_clipboard_component_type = custom_clipboard_component_type or ClipRegionClipboardComponent
        self._custom_clipboard = custom_clipboard_component_type(parent = self)
        self._on_target_clip_changed.subject = self._sequencer_clip
        self._on_clipboard_content_changed.subject = self._custom_clipboard
        self._on_target_clip_changed()
    
    def set_copy_button(self, button):
        self.copy_button.set_control_element(button)

    @copy_button.pressed
    def _on_copy_button_pressed(self, button):
        self._custom_clipboard.copy_or_paste(ClipRegion(self._paginator.page_time, self.bar_length))

    @listens("has_content")
    def _on_clipboard_content_changed(self, value):
        self.copy_button.is_on = value

    @listens("clip")
    def _on_target_clip_changed(self):
        self._custom_clipboard.set_clip(self._sequencer_clip.clip)

    def update(self):
        super().update()
        self._on_clipboard_content_changed(self._custom_clipboard.has_content)
