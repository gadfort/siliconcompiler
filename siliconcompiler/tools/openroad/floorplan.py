from siliconcompiler.tools._common import input_provides
from siliconcompiler.tools.openroad.openroad import setup as setup_tool
from siliconcompiler.tools.openroad.openroad import build_pex_corners
from siliconcompiler.tools.openroad.openroad import post_process as or_post_process
from siliconcompiler.tools.openroad.openroad import pre_process as or_pre_process
from siliconcompiler.tools.openroad.openroad import _set_reports, set_pnr_inputs, set_pnr_outputs


def setup(chip):
    '''
    Perform floorplanning, pin placements, macro placements and power grid generation
    '''

    # Generic tool setup.
    setup_tool(chip)

    tool = 'openroad'
    design = chip.top()
    step = chip.get('arg', 'step')
    index = chip.get('arg', 'index')
    task = chip._get_task(step, index)

    if chip.valid('input', 'asic', 'floorplan') and \
       chip.get('input', 'asic', 'floorplan', step=step, index=index):
        chip.add('tool', tool, 'task', task, 'require',
                 ",".join(['input', 'asic', 'floorplan']),
                 step=step, index=index)

    if f'{design}.vg' in input_provides(chip, step, index):
        chip.add('tool', tool, 'task', task, 'input', design + '.vg',
                 step=step, index=index)
    else:
        chip.add('tool', tool, 'task', task, 'require', 'input,netlist,verilog',
                 step=step, index=index)

    set_pnr_inputs(chip)
    set_pnr_outputs(chip)

    if chip.valid('tool', tool, 'task', task, 'file', 'padring') and \
       chip.get('tool', tool, 'task', task, 'file', 'padring',
                step=step, index=index):
        chip.add('tool', tool, 'task', task, 'require',
                 ','.join(['tool', tool, 'task', task, 'file', 'padring']),
                 step=step, index=index)
    chip.set('tool', tool, 'task', task, 'file', 'padring',
             'script to insert the padring',
             field='help')

    snap = chip.get('tool', tool, 'task', task, 'var', 'ifp_snap_strategy',
                    step=step, index=index)[0]
    snaps_allowed = ('none', 'site', 'manufacturing_grid')
    if snap not in snaps_allowed:
        chip.error(f'{snap} is not a supported snapping strategy. Allowed values: {snaps_allowed}')

    _set_reports(chip, [
        'setup',
        'unconstrained',
        'power'
    ])


def pre_process(chip):
    or_pre_process(chip)
    build_pex_corners(chip)


def post_process(chip):
    or_post_process(chip)
