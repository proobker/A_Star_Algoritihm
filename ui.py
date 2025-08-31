# ui.py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider
from typing import List, Tuple

from astar import a_star, idx_to_rc
from image_utils import load_image_as_array, make_walkable_mask
from state import State

AUTO_THRESHOLD = True
THRESH = 180
ANIM_INTERVAL_MS = 16


def run_visualizer(path: str):
    """
    Run the interactive pathfinder UI for a single image path.
    This function is self-contained and avoids module-level side effects by
    keeping mutable UI flags (like `invert`) local and using `nonlocal`.
    """

    # local UI flags (no globals)
    invert = False

    gray = load_image_as_array(path)
    H, W = gray.shape
    walk = make_walkable_mask(gray, invert, AUTO_THRESHOLD, THRESH)

    # --- Setup Matplotlib Figure ---
    fig, ax = plt.subplots()
    try:
        fig.canvas.manager.set_window_title("Path Finder") # type: ignore
    except Exception:
        pass

    plt.subplots_adjust(bottom=0.22)
    ax.set_title(
        "Left-click START & GOAL. Keys: i=invert, I=invert+recalc, "
        "r=reset, R=reopen, u=undo, +/- speed, q=quit"
    )
    ax.imshow(gray, cmap="gray", interpolation="nearest")
    overlay = ax.imshow(np.where(walk, 255, 0), cmap="autumn", alpha=0.15, interpolation="nearest")
    pts_scatter = ax.scatter([], [], s=50, c="blue")

    # --- Speed Slider ---
    ax_speed = plt.axes([0.15, 0.06, 0.7, 0.03]) # type: ignore
    speed_slider = Slider(ax_speed, "Speed", 1, 200, valinit=10, valstep=1)

    picked: List[Tuple[float, float]] = []
    state = State(speed_slider)

    # --- Helper functions ---
    def refresh_overlay():
        nonlocal walk
        newmask = make_walkable_mask(gray, invert, AUTO_THRESHOLD, THRESH)
        overlay.set_data(np.where(newmask, 255, 0))
        fig.canvas.draw_idle()

    def clear_visuals(keep_points=False):
        # stop & clear animation elements
        if state.anim is not None and getattr(state.anim, "event_source", None) is not None:
            state.anim.event_source.stop()
        state.anim = None

        if state.path_line is not None:
            try:
                state.path_line.remove()
            except Exception:
                pass
            state.path_line = None

        if state.travel_dot is not None:
            try:
                state.travel_dot.remove()
            except Exception:
                pass
            state.travel_dot = None

        if state.exp_scatter is not None:
            try:
                state.exp_scatter.remove()
            except Exception:
                pass
            state.exp_scatter = None

        state.phase = "idle"
        state.running = False
        state.exp_index = 0
        state.path_index = 0

        if not keep_points:
            picked.clear()
            pts_scatter.set_offsets(np.empty((0, 2)))
            pts_scatter.set_color("blue")

        ax.set_title(
            "Left-click START & GOAL. Keys: i=invert, I=invert+recalc, "
            "r=reset, R=reopen, u=undo, +/- speed, q=quit"
        )
        fig.canvas.draw_idle()

    def compute_and_start():
        nonlocal walk
        if len(picked) < 2:
            return
        (x0, y0), (x1, y1) = picked
        start_rc = (int(round(y0)), int(round(x0)))
        goal_rc = (int(round(y1)), int(round(x1)))

        # recompute mask with current invert setting
        walk = make_walkable_mask(gray, invert, AUTO_THRESHOLD, THRESH)

        path_rc, expanded_nodes = a_star(walk, start_rc, goal_rc)
        if path_rc is None:
            ax.set_title("No path found. Adjust threshold/invert, then try again.")
            fig.canvas.draw_idle()
            return

        state.path_rc = path_rc
        state.expanded_rc = [idx_to_rc(i, W) for i in expanded_nodes]

        # create artists
        state.path_line, = ax.plot([], [], linewidth=2.5, color="cyan") # type: ignore
        state.travel_dot, = ax.plot([], [], marker="o", color="red", markersize=6) # type: ignore
        state.exp_scatter = ax.scatter([], [], s=5, c="yellow", alpha=0.6) # type: ignore

        def init_anim():
            state.path_line.set_data([], []) # type: ignore
            state.travel_dot.set_data([], []) # type: ignore
            state.exp_scatter.set_offsets(np.empty((0, 2))) # type: ignore
            return state.path_line, state.travel_dot, state.exp_scatter

        def update(_):
            if not state.running:
                return state.path_line, state.travel_dot, state.exp_scatter

            if state.phase == "expand":
                start = state.exp_index
                end = min(start + state.expand_step, len(state.expanded_rc))
                if end > start:
                    batch = state.expanded_rc[start:end]
                    old = state.exp_scatter.get_offsets() # type: ignore
                    add = np.array([[c, r] for r, c in batch])
                    new = np.vstack([old, add]) if old.size else add
                    state.exp_scatter.set_offsets(new) # type: ignore
                    state.exp_index = end
                if state.exp_index >= len(state.expanded_rc):
                    state.phase = "path"

            elif state.phase == "path":
                rr, cc = zip(*state.path_rc)
                state.path_index = min(state.path_index + state.path_step, len(state.path_rc) - 1)
                state.path_line.set_data(cc[: state.path_index + 1], rr[: state.path_index + 1]) # type: ignore
                state.travel_dot.set_data([cc[state.path_index]], [rr[state.path_index]]) # type: ignore
                if state.path_index >= len(state.path_rc) - 1:
                    state.running = False
                    if state.anim and getattr(state.anim, "event_source", None):
                        state.anim.event_source.stop()

            return state.path_line, state.travel_dot, state.exp_scatter

        def frame_gen():
            while state.running:
                yield 0

        # start animation
        state.phase = "expand"
        state.exp_index = 0
        state.path_index = 0
        state.running = True
        state.expand_step = int(speed_slider.val)
        state.path_step = max(1, int(speed_slider.val))
        state.anim = FuncAnimation(
            fig,
            update, # type: ignore
            init_func=init_anim, # type: ignore
            frames=frame_gen,
            interval=ANIM_INTERVAL_MS,
            blit=True,
            repeat=False,
        )
        ax.set_title("Animating: yellow=explore, cyan=path. Keys: +/- speed, r reset, q quit")
        fig.canvas.draw_idle()

    # --- Event Handlers ---
    def on_click(event):
        if event.inaxes != ax or event.button != 1:
            return
        if state.running:
            return
        x, y = event.xdata, event.ydata
        if x is None or y is None:
            return
        picked.append((x, y))
        pts_scatter.set_offsets(np.array(picked))
        if len(picked) == 1:
            pts_scatter.set_color("blue")
            ax.set_title("Now pick GOAL. Keys: u undo, i invert")
        elif len(picked) == 2:
            pts_scatter.set_color(["blue", "red"])
            fig.canvas.draw_idle()
            compute_and_start()

    def adjust_speed(delta):
        val = int(speed_slider.val) + delta
        val = max(1, min(200, val))
        speed_slider.set_val(val)

    def on_speed_change(val):
        state.expand_step = int(val)
        state.path_step = max(1, int(val))
        # we keep the animation interval constant; speed controls steps per frame
        if state.anim and getattr(state.anim, "event_source", None):
            state.anim.event_source.interval = ANIM_INTERVAL_MS

    def on_key(event):
        nonlocal invert
        if event.key in ("q", "escape"):
            plt.close(fig)
        elif event.key == "r":
            clear_visuals()
        elif event.key == "R":
            def reopen(_):
                # reopen same image in new UI instance after close
                run_visualizer(path)
            fig.canvas.mpl_connect("close_event", reopen)
            plt.close(fig)
        elif event.key == "u":
            if picked:
                picked.pop()
                pts_scatter.set_offsets(np.array(picked) if picked else np.empty((0, 2)))
                pts_scatter.set_color("blue")
                fig.canvas.draw_idle()
        elif event.key == "i":
            invert = not invert
            refresh_overlay()
        elif event.key == "I":
            invert = not invert
            refresh_overlay()
            if len(picked) == 2:
                clear_visuals(keep_points=True)
                compute_and_start()
        elif event.key in ("+", "equal", "up", "right", "]"):
            adjust_speed(+5)
        elif event.key in ("-", "down", "left", "["):
            adjust_speed(-5)

    # --- Hook events ---
    speed_slider.on_changed(on_speed_change)
    fig.canvas.mpl_connect("button_press_event", on_click)
    fig.canvas.mpl_connect("key_press_event", on_key)

    ax.set_xlim([-0.5, W - 0.5]) # type: ignore
    ax.set_ylim([H - 0.5, -0.5]) # type: ignore
    ax.set_aspect("equal")
    plt.show()
