from ableton.v3.control_surface.component import Component
from ableton.v3.control_surface.display import Renderable
from ableton.v3.control_surface.controls import StepEncoderControl
from .Logger import logger
from ableton.v3.base import clamp, sign, listens, listenable_property

MAX_GROOVE_AMOUNT = 1.3

class GroovePoolComponent(Component, Renderable):
    coarse_groove_amount = StepEncoderControl(num_steps = 64)
    fine_groove_amount = StepEncoderControl(num_steps = 64)

    def __init__(self, name = "Groove_Pool", *a, **k):
        super().__init__(name, *a, **k)
        self.coarse_groove_amount.connect_property(
            self.song,
            "groove_amount",
            transform = lambda x: clamp(self.song.groove_amount + sign(x) / 20, 0, MAX_GROOVE_AMOUNT))
        
        self.fine_groove_amount.connect_property(
            self.song,
            "groove_amount",
            transform = lambda x: clamp(self.song.groove_amount + sign(x) / 100, 0, MAX_GROOVE_AMOUNT))
        
        self._on_groove_amount_changed.subject = self.song

    @listenable_property
    def amount_string(self):
        return f"{round(self.song.groove_amount * 100)}%"
    
    @listens("groove_amount")
    def _on_groove_amount_changed(self):
        self.notify_amount_string()
