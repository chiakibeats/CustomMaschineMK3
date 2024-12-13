from ableton.v3.control_surface.component import Component
from ableton.v3.control_surface.display import Renderable
from ableton.v3.control_surface.controls import StepEncoderControl, MappedControl, ButtonControl
from .Logger import logger
from ableton.v3.base import clamp, sign, listens, depends


class MasterVolumeComponent(Component):
    coarse_volume = StepEncoderControl(num_steps = 64)
    fine_volume = StepEncoderControl(num_steps = 64)
    reset_button = ButtonControl(color = None)

    _target_track = None

    @depends(target_track = None)
    def __init__(self, name = "Master_Volume", target_track = None, *a, **k):
        super().__init__(name, *a, **k)
        self._target_track = target_track

    # roughly 1dB / 0.1dB step gain control
    @coarse_volume.value
    def _on_coarse_volume_changed(self, value, encoder):
        volume_parameter = self._target_track.target_track.mixer_device.volume
        volume_parameter.value = clamp(volume_parameter.value + sign(value) / 40, 0.0, 1.0)
        
    @fine_volume.value
    def _on_fine_volume_changed(self, value, encoder):
        volume_parameter = self._target_track.target_track.mixer_device.volume
        volume_parameter.value = clamp(volume_parameter.value + sign(value) / 400, 0.0, 1.0)
    
    @reset_button.pressed
    def _on_reset_button_pressed(self, button):
        volume_parameter = self._target_track.target_track.mixer_device.volume
        volume_parameter.value = volume_parameter.default_value
