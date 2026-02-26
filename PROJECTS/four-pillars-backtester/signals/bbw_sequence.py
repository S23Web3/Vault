"""
Layer 2: BBW Sequence Tracker — color transitions, direction, skip detection, pattern IDs.

Pure function. No side effects, no print(), no file I/O.
Input: DataFrame with Layer 1 columns: bbwp_spectrum, bbwp_state, bbwp_value.
Output: Same DataFrame with 9 new bbw_seq_ columns added.

Depends on: signals/bbwp.py (Layer 1) output.
"""

import numpy as np
import pandas as pd

# ─── Constants (4 colors matching Pine v2 gradient inflection at 25/50/75) ───

COLOR_ORDER = {'blue': 0, 'green': 1, 'yellow': 2, 'red': 3}
COLOR_LETTERS = {'blue': 'B', 'green': 'G', 'yellow': 'Y', 'red': 'R'}
VALID_COLORS = set(COLOR_ORDER.keys())

REQUIRED_COLS = ['bbwp_spectrum', 'bbwp_state', 'bbwp_value']

OUTPUT_COLS = [
    'bbw_seq_prev_color', 'bbw_seq_color_changed', 'bbw_seq_bars_in_color',
    'bbw_seq_bars_in_state', 'bbw_seq_direction', 'bbw_seq_skip_detected',
    'bbw_seq_pattern_id', 'bbw_seq_from_blue_bars', 'bbw_seq_from_red_bars',
]


def _sequence_direction(prev_color, curr_color):
    """Return 'expanding', 'contracting', or 'flat' based on color order transition."""
    if prev_color is None or curr_color is None:
        return None
    if prev_color == curr_color:
        return 'flat'
    return 'expanding' if COLOR_ORDER[curr_color] > COLOR_ORDER[prev_color] else 'contracting'


def _is_skip(prev_color, curr_color):
    """Return True if the transition skipped a color step (abs diff > 1)."""
    if prev_color is None or curr_color is None:
        return False
    return abs(COLOR_ORDER[curr_color] - COLOR_ORDER[prev_color]) > 1


def track_bbw_sequence(df: pd.DataFrame) -> pd.DataFrame:
    """Track BBWP color sequences, transitions, patterns, and distances.

    Input: DataFrame with Layer 1 columns: bbwp_spectrum, bbwp_state, bbwp_value.
    Output: Same DataFrame with 9 new bbw_seq_ columns added.
    """
    # Validate required columns
    for col in REQUIRED_COLS:
        if col not in df.columns:
            raise ValueError(f"Missing required Layer 1 column: {col}")

    result = df.copy()
    n = len(result)

    # Pre-allocate output arrays
    prev_color_arr = np.empty(n, dtype=object)
    color_changed_arr = np.zeros(n, dtype=bool)
    bars_in_color_arr = np.zeros(n, dtype=np.int64)
    bars_in_state_arr = np.zeros(n, dtype=np.int64)
    direction_arr = np.empty(n, dtype=object)
    skip_detected_arr = np.zeros(n, dtype=bool)
    pattern_id_arr = np.empty(n, dtype=object)
    from_blue_arr = np.full(n, np.nan)
    from_red_arr = np.full(n, np.nan)

    # Initialize defaults for NaN/None rows
    for i in range(n):
        prev_color_arr[i] = None
        direction_arr[i] = None
        pattern_id_arr[i] = ''

    # Stateful tracking variables
    last_color = None
    last_state = None
    current_color_count = 0
    current_state_count = 0
    last_blue_idx = -1  # -1 means never seen
    last_red_idx = -1
    recent_transitions = []  # max 3 color letters

    spectrums = result['bbwp_spectrum'].values
    states = result['bbwp_state'].values

    for i in range(n):
        spectrum = spectrums[i]
        state = states[i]

        # Skip None/NaN spectrum bars entirely
        if spectrum is None or (isinstance(spectrum, float) and np.isnan(spectrum)):
            prev_color_arr[i] = None
            color_changed_arr[i] = False
            bars_in_color_arr[i] = 0
            bars_in_state_arr[i] = 0
            direction_arr[i] = None
            skip_detected_arr[i] = False
            pattern_id_arr[i] = ''
            from_blue_arr[i] = np.nan
            from_red_arr[i] = np.nan
            continue

        # Valid spectrum bar — track it
        prev_color_arr[i] = last_color

        # Color tracking
        if last_color is None:
            # First valid bar
            color_changed_arr[i] = False
            current_color_count = 1
            direction_arr[i] = None
            skip_detected_arr[i] = False
            recent_transitions.append(COLOR_LETTERS.get(spectrum, '?'))
        elif spectrum != last_color:
            # Color changed
            color_changed_arr[i] = True
            current_color_count = 1
            direction_arr[i] = _sequence_direction(last_color, spectrum)
            skip_detected_arr[i] = _is_skip(last_color, spectrum)
            recent_transitions.append(COLOR_LETTERS.get(spectrum, '?'))
            if len(recent_transitions) > 3:
                recent_transitions = recent_transitions[-3:]
        else:
            # Same color
            color_changed_arr[i] = False
            current_color_count += 1
            direction_arr[i] = 'flat'
            skip_detected_arr[i] = False

        bars_in_color_arr[i] = current_color_count

        # State tracking
        if last_state is None or state != last_state:
            current_state_count = 1
        else:
            current_state_count += 1
        bars_in_state_arr[i] = current_state_count

        # Pattern ID = last 3 transitions
        pattern_id_arr[i] = ''.join(recent_transitions[-3:])

        # Blue/red distance tracking
        if spectrum == 'blue':
            last_blue_idx = i
        if spectrum == 'red':
            last_red_idx = i

        from_blue_arr[i] = (i - last_blue_idx) if last_blue_idx >= 0 else np.nan
        from_red_arr[i] = (i - last_red_idx) if last_red_idx >= 0 else np.nan

        # Update state for next iteration
        last_color = spectrum
        last_state = state

    # Assign columns
    result['bbw_seq_prev_color'] = prev_color_arr
    result['bbw_seq_color_changed'] = color_changed_arr
    result['bbw_seq_bars_in_color'] = bars_in_color_arr
    result['bbw_seq_bars_in_state'] = bars_in_state_arr
    result['bbw_seq_direction'] = direction_arr
    result['bbw_seq_skip_detected'] = skip_detected_arr
    result['bbw_seq_pattern_id'] = pattern_id_arr
    result['bbw_seq_from_blue_bars'] = from_blue_arr
    result['bbw_seq_from_red_bars'] = from_red_arr

    return result
