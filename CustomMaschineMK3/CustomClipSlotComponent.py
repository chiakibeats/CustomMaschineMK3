# ==================================================
#
# This file is part of CustomMaschineMK3.
# CustomMaschineMK3 is free software licensed under GPL-3.0.
# For more details, see "LICENSE" file.
# 
# Copyright (C) 2024-2025 chiaki
#
# ==================================================

from ableton.v3.control_surface.components import ClipSlotComponent
from ableton.v3.base import (
    depends,
    listenable_property,
    listens,
    EventObject
)
from ableton.v3.control_surface import (
    LiveObjSkinEntry,
    OptionalSkinEntry
)

from Live.Base import Timer # type: ignore

from .Logger import logger

class LEDBlinker(EventObject):
    def __init__(self, blink_time = 0.5):
        self._blink_time = blink_time * 1000
        self._blink_state = True
        self._timer = Timer(callback = self.timer_callback, interval = int(self._blink_time), start = True)

    @listenable_property
    def blink_state(self):
        return self._blink_state

    def timer_callback(self):
        self._blink_state = not self._blink_state
        logger.info(f"Blink state = {self._blink_state}")
        self._timer.restart()
        self.notify_blink_state()

class CustomClipSlotComponent(ClipSlotComponent):
    @depends(blinker = None)
    def __init__(self, clipboard = None, blinker = None, *a, **k):
        super().__init__(*a, **k)
        self._blinker = blinker
        self._on_blink_state_changed.subject = self._blinker
        self._blink_state = self._blinker.blink_state

    def _update_launch_button_color(self):
        super()._update_launch_button_color()
    
    def _feedback_value(self, track, slot_or_clip):
        skin_or_str = super()._feedback_value(track, slot_or_clip)
        # Ableton has changed the return value of this function, so it has to consider two patterns
        # Earlier version always returns LiveObjSkinEntry
        # Later version (maybe 12.1?) returns str or OptionalSkinEntry
        if not self._blink_state:
            if isinstance(skin_or_str, LiveObjSkinEntry):
                if skin_or_str.name == "Session.ClipPlaying" or skin_or_str.name == "Session.ClipRecording":
                    skin_or_str.name += "Dimmed"
            elif isinstance(skin_or_str, str):
                if skin_or_str == "Session.ClipPlaying" or skin_or_str == "Session.ClipRecording":
                    skin_or_str += "Dimmed"
        
        # logger.info(f"Clip color = {skin_or_str}")

        return skin_or_str

    @listens("blink_state")
    def _on_blink_state_changed(self):
        self._blink_state = self._blinker.blink_state
        if self.launch_button.control_element != None:
            self._update_launch_button_color()