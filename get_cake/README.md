# Human-like Mouse Controller (Windows/macOS/Linux)

A tiny Python app that moves and clicks the mouse in a human-like way:
- move_to(x, y): smooth, non-linear, slightly noisy path with variable speed
- left_click(): left mouse click at the current position
- right_click(): right mouse click at the current position
- wait(seconds): pause for a duration
- press_key(key): press a keyboard key once (e.g. 'x', 'enter')
- press_x(): convenience for 'x'

It uses a custom Bézier-based path generator plus subtle jitter to simulate natural motion.

## Install

Prerequisites:
- Python 3.8+
- pip

Install dependencies:

```pwsh
python -m venv .venv
. .venv/Scripts/Activate.ps1
pip install -r requirements.txt
```

Note: On Windows, pyautogui may install Pillow and other small deps automatically via pip.

## Use

Run a quick demo from the project root:

```pwsh
# Move to 800, 500 at normal speed
python demo.py move 800 500 --speed normal

# Left click
python demo.py left-click

# Right click
python demo.py right-click

# Wait 2.5 seconds
python demo.py wait 2.5

# Press keyboard keys
python demo.py press x
python demo.py press-x

# Record your actions to JSON (Ctrl+C to stop)
python demo.py record my_actions.json

# Play them back
python demo.py play my_actions.json

### Interactive hotkeys app
Start the app and control recording with hotkeys:

```pwsh
python app.py
```

Hotkeys:
- r: start recording (mouse clicks, scrolls, and key up/down; mouse motion is not recorded)
- s: stop (recording or playback)
- p: play the last recording
- c: clear the last recording
- l: toggle loop mode on playback

You’ll see minimal CLI feedback lines while recording (e.g., key_down x, left_down @(...)).

On Windows, you can start the app via the launcher:

```bat
start.bat
```
This will create/activate a venv if needed, install dependencies, and run the app.
```

Speeds: slow | normal | fast

Safety: pyautogui enables a failsafe—moving your mouse to the top-left corner (0,0) aborts execution.

## API

```python
from human_mouse.controller import HumanMouse
from human_mouse import InputRecorder

mouse = HumanMouse()
mouse.move_to(800, 500, speed="normal")
mouse.left_click()
mouse.right_click()
mouse.wait(2.5)
mouse.press_key('x')
mouse.press_x()

# Record programmatically
rec = InputRecorder()
rec.start()
# ... perform actions manually ...
events = rec.stop()
rec.save('my_actions.json')
```

Options:
- speed: "slow" | "normal" | "fast" (affects pixels-per-second target)
- jitter: strength of micro-variations orthogonal to the path (default 1.5)

## Notes
- This takes control of your mouse. Save your work first.
- If coordinates are off-screen, they will be clamped to your primary display bounds.
- Recording uses pynput and may not work inside restricted/remote environments.

## Troubleshooting
- If nothing happens, ensure the virtual environment is activated and installation succeeded.
- If you get import errors, try upgrading pip: `python -m pip install --upgrade pip` and reinstall.
- Some RDP/VM environments restrict input simulation; try running directly on the host OS.
- If recording doesn’t capture events, run VS Code as administrator on Windows or grant accessibility permissions on macOS.

## JSON schema (simplified)
{
	"version": 1,
	"events": [
		{ "t": 0.000, "type": "move", "x": 120, "y": 300 },
		{ "t": 0.115, "type": "left_down", "x": 120, "y": 300 },
		{ "t": 0.145, "type": "left_up", "x": 120, "y": 300 },
		{ "t": 0.420, "type": "key_down", "key": "x" },
		{ "t": 0.520, "type": "key_up", "key": "x" }
	]
}
