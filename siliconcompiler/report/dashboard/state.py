import argparse
import json
import os
import streamlit
import streamlit_javascript
import fasteners

from siliconcompiler import Chip


DISPLAY_FLOWGRAPH = "show_flowgraph"
SELECTED_JOB = "selected_job"
SELECTED_NODE = "selected_node"
# This is needed until the graph supports setting a selected node
SELECTED_FLOWGRAPH_NODE = "selected_flowgraph_node"
SELECTED_FILE = "selected_file"
LOADED_CHIPS = "loaded_chips"
UI_WIDTH = "ui_width"
MANIFEST_FILE = "manifest_file"
MANIFEST_LOCK = "manifest_lock"
MANIFEST_TIME = "manifest_time"
IS_RUNNING = "is_flow_running"
GRAPH_JOBS = "graph_jobs"

DEBUG = False


def _add_default(key, value):
    if key not in streamlit.session_state:
        streamlit.session_state[key] = value


def update_manifest():
    file_time = os.stat(get_key(MANIFEST_FILE)).st_mtime

    if get_key(MANIFEST_TIME) != file_time:

        chip = Chip(design='')

        with get_key(MANIFEST_LOCK):
            chip.read_manifest(get_key(MANIFEST_FILE))
        set_key(MANIFEST_TIME, file_time)

        streamlit.session_state[LOADED_CHIPS]["default"] = chip

        for history in chip.getkeys('history'):
            history_chip = Chip(design='')
            history_chip.schema.cfg = chip.getdict('history', history)
            history_chip.set('design', chip.design)
            streamlit.session_state[LOADED_CHIPS][history] = history_chip

        if DEBUG:
            print("Reading manifest", streamlit.session_state[MANIFEST_FILE])

        return True
    return False


def init():
    _add_default(DISPLAY_FLOWGRAPH, True)
    _add_default(SELECTED_JOB, None)
    _add_default(SELECTED_NODE, None)
    _add_default(SELECTED_FLOWGRAPH_NODE, None)
    _add_default(SELECTED_FILE, None)
    _add_default(LOADED_CHIPS, {})
    _add_default(MANIFEST_FILE, None)
    _add_default(MANIFEST_LOCK, None)
    _add_default(MANIFEST_TIME, None)
    _add_default(IS_RUNNING, False)
    _add_default(GRAPH_JOBS, None)
    _add_default(UI_WIDTH, None)

    parser = argparse.ArgumentParser('dashboard')
    parser.add_argument('cfg', nargs='?')
    args = parser.parse_args()

    if not args.cfg:
        raise ValueError('configuration not provided')

    if not get_key(LOADED_CHIPS):
        # First time through

        with open(args.cfg, 'r') as f:
            config = json.load(f)

        set_key(MANIFEST_FILE, config["manifest"])
        set_key(MANIFEST_LOCK, fasteners.InterProcessLock(config["lock"]))

        update_manifest()
        chip = get_chip("default")
        for graph_info in config['graph_chips']:
            file_path = graph_info['path']
            graph_chip = Chip(design='')
            graph_chip.read_manifest(file_path)
            graph_chip.unset('arg', 'step')
            graph_chip.unset('arg', 'index')

            if graph_info['cwd']:
                graph_chip.cwd = graph_info['cwd']

            streamlit.session_state[LOADED_CHIPS][os.path.basename(file_path)] = graph_chip

        chip_step = chip.get('arg', 'step')
        chip_index = chip.get('arg', 'index')

        if chip_step and chip_index:
            set_key(SELECTED_NODE, f'{chip_step}{chip_index}')

    chip = get_chip("default")
    chip.unset('arg', 'step')
    chip.unset('arg', 'index')

    if not get_key(SELECTED_JOB):
        set_key(SELECTED_JOB, "default")


def setup():
    set_key(UI_WIDTH, streamlit_javascript.st_javascript("window.innerWidth"))


def get_chip(job=None):
    if not job:
        job = get_key(SELECTED_JOB)
    return get_key(LOADED_CHIPS)[job]


def get_chips():
    chips = list(get_key(LOADED_CHIPS).keys())
    chips.remove('default')
    chips.insert(0, 'default')
    return chips


def get_key(key):
    return streamlit.session_state[key]


def set_key(key, value):
    changed = value != streamlit.session_state[key]
    if changed:
        streamlit.session_state[key] = value
        return True
    return False


def compute_component_size(minimum, requested_px):
    ui_width = get_key(UI_WIDTH)

    if ui_width > 0:
        return min(requested_px / ui_width, minimum)

    return minimum


def debug_print(*args):
    if DEBUG:
        print(*args)


def debug_print_state():
    if not DEBUG:
        return

    for n, (key, value) in enumerate(streamlit.session_state.items()):
        print(n, key, type(value), value)
    print()
