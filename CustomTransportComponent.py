from ableton.v3.base import listens, listenable_property, task
from ableton.v3.control_surface.components import TransportComponent
from Live.Song import TimeFormat # type: ignore

from .Logger import logger
from time import time_ns

class CustomTransportComponent(TransportComponent):

    def __init__(self, name = "Transport", *a, **k):
        super().__init__(name, *a, **k)
        self._timestamp = 0
        self.register_slot(self.song, self.notify_song_tempo, "tempo")
        self.register_slot(self.song, self._notify_song_time_changed, "current_song_time")

    @listenable_property
    def song_tempo(self):
        return self.song.tempo
    
    @listenable_property
    def current_song_time_in_bars(self):
        song_time = self.song.get_current_beats_song_time()
        return f"{song_time.bars:>4}.{song_time.beats:>2}.{song_time.sub_division:>2}"
    
    @listenable_property
    def current_song_time(self):
        song_time = self.song.get_current_smpte_song_time(TimeFormat.ms_time)
        return f"{song_time.hours:>02}:{song_time.minutes:>02}:{song_time.seconds:>02}"
    
    def _notify_song_time_changed(self):
        # Make dead time to avoid too frequent update
        if time_ns() - self._timestamp > 50_000_000:
            self._timestamp = time_ns()
            # self._dead_time_task.restart()
            self.notify_current_song_time_in_bars()
            self.notify_current_song_time()
