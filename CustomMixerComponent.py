from ableton.v3.control_surface.components import (
    MixerComponent,
    ScrollComponent,
    Scrollable
)

from ableton.v3.control_surface.components.channel_strip import MAX_NUM_SENDS

from ableton.v3.control_surface.controls import (
    ButtonControl,
    EncoderControl,
    TouchControl,
    MappedControl,
    SendValueInputControl,
    SendValueEncoderControl,
    control_list
)

from ableton.v2.control_surface.control import (
    MatrixControl
)

from ableton.v2.control_surface import (
    WrappingParameter
)
from ableton.v3.control_surface import ScriptForwarding

from ableton.v3.base import (
    clamp,
    depends,
    listens,
    listenable_property,
)

from ableton.v3.live import liveobj_valid

from .Logger import logger

class CustomMixerComponent(MixerComponent):
    pan_or_send_controls = control_list(MappedControl)
    prev_control_button = ButtonControl()
    next_control_button = ButtonControl()

    _control_index = 0
    _control_count = 1
    _track_count = 0
    _display_names = ["Pan"] + ["Send " + chr(ord('A') + index) for index in range(MAX_NUM_SENDS)]

    @depends(session_ring = None, show_message = None)
    def __init__(self, name = "Mixer", session_ring = None, show_message = None, *a, **k):
        super().__init__(name, session_ring = session_ring, *a, **k)
        self._on_return_tracks_changed.subject = self.song
        self._on_return_tracks_changed()
        self._track_count = session_ring.num_tracks
        self._show_message = show_message

    def set_pan_or_send_controls(self, controls):
        self.pan_or_send_controls.set_control_element(controls)
        self._update_control_mapped_parameter(self.control_index)
        if controls != None:
            self._show_current_control_name()
    
    def set_prev_control_button(self, button):
        self.prev_control_button.set_control_element(button)

    def set_next_control_button(self, button):
        self.next_control_button.set_control_element(button)

    @property
    def control_index(self):
        return self._control_index
    
    @control_index.setter
    def control_index(self, index):
        changed = self._control_index != index
        self._control_index = clamp(index, 0, self._control_count - 1)
        if changed:
            self._update_control_mapped_parameter(self._control_index)
    
    @prev_control_button.pressed
    def _on_prev_button_pressed(self, button):
        if self.control_index == 0:
            self.control_index = self._control_count - 1
        else:
            self.control_index -= 1

        self._show_current_control_name()

    @next_control_button.pressed
    def _on_next_button_pressed(self, button):
        if self.control_index == self._control_count - 1:
            self.control_index = 0
        else:
            self.control_index += 1

        self._show_current_control_name()

    def _update_control_mapped_parameter(self, index):
        map_range = range(min(self._track_count, self.pan_or_send_controls.control_count))
        logger.info(f"current control index = {index}")
        if index == 0:
            for track_index in map_range:
                track = self.channel_strip(track_index).track
                if liveobj_valid(track):
                    self.pan_or_send_controls[track_index].mapped_parameter = track.mixer_device.panning
                else:
                    self.pan_or_send_controls[track_index].mapped_parameter = None
        else:
            for track_index in map_range:
                track = self.channel_strip(track_index).track                
                if liveobj_valid(track) and len(track.mixer_device.sends) > index - 1:
                    self.pan_or_send_controls[track_index].mapped_parameter = track.mixer_device.sends[index - 1]
                else:
                    self.pan_or_send_controls[track_index].mapped_parameter = None

    def _show_current_control_name(self):
        self._show_message(f"Mixer Control Select: {self._display_names[self.control_index]}")

    def _reassign_tracks(self):
        super()._reassign_tracks()
        self._update_control_mapped_parameter(self.control_index)

    @listens("return_tracks")
    def _on_return_tracks_changed(self):
        self._control_count = 1 + len(self.song.return_tracks)
        if self.control_index >= self._control_count:
            self.control_index = self._control_count - 1
            self._show_current_control_name()
    
