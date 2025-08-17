# get_cake — human-like mouse controller, recorder, and playback (Windows)

Human-like mouse movement and simple hotkey-driven recording/playback.

Highlights:
- Smooth, non-linear paths with subtle jitter for realism
- “Dash” movement style: quick start, slow near target
- Record clicks, scrolls, and key up/down (mouse moves optional) to JSON
- Hotkeys: r (record), s (stop), p (play), c (clear), l (loop)
- Loop playback resets timing correctly and waits 5 seconds between sessions

## Quick start

Windows launcher:

```bat
start.bat
```

This creates/activates a venv, installs deps, and starts the app.

Manual setup (PowerShell):

```pwsh
python -m venv .venv
. .venv/Scripts/Activate.ps1
pip install -r requirements.txt
python app.py
```

## Hotkeys (in the app)
- r: start recording (mouse clicks, scrolls, key up/down; motion not recorded by default)
- s: stop (recording or playback)
- p: play the last recording (from memory or last_recording.json)
- c: clear the last in-memory recording
- l: toggle loop mode (adds a 5s delay before each new loop)

Notes:
- Playback pre-positions to the first event, then preserves original event timings each loop.
- Move mouse to top-left corner to trigger PyAutoGUI failsafe.

## CLI demo (optional)

```pwsh
# Move with human-like motion
python demo.py move 800 500 --speed normal

# Record to a file (Ctrl+C to stop) and play
python demo.py record my_actions.json
python demo.py play my_actions.json
```

## Safety and permissions
- This controls your mouse and keyboard; save work first.
- Some environments (RDP/VMs) restrict input simulation.

## License
MIT
