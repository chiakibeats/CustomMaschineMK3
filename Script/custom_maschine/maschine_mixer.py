# ==================================================
#
# This file is part of CustomMaschineMK3.
# CustomMaschineMK3 is free software licensed under GPL-3.0.
# For more details, see "LICENSE" file.
# 
# Copyright (C) 2024-2025 chiaki
#
# ==================================================

from functools import partial
from itertools import zip_longest
from ableton.v3.control_surface.components import (
    ChannelStripComponent,
    ScrollComponent,
    Scrollable
)

from ableton.v3.control_surface.components.channel_strip import MAX_NUM_SENDS

from ableton.v3.control_surface.controls import (
    ButtonControl,
    MappedControl,
    MappedSensitivitySettingControl,
    RadioButtonGroup,
    control_list
)

from ableton.v2.control_surface.control import (
    MatrixControl
)

from ableton.v3.control_surface.display import Renderable

from ableton.v3.control_surface import Component

from ableton.v3.base import (
    clamp,
    depends,
    listens,
    listenable_property,
)

from ableton.v3.live import liveobj_valid

from .logger import logger

class MaschineMixerComponent(ScrollComponent, Renderable, Scrollable):
    """
    Another mixer component suitable for Maschine controller.

    Stock version of `MixerComponent` ties to session box.
    It constraints the count of tracks that the component can handle.
    Also, the session box determines which tracks is assigned to `MixerComponent` by its position.
    This desgin is useful if the controller's button row count and knob count are same, but not for Maschine.

    This component has dedicated track count configuration and paging feature.
    """
    parameter_controls = control_list(MappedControl)
    parameter_select_buttons = RadioButtonGroup(
        unchecked_color = "Mixer.Parameter",
        checked_color = "Mixer.ParameterSelected")
    
    prev_parameter_button = ButtonControl(color = "DefaultButton.On")
    next_parameter_button = ButtonControl(color = "DefaultButton.On")
    crossfader_control = MappedControl()
    knob_touch_buttons = control_list(ButtonControl, color = None)
    erase_button = ButtonControl(color = None)

    @depends(session_ring = None)
    def __init__(self, name = "Mixer", track_count = 8, session_ring = None, *a, **k):
        super().__init__(name = name, scroll_skin_name = "Mixer.TrackScroll", *a, **k)
        self.register_slot(self.song, self._assign_tracks, "tracks")
        self.register_slot(self.song, self._assign_tracks, "return_tracks")
        self.register_slot(self.song, self._assign_tracks, "visible_tracks")
        
        self._track_count = track_count
        self._track_position = 0
        self._all_tracks = []
        self._parameter_index = 0
        self._parameter_names = ["Volume", "Pan"] + ["Send " + chr(ord('A') + index) for index in range(MAX_NUM_SENDS)]
        self._channel_strips = [ChannelStripComponent(parent = self) for i in range(self._track_count)]

        self.parameter_controls.control_count = self._track_count
        self.parameter_select_buttons.control_count = self._track_count
        self.parameter_select_buttons.checked_index = 0

        self._assign_tracks()

    @parameter_select_buttons.pressed
    def _on_parameter_select_buttons_pressed(self, button):
        if button.index < len(self.song.return_tracks) + 2:
            self.parameter_index = button.index

    @prev_parameter_button.pressed
    def _on_prev_parameter_button_pressed(self, button):
        if self.parameter_index == 0:
            self.parameter_index = 2 + len(self.song.return_tracks) - 1
        else:
            self.parameter_index -= 1

    @next_parameter_button.pressed
    def _on_next_parameter_button_pressed(self, button):
        if self.parameter_index == 2 + len(self.song.return_tracks) - 1:
            self.parameter_index = 0
        else:
            self.parameter_index += 1
    
    @knob_touch_buttons.double_clicked
    def _on_knob_touch_double_clicked(self, button):
        if self.erase_button.is_pressed:
            parameter = self.parameter_controls[button.index].mapped_parameter
            if liveobj_valid(parameter) and not parameter.is_quantized:
                parameter.value = parameter.default_value
    
    @listenable_property
    def parameter_name(self):
        return self._parameter_names[self.parameter_index]
    
    @property
    def track_position(self):
        return self._track_position
    
    @track_position.setter
    def track_position(self, value):
        logger.info(f"Mixer track position {value}")

        self._track_position = value
        self._assign_tracks()
    
    @property
    def parameter_index(self):
        return self._parameter_index
    
    @parameter_index.setter
    def parameter_index(self, value):
        logger.info(f"Select mixer parameter index {value}")

        self._parameter_index = value
        if self._parameter_index < self.parameter_select_buttons.control_count:
            self.parameter_select_buttons.checked_index = self._parameter_index
        else:
            self.parameter_select_buttons.checked_index = -1
        self._assign_parameters()
        self.notify_parameter_name()
    
    def set_parameter_controls(self, controls):
        self.parameter_controls.set_control_element(controls)

    def set_parameter_select_buttons(self, buttons):
        self.parameter_select_buttons.set_control_element(buttons)

    def set_prev_parameter_button(self, button):
        self.prev_parameter_button.set_control_element(button)

    def set_next_parameter_button(self, button):
        self.next_parameter_button.set_control_element(button)

    def set_shift_button(self, button):
        for strip in self._channel_strips:
            strip.shift_button.set_control_element(button)

    def set_crossfader_control(self, control):
        self.crossfader_control.set_control_element(control)

    def set_knob_touch_buttons(self, buttons):
        self.knob_touch_buttons.set_control_element(buttons)

    def set_erase_button(self, button):
        self.erase_button.set_control_element(button)

    def __getattr__(self, name):
        """
        Proxy for mapping each control of array to each `ChannelStripComponent`.

        This works under combination of Python's name lookup and Live's mapping behaviour.

        1. Live's mapping system tries to find `set_{control name}` function to assign element to component.
        2. If the function is in the instance dictionary, call that function.
        3. If the function wasn't in the dictionary, Python calls `__getattr__` to retrieve the function dynamically.
        4. If it wasn't found, try finding `{control name}` member to assign element directly.
        5. If the member wasn't found, throw the error and abort the mapping procedure.

        This function cooperates with this flow by returning improvised setter to assign each element to channel strip.
        """
        if name.startswith("set_"):
            return partial(self._set_strip_controls, name[4:-1])
        # TODO: Add name parameter to the error
        raise AttributeError

    def can_scroll_up(self):
        return self.track_position - self._track_count >= 0
    
    def can_scroll_down(self):
        return self.track_position + self._track_count < len(self._all_tracks)
    
    def scroll_up(self):
        self._move_position(-self._track_count)
    
    def scroll_down(self):
        self._move_position(self._track_count)
    
    def _move_position(self, offset):
        total_tracks = len(self._all_tracks)
        self.track_position = clamp(self.track_position + offset, 0, total_tracks - total_tracks % self._track_count)

    def _get_parameter_by_index(self, track, index):
        if index == 0:
            return track.mixer_device.volume
        elif index == 1:
            return track.mixer_device.panning
        elif index > 1 and index - 2 < len(track.mixer_device.sends):
            return track.mixer_device.sends[index - 2]
        else:
            return None
        
    def _assign_parameters(self):
        for index in range(self._track_count):
            track_index = self.track_position + index
            if track_index < len(self._all_tracks):
                self.parameter_controls[index].mapped_parameter = self._get_parameter_by_index(self._all_tracks[track_index], self.parameter_index)
            else:
                self.parameter_controls[index].mapped_parameter = None

    def _assign_tracks(self):
        logger.info("Assign tracks to mixer")
        self._all_tracks = self.song.visible_tracks
        self._all_tracks += self.song.return_tracks
        self._all_tracks += (self.song.master_track,)

        for index in range(self._track_count):
            track_index = self.track_position + index
            if track_index < len(self._all_tracks):
                self._channel_strips[index].set_track(self._all_tracks[track_index])
            else:
                self._channel_strips[index].set_track(None)
        
        self._assign_parameters()

        super().update()

    def _set_strip_controls(self, name, controls):
        """
        Assign each control element to the corresponding control in channel strip.

        Args:
            name(str): Name of assignee.
            controls(list): Control elements to assign.
        """
        for strip, control in zip_longest(self._channel_strips, controls or []):
            getattr(strip, name).set_control_element(control)

    def update(self):
        super().update()
        self._assign_tracks()
        if self.is_enabled():
            self.crossfader_control.mapped_parameter = self.song.master_track.mixer_device.crossfader
        else:
            self.crossfader_control.mapped_parameter = None
