from ableton.v3.control_surface.component import Component
from ableton.v3.control_surface.display import Renderable
from ableton.v3.control_surface.controls import StepEncoderControl, MappedControl, ButtonControl
from .Logger import logger
from ableton.v3.base import clamp, sign, listens, depends, listenable_property


class MasterVolumeComponent(Component, Renderable):
    master_volume = StepEncoderControl(num_steps = 64)
    reset_button = ButtonControl(color = None)

    def __init__(self, name = "Master_Volume", target_track = None, *a, **k):
        super().__init__(name, *a, **k)
        self._master_volume = self.song.master_track.mixer_device.volume
        self._on_master_volume_changed.subject = self._master_volume

    @listenable_property
    def gain_string(self):
        display_value = self._master_volume.str_for_value(self._master_volume.value)
        return " " + display_value if display_value[0] != "-" else display_value

    # Roughly 0.1dB step gain control
    # +6 to -18dB range has perfect linearity, lower range has different (exponential) scale.
    @master_volume.value
    def _on_coarse_volume_changed(self, value, encoder):
        self._master_volume.value = clamp(self._master_volume.value + sign(value) / 400, 0.0, 1.0)
            
    @reset_button.pressed
    def _on_reset_button_pressed(self, button):
        self._master_volume.value = self._master_volume.default_value

    @listens("value")
    def _on_master_volume_changed(self):
        self.notify_gain_string()
