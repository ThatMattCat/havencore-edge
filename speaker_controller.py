import sys
sys.path.append('/usr/lib/python3/dist-packages')
import uvicorn
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import json
import socket
import config
import logging
from fastapi import FastAPI, Request
from pydantic import BaseModel
from trace_id import with_trace, get_trace_id, set_trace_id


logger = config.get_logger('rpi')
Gst.init(None)

class SpeakerController:
    """Controller for audio playback using GStreamer.
    
    Handles playing audio from URLs through the system's audio output.
    """
    def __init__(self):
        self.is_playing = False
        self.playlist = []
        self.ws = None

    @with_trace
    async def play_audio(self, audio_url: str = None, trace_id: str = None):
        """Play audio from a URL using GStreamer.
        
        Args:
            audio_url: URL of the audio to play
            trace_id: Optional trace ID for request tracing
        """
        if trace_id:
            set_trace_id(trace_id)
        pipeline_str = f"playbin uri={audio_url} audio-sink=\"autoaudiosink\""
        logger.debug(f"pipeline_str: {pipeline_str}")
        pipeline = Gst.parse_launch(pipeline_str)
        pipeline.set_state(Gst.State.PLAYING)
        loop = GLib.MainLoop()
        bus = pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message, loop, pipeline)
        loop.run()

    def on_message(self, bus, message, loop, pipe):
        t = message.type
        if t == Gst.MessageType.EOS:
            print("End of stream")
            pipe.set_state(Gst.State.NULL)
            loop.quit()
        elif t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            logger.error(f"Error: {err}, {debug}")
            pipe.set_state(Gst.State.NULL)
            loop.quit()

    async def stop(self):
        pass
