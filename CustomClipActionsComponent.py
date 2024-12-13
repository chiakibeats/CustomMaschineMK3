from ableton.v3.control_surface.components import ClipActionsComponent
from ableton.v3.control_surface.components.clip_actions import QUANTIZATION_OPTION_NAMES
from ableton.v3.control_surface.controls import ButtonControl
from ableton.v3.live import display_name

class CustomClipActionsComponent(ClipActionsComponent):
    half_quantize_button = ButtonControl(color = "ClipActions.Quantize", pressed_color = "ClipActions.QuantizePressed")

    @half_quantize_button.pressed
    def half_quantize_button(self, _):
        target_clip = self._target_track.target_clip
        target_clip.quantize(self._quantization_value, 0.5)
        self.notify(self.notifications.Clip.quantize, display_name(target_clip), QUANTIZATION_OPTION_NAMES[self._quantization_value])

    def _update_quantize_button(self):
        super()._update_quantize_button()
        self.half_quantize_button.enabled = self._get_target_clip() is not None
