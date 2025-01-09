'''
Verilator is a free and open-source software tool which converts Verilog (a
hardware description language) to a cycle-accurate behavioral model in C++
or SystemC.

All Verilator tasks may consume input either from a single pickled Verilog file
(``inputs/<design>.v``) generated by a preceding task, or if that file does not
exist, through the following keypaths:

    * :keypath:`input, rtl, verilog`
    * :keypath:`input, cmdfile, f`
    * :keypath:`option, ydir`
    * :keypath:`option, vlib`
    * :keypath:`option, idir`

For all tasks, this driver runs Verilator using the ``-sv`` switch to enable
parsing a subset of SystemVerilog features.

Documentation: https://verilator.org/guide/latest

Sources: https://github.com/verilator/verilator

Installation: https://verilator.org/guide/latest/install.html
'''

import os
from siliconcompiler.tools._common import (
    add_frontend_requires,
    get_frontend_options,
    add_require_input,
    get_input_files,
    get_tool_task,
    input_provides
)


####################################################################
# Make Docs
####################################################################
def make_docs(chip):
    from siliconcompiler.targets import freepdk45_demo
    chip.use(freepdk45_demo)


def setup(chip):
    ''' Per tool function that returns a dynamic options string based on
    the dictionary settings. Static settings only.
    '''

    tool = 'verilator'
    step = chip.get('arg', 'step')
    index = chip.get('arg', 'index')
    _, task = get_tool_task(chip, step, index)

    # Basic Tool Setup
    chip.set('tool', tool, 'exe', 'verilator')
    chip.set('tool', tool, 'vswitch', '--version')
    chip.set('tool', tool, 'version', '>=4.034', clobber=False)

    # Common to all tasks
    # Max threads
    chip.set('tool', tool, 'task', task, 'threads', os.cpu_count(),
             step=step, index=index, clobber=False)

    # Basic warning and error grep check on logfile
    chip.set('tool', tool, 'task', task, 'regex', 'warnings', r"^\%Warning",
             step=step, index=index, clobber=False)
    chip.set('tool', tool, 'task', task, 'regex', 'errors', r"^\%Error",
             step=step, index=index, clobber=False)

    chip.set('tool', tool, 'task', task, 'file', 'config',
             'Verilator configuration file',
             field='help')
    add_require_input(chip, 'tool', tool, 'task', task, 'file', 'config')
    add_require_input(chip, 'option', 'file', 'verilator_config')

    chip.set('tool', tool, 'task', task, 'var', 'initialize_random',
             'true/false, when true registers will reset with a random value.',
             field='help')
    chip.set('tool', tool, 'task', task, 'var', 'initialize_random', False,
             step=step, index=index, clobber=False)

    chip.set('tool', tool, 'task', task, 'var', 'random_seed',
             'controls the random seed.',
             field='help')

    chip.set('tool', tool, 'task', task, 'var', 'enable_assert',
             'true/false, when true assertions are enabled in Verilator.',
             field='help')
    chip.set('tool', tool, 'task', task, 'var', 'enable_assert', False,
             step=step, index=index, clobber=False)

    if chip.get('tool', tool, 'task', task, 'var', 'enable_assert', step=step, index=index):
        chip.add('tool', tool, 'task', task, 'require',
                 ','.join(['tool', tool, 'task', task, 'var', 'enable_assert']),
                 step=step, index=index)

    if f'{chip.top()}.v' not in input_provides(chip, step, index):
        add_require_input(chip, 'input', 'rtl', 'verilog')
        add_require_input(chip, 'input', 'rtl', 'systemverilog')
    add_require_input(chip, 'input', 'cmdfile', 'f')
    add_frontend_requires(chip, ['ydir', 'vlib', 'idir', 'libext', 'param', 'define'])


def runtime_options(chip):
    cmdlist = []
    tool = 'verilator'
    step = chip.get('arg', 'step')
    index = chip.get('arg', 'index')
    _, task = get_tool_task(chip, step, index)

    design = chip.top()

    has_input = os.path.isfile(f'inputs/{design}.v')
    opts_supports = ['param', 'libext']
    if not has_input:
        opts_supports.extend(['ydir', 'vlib', 'idir', 'define'])

    frontend_opts = get_frontend_options(chip, opts_supports)

    # Even though most of these don't need to be set in runtime_options() in order for the driver to
    # function properly, setting all the CLI options here facilitates a user using ['tool', <tool>,
    # 'task', <task>, 'option'] to supply additional CLI flags.

    cmdlist.append('-sv')
    cmdlist.extend(['--top-module', design])

    assertions = chip.get('tool', tool, 'task', task, 'var',
                          'enable_assert', step=step, index=index)
    if assertions == ['true']:
        cmdlist.append('--assert')

    random_init = chip.get('tool', tool, 'task', task, 'var',
                           'initialize_random', step=step, index=index)
    if random_init == ['true']:
        cmdlist.extend(['--x-assign', 'unique'])
        cmdlist.append('+verilator+rand+reset+2')

    random_seed = chip.get('tool', tool, 'task', task, 'var',
                           'random_seed', step=step, index=index)
    if random_seed:
        cmdlist.append(f'+verilator+seed+{random_seed[0]}')

    # Converting user setting to verilator specific filter
    for warning in chip.get('tool', tool, 'task', task, 'warningoff', step=step, index=index):
        cmdlist.append(f'-Wno-{warning}')

    libext = frontend_opts['libext']
    if libext:
        libext_option = f"+libext+.{'+.'.join(libext)}"
        cmdlist.append(libext_option)

    # Verilator docs recommend this file comes first in CLI arguments
    for value in get_input_files(chip, 'tool', tool, 'task', task, 'file', 'config'):
        cmdlist.append(value)
    for value in get_input_files(chip, 'option', 'file', 'verilator_config'):
        cmdlist.append(value)

    for param, value in frontend_opts['param']:
        cmdlist.append(f'-G{param}={value}')

    if os.path.isfile(f'inputs/{design}.v'):
        cmdlist.append(f'inputs/{design}.v')
    else:
        for value in frontend_opts['ydir']:
            cmdlist.append(f'-y {value}')
        for value in frontend_opts['vlib']:
            cmdlist.append(f'-v {value}')
        for value in frontend_opts['idir']:
            cmdlist.append(f'-I{value}')
        for value in frontend_opts['define']:
            if value == "VERILATOR":
                # Verilator auto defines this and will error if it is defined twice.
                continue
            cmdlist.append(f'-D{value}')
        for value in get_input_files(chip, 'input', 'rtl', 'systemverilog'):
            cmdlist.append(value)
        for value in get_input_files(chip, 'input', 'rtl', 'verilog'):
            cmdlist.append(value)

    for value in get_input_files(chip, 'input', 'cmdfile', 'f'):
        cmdlist.append(f'-f {value}')

    return cmdlist


################################
# Version Check
################################


def parse_version(stdout):
    # Verilator 4.104 2020-11-14 rev v4.104
    return stdout.split()[1]


##################################################
if __name__ == "__main__":

    chip = make_docs()
    chip.write_manifest("verilator.csv")
