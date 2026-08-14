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
    listens,
)
from ableton.v3.live import liveobj_valid
from ableton.v3.control_surface import (
    LiveObjSkinEntry,
    OptionalSkinEntry
)

from .logger import logger

class CustomClipSlotComponent(ClipSlotComponent):
    """
    Custom clip slot that supports blinking on playing or recording states.
    """
    @depends(blinker = None)
    def __init__(self, blinker = None, *a, **k):
        """
        Args:
            clipboard: Clipboard object for copy-paste operation.
            blinker(LEDBlinker): Timer object for blinking. DI container will supply actual value.
        """
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

        # Check this slot has an assigned control element and valid ClipSlot object.
        if self.launch_button.control_element != None and liveobj_valid(self.clip_slot):
            clip_or_slot = self.clip_slot.clip if self.clip_slot.has_clip else self.clip_slot

            # Perform periodic update if the associated clip or slot is in playing or recording state.
            if clip_or_slot.is_playing or clip_or_slot.is_recording:
                self._update_launch_button_color()