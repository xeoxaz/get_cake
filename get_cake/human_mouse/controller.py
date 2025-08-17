import math
import random
import time
from dataclasses import dataclass
from typing import Iterable, List, Tuple

import pyautogui as pag


@dataclass
class SpeedProfile:
    name: str
    px_per_sec: float


SPEEDS = {
    "slow": SpeedProfile("slow", 400.0),
    "normal": SpeedProfile("normal", 900.0),
    "fast": SpeedProfile("fast", 1600.0),
}


class HumanMouse:
    """Human-like mouse controller.

    Methods:
        move_to(x, y, speed="normal", jitter=1.5): Smoothly move to (x, y)
        left_click(): Left click at current position
        right_click(): Right click at current position
    wait(seconds): Pause for the given number of seconds
    press_key(key): Press a keyboard key (e.g., 'x')
    press_x(): Convenience wrapper to press 'x'
    """

    def __init__(self) -> None:
        pag.FAILSAFE = True
        pag.PAUSE = 0

    def left_click(self) -> None:
        pag.click(button="left")

    def right_click(self) -> None:
        pag.click(button="right")

    def wait(self, seconds: float) -> None:
        """Pause execution for the given seconds (non-negative)."""
        try:
            secs = float(seconds)
        except Exception:
            secs = 0.0
        if secs < 0:
            secs = 0.0
        time.sleep(secs)

    def press_key(self, key: str) -> None:
        """Press a keyboard key once.

        Example: press_key('x')
        """
        try:
            pag.press(key)
        except Exception as e:
            raise ValueError(f"Unsupported or invalid key: {key}") from e

    def press_x(self) -> None:
        """Press the 'x' key once (convenience)."""
        self.press_key('x')

    def move_to(
        self,
        x: int,
        y: int,
        speed: str = "normal",
        jitter: float = 1.5,
        duration_seconds: "float | None" = None,
        easing: str = "smooth",
    ) -> None:
        """Smoothly move cursor to (x, y) with human-like motion.

        Parameters:
        - speed: named speed profile
        - jitter: lateral randomness scale
        - duration_seconds: override total move time
        - easing:
            'smooth' (default): slow start, faster middle, slow end (S-curve)
            'dash': quick start, progressively slow near target (ease-out)
            'linear': constant pace
        """
        screen_w, screen_h = pag.size()
        tx = max(0, min(int(x), screen_w - 1))
        ty = max(0, min(int(y), screen_h - 1))

        sx, sy = pag.position()
        if (sx, sy) == (tx, ty):
            return

        sp = SPEEDS.get(speed, SPEEDS["normal"])
        path = self._generate_path((sx, sy), (tx, ty), jitter=jitter)

        total_dist = sum(
            math.hypot(path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1])
            for i in range(len(path) - 1)
        )
        if duration_seconds is not None:
            try:
                total_time = max(0.02, float(duration_seconds))
            except Exception:
                total_time = max(0.08, total_dist / sp.px_per_sec)
        else:
            total_time = max(0.08, total_dist / sp.px_per_sec)

        steps = len(path)
        start_time = time.perf_counter()
        for i, (px, py) in enumerate(path):
            t = i / max(1, steps - 1)
            # Easing function selection
            if easing == "dash":
                # Ease-out (fast start, slow end)
                eased = 1 - (1 - t) ** 3
            elif easing == "linear":
                eased = t
            else:
                # Smooth S-curve (slow start, fast middle, slow end)
                eased = 1 / (1 + math.exp(-10 * (t - 0.5)))
            target_elapsed = eased * total_time

            while True:
                now = time.perf_counter()
                if now - start_time >= target_elapsed:
                    break
                time.sleep(0.001)

            pag.moveTo(int(px), int(py))

    def _generate_path(
        self,
        start: Tuple[int, int],
        end: Tuple[int, int],
        jitter: float = 1.5,
    ) -> List[Tuple[float, float]]:
        sx, sy = start
        ex, ey = end

        dx, dy = ex - sx, ey - sy
        dist = math.hypot(dx, dy)
        if dist < 1:
            return [(ex, ey)]

        nx, ny = (0.0, 0.0)
        if dist > 0:
            nx, ny = (-dy / dist, dx / dist)
        lateral = min(80.0, 0.12 * dist) * (0.5 + random.random())
        if random.random() < 0.5:
            lateral = -lateral
        c1 = (sx + dx * 0.33 + nx * lateral * 0.6, sy + dy * 0.33 + ny * lateral * 0.6)
        c2 = (sx + dx * 0.66 + nx * lateral, sy + dy * 0.66 + ny * lateral)
        samples = max(20, min(220, int(dist / 5)))
        pts: List[Tuple[float, float]] = []
        for i in range(samples + 1):
            t = i / samples
            x = (
                (1 - t) ** 3 * sx
                + 3 * (1 - t) ** 2 * t * c1[0]
                + 3 * (1 - t) * t ** 2 * c2[0]
                + t ** 3 * ex
            )
            y = (
                (1 - t) ** 3 * sy
                + 3 * (1 - t) ** 2 * t * c1[1]
                + 3 * (1 - t) * t ** 2 * c2[1]
                + t ** 3 * ey
            )

            fade = (math.sin(math.pi * t)) ** 1.5
            jmag = jitter * (0.5 + random.random()) * fade
            x += nx * jmag * random.uniform(-1, 1)
            y += ny * jmag * random.uniform(-1, 1)

            pts.append((x, y))

        dedup: List[Tuple[float, float]] = []
        last = None
        for p in pts:
            ip = (round(p[0], 1), round(p[1], 1))
            if ip != last:
                dedup.append(p)
                last = ip
        if dedup[-1] != (ex, ey):
            dedup[-1] = (ex, ey)
        return dedup
