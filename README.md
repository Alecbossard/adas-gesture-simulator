# ADAS Gesture Simulator

Small toy project to demonstrate basic Advanced Driver Assistance Systems (ADAS) behaviour using Python, OpenCV and MediaPipe.

The goal is not to be physically accurate, but to show how you can prototype:
- longitudinal control (ACC-style following),
- lateral control (lane keeping assistance),
- simple safety logic for lane changes,
- a webcam-based HMI using hand gestures.

## Project structure

- `adas_webcam_demo.py`  
  Webcam demo: hand-gesture control of ADAS modes + mini HUD.

- `adas_simulation_2cars.py`  
  Pure 2D simulation with two vehicles moving on a 3‑lane road.

- `requirements.txt`  
  Python dependencies for both demos.

---

## 1. Requirements and setup

Recommended:
- **Python 3.11** (MediaPipe is not yet available for 3.13 at the time this project was written)
- A virtual environment (`.venv` or similar)

Install dependencies:

```bash
pip install -r requirements.txt
```

`requirements.txt` contains:

```text
opencv-python
mediapipe
numpy
```

---

## 2. Webcam demo – `adas_webcam_demo.py`

This script:

- opens the webcam,
- uses **MediaPipe Hands** to detect one hand and count extended fingers,
- maps the number of fingers to an ADAS mode,
- draws a mini “ADAS dashboard” on top of the webcam image.

### ADAS modes (gesture-controlled)

Number of lifted fingers → mode:

- **0 fingers or no hand** → `MANUAL`
- **1 finger** → `ACC` (Adaptive Cruise Control)
- **2 fingers** → `LKA` (Lane Keeping Assist)
- **3 fingers** → `EMERGENCY` (emergency braking)
- **4 or 5 fingers** → treated as `MANUAL` (fallback)

The HUD shows:
- ego vehicle (you),
- a target vehicle in front,
- lane lines,
- current mode,
- additional messages (e.g. “Distance mini atteinte”, “BRAKE!”).

### Longitudinal behaviour (simplified)

- In `MANUAL` mode, ego just moves with a fixed nominal speed.
- In `ACC` mode:
  - if ego is in the same lane and behind the target, and the distance is below a threshold,  
    → ego speed is matched to the target’s speed (simple constant-distance following).
- In `EMERGENCY` mode, ego speed is set to zero (full stop).

### Lateral behaviour & lane changes

Keyboard is still used to show lateral behaviour:

- `q` or **left arrow**  
  - In `LKA`: ego drifts towards the left lane line, then automatically returns to the centre of its lane (shows the system “correcting” the driver).
  - In other modes: ego requests a lane change to the left if possible.
- `d` or **right arrow**  
  - Symmetric to `q` but on the right side.

A simple **lateral safety** mechanism is implemented:

- If you try to change lane into a lane where the target vehicle is “next to you” (similar longitudinal coordinate),
  - the lane change is blocked,
  - the system only performs the lane-keeping style correction (drift towards the line, then back).

Other useful key:

- `ESC` → quit.

---

## 3. 2D simulation demo – `adas_simulation_2cars.py`

This script does not use the webcam.  
It creates a simple 2D top-view scene:

- a 3‑lane road,
- one **ego vehicle**,
- one **target vehicle** in front.

Both vehicles move in the longitudinal direction, with:
- a constant speed for the target,
- a driver-adjustable speed for the ego (plus ADAS logic on top).

### Coordinates and motion model

- Longitudinal positions are represented by **normalised coordinates** in `[0, 1]`:
  - `0` = top of the screen,
  - `1` = bottom of the screen.
- Speeds are small negative values (moving upwards on the screen).
- When a vehicle goes off the top (`position < 0`), it is respawned at the bottom (`position = 1`).

Ego “commanded” speed:

- `v_ego_base` is the speed requested by the driver (modified by the keyboard).
- The actual speed `v_ego` used at each step depends on the ADAS mode.

Target speed:

- `v_cible` is constant and independent of the driver.

### ADAS modes (keyboard-controlled)

Press one of:

- `0` → `MANUEL`
- `1` → `ACC`
- `2` → `LKA`
- `3` → `EMERGENCY`

Current mode is displayed in the HUD.

#### Longitudinal control (ACC / EMERGENCY)

- `MANUEL`:
  - ego simply uses `v_ego_base`.

- `ACC`:
  - if ego is in the **same lane** and **behind** the target:
    - if the distance is larger than a threshold → ego uses `v_ego_base` (catching up).
    - if the distance is **below** the threshold → ego speed is set to **match the target speed** `v_cible` (simple constant gap following).
  - if not in the same lane, ACC does not act → ego uses `v_ego_base`.

- `EMERGENCY`:
  - ego speed is forced to `0.0`.

The HUD shows when the “minimal distance” condition is active.

#### Lateral control (lane change, LKA, lateral safety)

Lateral motion is handled in three phases:
- `"idle"` → no special lateral effect,
- `"out"` → drift towards a lane boundary,
- `"back"` → return to the lane centre.

Keyboard:

- `q` or left arrow:
  - In `LKA`:
    - trigger `"out"` toward the left lane line, then `"back"` to the centre of the same lane.
    - This visually shows the system “fighting” the driver and bringing the car back inside the lane.
  - In other modes:
    - if the target lane on the left is **free**, start a smooth lane change to that lane,
    - if the target lane is **occupied** by the front car at similar longitudinal position,  
      → perform only the correction (drift + back) instead of a real lane change.

- `d` or right arrow:
  - exact same logic on the right side.

The function:

```python
def voie_bloquee(target_lane):
    return (
        target_lane == indice_voie_cible and
        abs(position_relative_ego - position_relative_cible) <= seuil_blocage_lateral
    )
)
```

encodes the “car next to you” logic for lateral safety.

### Speed control for the ego (driver input)

You can change the commanded ego speed on the fly:

- `z` → **accelerate** ego (`v_ego_base` becomes more negative, up to a limit),
- `s` → **slow down** ego (`v_ego_base` becomes less negative, down to a minimum).

This does **not** affect the target speed; it only changes the driver command, on top of which ACC / EMERGENCY may still act.

### Other keys

- `ESC` → quit the simulation window.

---

## 4. Limitations and possible extensions

This is a deliberately simple demo, meant to be used as an interview / teaching support:

- No real vehicle dynamics (no steering angle, no acceleration model).
- No physical units (everything is expressed in normalised screen coordinates).
- No real sensor model (positions are known exactly).

Possible extensions:

- Add simple noise on the positions to mimic sensor uncertainty.
- Add more vehicles and more complex scenarios (cut-in, cut-out, etc.).
- Log the trajectories and analyse them in a Jupyter notebook.
- Replace the hand-gesture mode selection with a simple GUI or joystick.

---

## 5. Running the demos

In a virtual environment:

```bash
pip install -r requirements.txt
```

Then:

- For the webcam + gestures demo:

```bash
python adas_webcam_demo.py
```

- For the 2D two-cars simulation:

```bash
python adas_simulation_2cars.py
```

Make sure your webcam is accessible for the first script, and that you run this on Python 3.11 (or any version supported by the `mediapipe` wheel you use).
