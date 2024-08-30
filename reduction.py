from casavlbitools import fitsidi
from natsort import natsort_keygen

from casavlbitools import fitsidi
from casatasks import (
    applycal, 
    flagdata, 
    flagmanager, 
    fringefit,
    gencal, 
    importfitsidi,
    listobs
)
# from casatools import msmd
from casaplotms import plotms

import glob

# load data required for the data reduction procedure
# ... make naturally sorted fits.idi files
# ... import files
# ... flag data
# ... generate a-priori gain calibration
def load_data(experiment):

    myidifiles = sorted(glob.glob(f'{experiment}*IDI*'),key=natsort_keygen()) 

    fitsidi.append_tsys(f'{experiment}.antab',myidifiles)

    fitsidi.convert_flags(f'{experiment}.uvflg', myidifiles, outfile=experiment.flag)

    importfitsidi(vis=f'{experiment}.ms',
                  fitsidifile=myidifiles,
                  constobsid=True,
                  scanreindexgap_s=15.0)

    flagdata(vis=f'{experiment}.ms',
             mode='list',
             inpfile=f'{experiment}.flag',
             reason='any',
             action='apply',
             flagbackup=True,
             savepars=False)

    gencal(vis=f'{experiment}.ms',
           caltable='cal.tsys',
           caltype='tsys',
           uniform=False)

    gencal(vis=f'{experiment}.ms',
           caltable='cal.gcal',
           caltype='gc')
    

# Inspect the data
def quick_inspect(experiment):
    listobs(vis=f'{experiment}.ms')
    plotms(vis=f'{experiment}.ms')

# Atmospheric corrections
def atmospheric_corrections(experiment):
    from casatasks.private import tec_maps
    tec_image, tec_rms_image, plotname = tec_maps.create(vis=f'{experiment}.ms', doplot=True)

    gencal(vis=f'{experiment}.ms', caltable='cal.tecim',
        caltype='tecim', infile='tec_image')

    viewer(f'{experiment}.ms.IGS_TEC.im')
    viewer(f'{experiment}.ms.IGS_RMS_TEC.im')


# Removing instrumental delay
def fit_fringe(experiment):
    fringefit(vis=f"{experiment}.ms",
              caltable="cal.sbd",
              timerange='h1:m1:s1~h2:m2:s2',
              solint='inf',
              zerorates=True,
              refant='a'
              minsnr=10,
              gaintable=['cal.tsys', 'cal.gcal']
              parang=True)

    plotms(vis='cal.sbd',
           xaxis='frequency',
           yaxis='phase',
           antenna='a'
           correlation='rr,ll',
           timerange='h1:m1:s1~h2:m2:s2',
           averagedata=True,
           avgtime='120') # can also be plotted with 'plotcal'

    applycal(vis=f'{experiment}.ms',
             gaintable=['cal.tsys', 'cal.gcal', 'cal.sbd', '...'],
             parang=True)


# Bandpass calibration
def calibrate_bandpass(experiment):
    bandpass(vis=f'{experiment}.ms',
        caltable='cal.bpass'
        field='bandpass-calibrator',
        gaintable=['cal.tsys', 'cal.gcal', '...'],
        solnorm=True,
        solint='inf',
        refant='a',
        bandtype='B',
        parang=True)


# Global fringe (or frequency and time-dependent phase calibration)
def fit_fringe_global(experiment):
    fringefit(vis=f'{experiment}.ms',
        caltable='cal.mbd',
        solint='t',
        combine='spw',
        field='calsource1, calsource2,...',
        refant='a',
        minsnr=7,
        gaintable=['cal.tsys', 'cal.gcal', 'cal.bpass', 'cal.sbd', ...],
        parang=True)

    applycal(vis=f'{experiment}.ms',
        gaintable=['cal.tsys', 'cal.gcal', 'cal.bpass', 'cal.sbd', 'cal.mbd', ...],
        spwmap=[[], [], [], N*[0], ...],
        parang=True)


# Split and store the data
def split_data(experiment):
    split(vis=f'{experiment}.ms',
        field='source_name',
        outputvis='source_name.ms',
        datacolumn='corrected')

def store_data(source_name):
    exportuvfits(vis='filename.ms',
                 field='sources',
                 fitsfile='filename.uvfits',
                 datacolumn='corrected')
