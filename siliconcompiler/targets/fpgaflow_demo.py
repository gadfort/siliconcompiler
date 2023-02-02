import siliconcompiler

def make_docs():
    '''
    Demonstration target for running the open-source fpgaflow.
    '''

    chip = siliconcompiler.Chip('<design>')
    chip.set('fpga', 'partname', 'ice40up5k-sg48')
    setup(chip)
    return chip

def setup(chip):
    '''
    Target setup
    '''

    #1. Load flow
    from flows import fpgaflow
    chip.use(fpgaflow)

    #2. Select default flow
    chip.set('option', 'mode', 'fpga')
    chip.set('option', 'flow', 'fpgaflow')

#########################
if __name__ == "__main__":

    chip = make_docs()
