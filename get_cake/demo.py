import argparse
import time
from human_mouse import HumanMouse, InputRecorder


def main():
    parser = argparse.ArgumentParser(description="Human-like mouse demo")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_move = sub.add_parser("move", help="Move to x y")
    p_move.add_argument("x", type=int)
    p_move.add_argument("y", type=int)
    p_move.add_argument("--speed", choices=["slow", "normal", "fast"], default="normal")
    p_move.add_argument("--jitter", type=float, default=1.5)

    sub.add_parser("left-click", help="Left click")
    sub.add_parser("right-click", help="Right click")
    p_wait = sub.add_parser("wait", help="Wait seconds")
    p_wait.add_argument("seconds", type=float)

    p_press = sub.add_parser("press", help="Press a keyboard key once")
    p_press.add_argument("key", type=str, help="Key to press, e.g. x, enter, space, up")

    sub.add_parser("press-x", help="Press the 'x' key once")

    p_rec = sub.add_parser("record", help="Record mouse+keyboard to JSON until Ctrl+C")
    p_rec.add_argument("output", type=str, help="Path to write JSON events file")

    p_play = sub.add_parser("play", help="Play back a JSON recording")
    p_play.add_argument("input", type=str, help="Path to JSON events file")

    args = parser.parse_args()

    mouse = HumanMouse()

    if args.cmd == "move":
        mouse.move_to(args.x, args.y, speed=args.speed, jitter=args.jitter)
    elif args.cmd == "left-click":
        mouse.left_click()
    elif args.cmd == "right-click":
        mouse.right_click()
    elif args.cmd == "wait":
        mouse.wait(args.seconds)
    elif args.cmd == "press":
        mouse.press_key(args.key)
    elif args.cmd == "press-x":
        mouse.press_x()
    elif args.cmd == "record":
        rec = InputRecorder()
        print("Recording... press Ctrl+C to stop.")
        rec.start()
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            events = rec.stop()
            rec.save(args.output)
            print(f"Saved {len(events)} events to {args.output}")
    elif args.cmd == "play":
        import json, time, pyautogui as pag
        with open(args.input, 'r', encoding='utf-8') as f:
            data = json.load(f)
        events = data.get('events', [])
        print(f"Playing {len(events)} events...")
        t0 = None
        for e in events:
            t = float(e.get('t', 0))
            if t0 is None:
                t0 = time.perf_counter()
            else:
                # wait until t since start
                while time.perf_counter() - t0 < t:
                    time.sleep(0.001)
            etype = e.get('type')
            if etype == 'move':
                pag.moveTo(int(e['x']), int(e['y']))
            elif etype == 'left_down':
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
        print("Done.")


if __name__ == "__main__":
    main()
