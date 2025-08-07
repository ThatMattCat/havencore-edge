import asyncio
from enum import Enum
import logging
import numpy as np
import pyaudio
import pvporcupine
import usb.core
import usb.util
import websockets
from concurrent.futures import ThreadPoolExecutor
import config
import queue
import json
from trace_id import with_trace, get_trace_id, set_trace_id
from speaker_controller import SpeakerController
from pixel_ring import PixelRing
from usb_4_mic_array.tuning import Tuning

# Apply the configuration
logger = config.get_logger('rpi')

class WSMessages(Enum):
    AUDIO_TYPE = "AUDIO"
    CONTROL_TYPE = "CONTROL"
    START_MSG = "start"
    STOP_MSG = "stop"

# TODO: Split out mic-related code into separate microphone controller class
class AudioController:
    def __init__(self):
        self.speaker = SpeakerController()
        self.respeaker = self.initialize_respeaker() # also sets self.pixel_ring
        if not self.respeaker:
            logger.error("ReSpeaker initialization failed")
            exit(1)
        self.pixel_ring.off() # Normally off
        self.porcupine = pvporcupine.create(access_key=config.ACCESS_KEY, keyword_paths=config.KEYWORD_PATHS)
        self.porcupine_frame_length = self.porcupine.frame_length
        self.stt_ip = config.STT_IP
        self.stt_port = config.STT_PORT
        self.is_streaming = False
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.ws = None
        self.silence_task = None
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.audio_queue = queue.Queue()

    def initialize_respeaker(self):
        try:
            dev = usb.core.find(idVendor=config.RESPEAKER_ID_VENDOR, idProduct=config.RESPEAKER_ID_PRODUCT)
            if dev:
                self.pixel_ring = PixelRing(dev)
                return Tuning(dev)
            else:
                logger.warning("ReSpeaker device not found")
                return None
        except Exception as e:
            logger.error(f"Error initializing ReSpeaker: {e}")
            return None

    def open_stream(self):
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
        
        self.stream = self.audio.open(
            rate=16000,
            channels=6,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=4096,
            stream_callback=self.audio_callback
        )
        logger.info("Audio stream opened")

    def audio_callback(self, in_data, frame_count, time_info, status):
        self.audio_queue.put(in_data)
        return (None, pyaudio.paContinue)

    async def process_audio_queue(self):
        while True:
            try:
                in_data = self.audio_queue.get_nowait()
                await self.process_audio(in_data)
            except queue.Empty:
                await asyncio.sleep(0.01)  # Short sleep to prevent busy-waiting

    @with_trace
    async def process_audio(self, in_data):
        audio_array = np.frombuffer(in_data, dtype=np.int16).reshape(-1, 6)
        channel_0 = audio_array[:, 0]
        if not self.is_streaming:
            for i in range(0, len(channel_0), self.porcupine_frame_length):
                porcupine_chunk = channel_0[i:i + self.porcupine_frame_length]
                
                if len(porcupine_chunk) == self.porcupine_frame_length:
                    result = self.porcupine.process(porcupine_chunk)
                    if result >= 0:
                        trace_id = set_trace_id()
                        logger.info("Wake word detected!", extra={"trace_id": trace_id})
                        self.pixel_ring.listen()
                        await self.send_message(message_type=WSMessages.CONTROL_TYPE.value, message=WSMessages.START_MSG.value)
                        self.start_silence_detection()
                        self.is_streaming = True
                        break
        else:
            if self.is_streaming:
                await self.stream_audio_chunk(channel_0.tobytes())


    async def connect_websocket(self):
        try:
            self.ws = await websockets.connect(f'ws://{self.stt_ip}:{self.stt_port}')
            logger.info("Successfully connected to Speech-To-Text WebSocket")
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket: {e}")
            raise

    @with_trace
    async def send_message(self, message_type: str, message):
        trace_id = get_trace_id()
        try:
            if self.ws and message_type == WSMessages.CONTROL_TYPE.value:
                wsmessage = json.dumps({"type": message_type, "message": message, "source_ip": config.IP_ADDRESS, "trace_id": trace_id})
                await self.ws.send(wsmessage)
            elif self.ws and message_type == WSMessages.AUDIO_TYPE.value:
                #wsmessage = json.dumps({"type": message_type, "message": message})
                await self.ws.send(message) #Cant encode the raw audio bytes to json
            if not self.ws:
                logger.error("WebSocket not connected")
        except Exception as e:
            logger.error(f"Error sending message: {e}")

    async def stream_audio_chunk(self, audio_chunk):
        if self.ws:
            logger.debug("Sending audio chunk")
            await self.send_message(WSMessages.AUDIO_TYPE.value, audio_chunk)
        else:
            logger.error("Audio WebSocket not connected")

    def start_silence_detection(self):
        if self.silence_task is None or self.silence_task.done():
            self.silence_task = asyncio.create_task(self.silence_detection())

    async def silence_detection(self):
        silence_duration = 0
        while self.is_streaming:
            if self.respeaker:
                future = self.executor.submit(self.respeaker.is_voice)
                is_voice = await asyncio.wrap_future(future)
                if not is_voice:
                    silence_duration += 0.1
                    if silence_duration >= config.NO_VOICE_TRIGGER:
                        logger.info(f"Silence detected for {config.NO_VOICE_TRIGGER} seconds. Stopping stream.")
                        self.pixel_ring.think()
                        self.is_streaming = False
                        while not self.audio_queue.empty():
                            try:
                                self.audio_queue.get_nowait()
                            except queue.Empty:
                                break
                        await self.send_message(WSMessages.CONTROL_TYPE.value, WSMessages.STOP_MSG.value)
                        break
                else:
                    silence_duration = 0
            await asyncio.sleep(0.1)
        logger.info("Silence detection task ended")

    @with_trace
    async def listener(self, websocket):
        self.ws = websocket
        while True:
            try:
                msg = await self.ws.recv()
                msg = json.loads(msg)
                if 'trace_id' in msg:
                    trace_id = msg['trace_id']
                else:
                    trace_id = get_trace_id()
                if 'url' in msg:
                    url = msg['url']
                    logger.info(f"Received audio playback request via URL: {msg}")
                    self.pixel_ring.speak()
                    await self.speaker.play_audio(url, trace_id)
                    self.pixel_ring.off()
                    await asyncio.sleep(0.1)
                else:
                    logger.info(f"Received message: {msg}")
                    self.pixel_ring.off()
            except json.JSONDecodeError as e:
                pass # Probably some websocket protocol message
            except Exception as e:
                logger.error(f"Error: {e}") # Log in case I'm wrong
                pass # but probably still some websocket protocol message

    async def run(self):
        try:
            await self.connect_websocket()
            self.open_stream()
            self.stream.start_stream()
            await asyncio.gather(self.process_audio_queue(), self.listener(self.ws))

        finally:
            logger.info("Cleaning up resources...")
            await self.speaker.stop()
            if self.silence_task:
                self.silence_task.cancel()
            self.stream.stop_stream()
            self.stream.close()
            self.audio.terminate()
            await self.ws.close()
            self.respeaker.close()
            self.executor.shutdown(wait=False)

async def main():
    audio = AudioController()
    try:
        await audio.run()
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received. Shutting down...")

if __name__ == "__main__":
    asyncio.run(main())
