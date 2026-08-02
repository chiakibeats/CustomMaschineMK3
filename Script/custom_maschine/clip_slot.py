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

from .logger import logger

class LEDBlinker(EventObject):
    """
    Timer and flag management for LED blinking.
    """
    def __init__(self, blink_time = 0.5):
        self._blink_time = blink_time * 1000
        self._blink_state = True
        self._timer = Timer(callback = self.timer_callback, interval = int(self._blink_time), start = True)

    @listenable_property
    def blink_state(self):
        return self._blink_state

    def timer_callback(self):
        self._blink_state = not self._blink_state
        #logger.info(f"Blink state = {self._blink_state}")
        self._timer.restart()
        self.notify_blink_state()

class CustomClipSlotComponent(ClipSlotComponent):
    """
    Custom clip slot that supports blinking on playing or recording states.
    """
    @depends(blinker = None)
    def __init__(self, clipboard = None, blinker = None, *a, **k):
        super().__init__(*a, **k)
        self._blinker = blinker
        self._on_blink_state_changed.subject = self._blinker
        self._blink_state = self._blinker.blink_state

    def _update_launch_button_color(self):
        super()._update_launch_button_color()
    
    def _feedback_value(self, track, slot_or_clip):
        """
        Update the button color according to the states of assigned slot.

        This script implements blinking mechanism by combination of timer and skin color definition.
        Other Ableton-ready controllers usually have this feature inside sending messages to the dedicated "blinking" MIDI channel.

        It is fine with 16 pads, but it potentially causes performance issue if the controller has too many pads.
        """
        # 3 different type values are returned from _feedback_value method.
        # 1. str
        # 2. LiveObjSkinEntry
        # 3. OptionalSkinEntry
        # We must check object type and determine what to do.
        skin_or_str = super()._feedback_value(track, slot_or_clip)

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
        """Trigger updating color of clip launch button."""
        self._blink_state = self._blinker.blink_state
        # Call update if the component has mapped element
        # TODO: Check assigned slot state to reduce redundant calls.
        if self.launch_button.control_element != None:
            self._update_launch_button_color()