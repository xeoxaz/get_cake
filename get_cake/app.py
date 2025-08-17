import os
import threading
import time
from typing import List

import pyautogui as pag

from human_mouse import HumanMouse, InputRecorder

HOTKEYS = {
    'record': 'r',
    'stop': 's',
    'play': 'p',
    'clear': 'c',
    'loop': 'l',
}

STATE_IDLE = 'idle'
STATE_RECORDING = 'recording'
STATE_PLAYING = 'playing'


class App:
    def __init__(self):
        self.mouse = HumanMouse()
        self.loop = False
        self._save_path = os.path.join(os.path.dirname(__file__), 'last_recording.json')
        self.recorder = InputRecorder(
            record_moves=False,
            ignored_keys=set(HOTKEYS.values()),
            on_event=self._on_record_event,
        )
        self.state = STATE_IDLE
        self.events: List[dict] = []
        self._play_thread: threading.Thread | None = None
        self._stop_play = threading.Event()

    def start(self):
        print("App ready. Hotkeys: [r]=record, [s]=stop, [p]=play, [c]=clear, [l]=loop toggle. Move mouse to top-left to abort.")
        from pynput import keyboard

        def on_press(key):
            try:
                k = key.char.lower() if hasattr(key, 'char') and key.char else None
            except Exception:
                k = None
            if k == HOTKEYS['record'] and self.state != STATE_RECORDING:
                self._start_recording()
            elif k == HOTKEYS['stop'] and self.state == STATE_RECORDING:
                self._stop_recording()
            elif k == HOTKEYS['play'] and self.state != STATE_RECORDING:
                self._start_playback()
            elif k == HOTKEYS['clear'] and self.state != STATE_RECORDING:
                self._clear()
            elif k == HOTKEYS['loop'] and self.state != STATE_RECORDING:
                self.loop = not self.loop
                print(f"Loop mode: {'ON' if self.loop else 'OFF'}")
            elif k == HOTKEYS['stop'] and self.state == STATE_PLAYING:
                self._stop_playback()

        with keyboard.Listener(on_press=on_press) as listener:
            try:
                listener.join()
            except KeyboardInterrupt:
                pass

    def _start_recording(self):
        self.recorder = InputRecorder(
            record_moves=False,
            ignored_keys=set(HOTKEYS.values()),
            on_event=self._on_record_event,
        )
        self.recorder.start()
        self.state = STATE_RECORDING
        print("Recording... [s] to stop")

    def _stop_recording(self):
        evs = self.recorder.stop()
        self.events = [
            {"t": e.t, "type": e.type, "x": e.x, "y": e.y, "dx": e.dx, "dy": e.dy, "key": e.key}
            for e in evs
        ]
        try:
            self.recorder.save(self._save_path)
            print(f"Saved recording to: {self._save_path}")
        except Exception as e:
            print(f"Failed to save recording: {e}")
        self.state = STATE_IDLE
        print(f"Recorded {len(self.events)} events.")

    def _playback_worker(self):
        print(f"Playing {len(self.events)} events... (loop={'ON' if self.loop else 'OFF'})")
        while not self._stop_play.is_set():
            # Optionally refresh events from save file each loop iteration
            if self._save_path and os.path.exists(self._save_path):
                try:
                    loaded = InputRecorder.load(self._save_path)
                    self.events = [
                        {"t": e.t, "type": e.type, "x": e.x, "y": e.y, "dx": e.dx, "dy": e.dy, "key": e.key}
                        for e in loaded
                    ]
                except Exception as e:
                    print(f"Failed to load saved recording: {e}")

            if not self.events:
                print("No events to play.")
                break

            first = self.events[0]
            # Pre-position to the start; don't count pre-move time into event schedule
            if first.get('x') is not None and first.get('y') is not None:
                pag.moveTo(int(first['x']), int(first['y']))

            # Reset time baseline AFTER pre-move so relative timings align exactly
            t_offset = float(first.get('t', 0.0))
            t0 = time.perf_counter()

            # Lerp mouse between action points: aim to arrive at the event timestamp.
            for e in self.events:
                if self._stop_play.is_set():
                    break
                t_event = float(e.get('t', 0)) - t_offset
                etype = e.get('type')
                ex = e.get('x')
                ey = e.get('y')

                # Time until this event
                elapsed = time.perf_counter() - t0
                dt = max(0.0, t_event - elapsed)

                # If we have coordinates, move smoothly and arrive before the action, then wait until event time
                if ex is not None and ey is not None:
                    if dt > 0.02:
                        move_dur = min(0.8, dt * 0.8)
                        self.mouse.move_to(int(ex), int(ey), duration_seconds=move_dur, jitter=1.0, easing="dash")
                        wait_left = max(0.0, dt - move_dur)
                        deadline = time.perf_counter() + wait_left
                        while time.perf_counter() < deadline and not self._stop_play.is_set():
                            time.sleep(0.005)
                        if self._stop_play.is_set():
                            break
                    else:
                        # No time to lerp: still prefer a slight ease-out hop
                        self.mouse.move_to(int(ex), int(ey), duration_seconds=0.02, jitter=0.0, easing="dash")
                else:
                    # No coordinates: wait until event time (with stop responsiveness)
                    deadline = time.perf_counter() + dt
                    while time.perf_counter() < deadline and not self._stop_play.is_set():
                        time.sleep(0.005)
                    if self._stop_play.is_set():
                        break

                # Perform the event action at its timestamp
                if etype == 'left_down':
                    pag.mouseDown(button='left', x=int(e.get('x', 0)), y=int(e.get('y', 0)))
                elif etype == 'left_up':
                    pag.mouseUp(button='left', x=int(e.get('x', 0)), y=int(e.get('y', 0)))
                elif etype == 'right_down':
                    pag.mouseDown(button='right', x=int(e.get('x', 0)), y=int(e.get('y', 0)))
                elif etype == 'right_up':
                    pag.mouseUp(button='right', x=int(e.get('x', 0)), y=int(e.get('y', 0)))
                elif etype == 'scroll':
                    pag.scroll(int(e.get('dy', 0)))
                elif etype == 'key_down':
                    pag.keyDown(str(e.get('key', '')))
                elif etype == 'key_up':
                    pag.keyUp(str(e.get('key', '')))
            if self._stop_play.is_set():
                break
            if not self.loop:
                break
            # Pause before next loop iteration to avoid immediate restart
            print("Looping again in 6 seconds... [s] to stop")
            deadline = time.perf_counter() + 6.0
            while not self._stop_play.is_set() and time.perf_counter() < deadline:
                time.sleep(0.05)
        print("Playback ended.")
        self.state = STATE_IDLE

    def _start_playback(self):
        if not self.events:
            can_load = self._save_path and os.path.exists(self._save_path)
            if not can_load:
                print("Nothing to play.")
                return
        if self._play_thread and self._play_thread.is_alive():
            print("Already playing.")
            return
        self.state = STATE_PLAYING
        self._stop_play.clear()
        self._play_thread = threading.Thread(target=self._playback_worker, daemon=True)
        self._play_thread.start()

    def _clear(self):
        self.events = []
        print("Cleared recorded events.")

    def _stop_playback(self):
        if self._play_thread and self._play_thread.is_alive():
            print("Stopping playback...")
            self._stop_play.set()
            self._play_thread.join(timeout=2.0)
        self.state = STATE_IDLE

    def _on_record_event(self, ev):
        if ev.type.startswith('left') or ev.type.startswith('right') or ev.type in ('scroll', 'key_down', 'key_up'):
            if ev.type in ('key_down', 'key_up'):
                print(f"[{ev.t:0.3f}] {ev.type} {ev.key}")
            elif ev.type == 'scroll':
                print(f"[{ev.t:0.3f}] scroll dy={ev.dy}")
            else:
                print(f"[{ev.t:0.3f}] {ev.type} @({ev.x},{ev.y})")


if __name__ == "__main__":
    App().start()
