from siliconcompiler.tools.builtin import _common
from siliconcompiler.tools.builtin import nop
from siliconcompiler.tools.builtin.builtin import set_io_files


def setup(chip):
    '''
    Merges outputs from a list of input tasks.
    '''

    set_io_files(chip)


def _select_inputs(chip, step, index):
    chip.logger.info("Running builtin task 'join'")

    flow = chip.get('option', 'flow')
    return list(chip.get('flowgraph', flow, step, index, 'input'))


def _gather_outputs(chip, step, index):
    return nop._gather_outputs(chip, step, index)


def run(chip):
    return _common.run(chip)


def post_process(chip):
    _common.post_process(chip)
