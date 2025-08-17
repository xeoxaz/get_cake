from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Literal, Optional, Set, Callable

from pynput import mouse as pmouse
from pynput import keyboard as pkeyboard

EventType = Literal[
    "move", "left_down", "left_up", "right_down", "right_up",
    "scroll", "key_down", "key_up"
]


@dataclass
class RecordedEvent:
    t: float
    type: EventType
    x: Optional[int] = None
    y: Optional[int] = None
    dx: Optional[int] = None
    dy: Optional[int] = None
    key: Optional[str] = None


class InputRecorder:

    def __init__(self, *, record_moves: bool = True, ignored_keys: Optional[Set[str]] = None, on_event: Optional[Callable[[RecordedEvent], None]] = None) -> None:
        self._start: Optional[float] = None
        self._events: List[RecordedEvent] = []
        self._mouse_listener: Optional[pmouse.Listener] = None
        self._keyboard_listener: Optional[pkeyboard.Listener] = None
        self._record_moves = record_moves
        self._ignored_keys = {k.lower() for k in (ignored_keys or set())}
        self._on_event = on_event

    def start(self) -> None:
        if self._start is not None:
            return
        self._events.clear()
        self._start = time.perf_counter()

        def now() -> float:
            assert self._start is not None
            return time.perf_counter() - self._start

        def _emit(ev: RecordedEvent):
            self._events.append(ev)
            if self._on_event:
                try:
                    self._on_event(ev)
                except Exception:
                    pass

        def on_move(x, y):
            if self._record_moves:
                _emit(RecordedEvent(now(), "move", x=int(x), y=int(y)))

        def on_click(x, y, button, pressed):
            if button == pmouse.Button.left:
                ev = "left_down" if pressed else "left_up"
            elif button == pmouse.Button.right:
                ev = "right_down" if pressed else "right_up"
            else:
                ev = None
            if ev:
                _emit(RecordedEvent(now(), ev, x=int(x), y=int(y)))

        def on_scroll(x, y, dx, dy):
            _emit(RecordedEvent(now(), "scroll", x=int(x), y=int(y), dx=int(dx), dy=int(dy)))

        def key_to_str(key) -> str:
            try:
                return key.char if hasattr(key, 'char') and key.char is not None else str(key).split('.')[-1]
            except Exception:
                return str(key)

        def on_key_press(key):
            k = key_to_str(key)
            if k and k.lower() in self._ignored_keys:
                return
            _emit(RecordedEvent(now(), "key_down", key=k))

        def on_key_release(key):
            k = key_to_str(key)
            if k and k.lower() in self._ignored_keys:
                return
            _emit(RecordedEvent(now(), "key_up", key=k))

        self._mouse_listener = pmouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll)
        self._keyboard_listener = pkeyboard.Listener(on_press=on_key_press, on_release=on_key_release)
        self._mouse_listener.start()
        self._keyboard_listener.start()

    def stop(self) -> List[RecordedEvent]:
        if self._mouse_listener:
            self._mouse_listener.stop()
            self._mouse_listener = None
        if self._keyboard_listener:
            self._keyboard_listener.stop()
            self._keyboard_listener = None
        self._start = None
        return list(self._events)

    def save(self, path: str) -> None:
        data = [asdict(e) for e in self._events]
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({"events": data, "version": 1}, f, ensure_ascii=False, indent=2)

    @staticmethod
    def load(path: str) -> List[RecordedEvent]:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        events = data.get("events", [])
        out: List[RecordedEvent] = []
        for e in events:
            out.append(RecordedEvent(
                t=float(e.get('t', 0)),
                type=e.get('type'),
                x=e.get('x'), y=e.get('y'),
                dx=e.get('dx'), dy=e.get('dy'),
                key=e.get('key'),
            ))
        return out
