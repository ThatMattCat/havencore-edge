# -*- coding: utf-8 -*-
"""
Keyword spotting using pocketsphinx
"""
import os
import threading
import queue
from typing import Callable, Optional
from voice_engine.element import Element
from pocketsphinx import Pocketsphinx

class KWS(Element):
    def __init__(self, kws_list: Optional[str] = None, hmm_path: Optional[str] = None, dict_path: Optional[str] = None):
        super(KWS, self).__init__()
        self.queue = queue.Queue()
        self.on_detected: Optional[Callable[[str], None]] = None
        self.done = False
        self.kws_list = kws_list
        self.hmm_path = hmm_path
        self.dict_path = dict_path

    def put(self, data: bytes) -> None:
        self.queue.put(data)

    def start(self) -> None:
        self.done = False
        thread = threading.Thread(target=self.run)
        thread.daemon = True
        thread.start()

    def stop(self) -> None:
        self.done = True

    def set_callback(self, callback: Callable[[str], None]) -> None:
        self.on_detected = callback

    def run(self) -> None:
        if not self.hmm_path:
            self.hmm_path = os.path.join(os.path.dirname(__file__), '..', '..', 'lib', 'python3.11', 'site-packages', 'pocketsphinx', 'model', 'en-us', 'en-us')
        if not self.dict_path:
            self.dict_path = os.path.join(os.path.dirname(__file__), '..', '..', 'lib', 'python3.11', 'site-packages', 'pocketsphinx', 'model', 'en-us', 'cmudict-en-us.dict')
        if not self.kws_list:
            self.kws_list = os.path.join(os.path.dirname(__file__), 'pocketsphinx-data', 'keywords.txt')

        config = {
            'hmm': self.hmm_path,
            'dict': self.dict_path,
            'kws': self.kws_list,
        }

        ps = Pocketsphinx(**config)
        ps.start_utt()

        while not self.done:
            data = self.queue.get()
            ps.process_raw(data, False, False)
            hyp = ps.get_hyp()
            if hyp:
                keyword = hyp[0]
                if callable(self.on_detected):
                    self.on_detected(keyword)
                ps.end_utt()
                ps.start_utt()
            super(KWS, self).put(data)


def main():
    import time
    from .source import Source

    src = Source()
    kws = KWS()
    src.link(kws)

    def on_detected(keyword):
        print(f'Found keyword: {keyword}')

    kws.set_callback(on_detected)
    kws.start()
    src.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        kws.stop()
        src.stop()

if __name__ == '__main__':
    main()
