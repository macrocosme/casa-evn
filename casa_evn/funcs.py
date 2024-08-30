import os
from astropy.io import fits as pyfits
from casavlbitools import fitsidi
from casatasks import applycal, flagdata, flagmanager, gencal, importfitsidi, listobs
from casaplotms import plotms
from casatools import msmetadata as msmd
import glob


# General
def gunzip(basedir, calibdir, keep=False):
    search_gz = f"{basedir}/{calibdir}"
    for f in os.listdir(search_gz):
        if ".gz" in f:
            cmd = f"gunzip {search_gz}/{f}" if (not keep) else f"gunzip {f} -k"
            print(cmd)
            os.system(cmd)


def get_idifiles(basedir, fitsdir, experiment):
    import re

    natsort = lambda s: [
        int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)
    ]
    idifiles = sorted(glob.glob(f"{basedir}/{fitsdir}/{experiment}*IDI*"), key=natsort)
    return idifiles


def set_working_vars(basedir, workdir, experiment):
    """Set working variables

    Parameters
    ----------
        basedir, workdir, experiment

    Returns
    -------
        gcaltab, tsystab, sbdtab, mbdtab, bpasstab
    """
    set_working_vars_base = (
        lambda basedir, extradir, experiment, extension: f"{basedir}/{extradir}/{experiment}.{extension}"
    )
    gcaltab = set_working_vars_base(basedir, workdir, experiment, "gcal")
    tsystab = set_working_vars_base(basedir, workdir, experiment, "tsys")
    sbdtab = set_working_vars_base(basedir, workdir, experiment, "sbd")
    mbdtab = set_working_vars_base(basedir, workdir, experiment, "mbd")
    bpasstab = set_working_vars_base(basedir, workdir, experiment, "bpass")
    return (gcaltab, tsystab, sbdtab, mbdtab, bpasstab)


def append_tsys_gaincurve(basedir, calibdir, experiment, idifiles):
    antabfile = f"{basedir}/{calibdir}/{experiment}.antab"
    try:
        hdulist = pyfits.open(idifiles[0])
        hdu = hdulist["SYSTEM_TEMPERATURE"]
        print("✅ TSYS table already present, skipping the append step")
    except IndexError:
        print("🛑 Your list of files is empty, have you set the correct path?")
    except KeyError:
        print("Appending TSYS, this takes some time, go for a walk")
        fitsidi.append_tsys(antabfile, idifiles)
    except FileNotFoundError:
        print("🛑 Your FITS-IDI files cannot be found, have you set the correct path?")

    try:
        hdulist = pyfits.open(idifiles[0])
        hdu = hdulist["GAIN_CURVE"]
        print("✅ Gain curve table already present, skipping the append step")
    except KeyError:
        print("Appending gain curve")
        fitsidi.append_gc(antabfile, idifiles[0])
    except IndexError:
        print("🛑 Your list of files is empty, have you set the correct path?")
    except FileNotFoundError:
        print("🛑 Your FITS-IDI files cannot be found, have you set the correct path?")


def import_fits_idi(basedir, fitsdir, workdir, experiment, vis, idifiles):
    importfitsidi(
        fitsidifile=idifiles,
        vis=vis,
        constobsid=True,
        scanreindexgap_s=15.0,
        specframe="GEO",
    )


# Data reduction & calibration
def convert_flag(basedir, calibdir, workdir, experiment, idifiles):
    AIPSflag = f"{basedir}/{calibdir}/{experiment}.uvflg"
    outfile = f"{basedir}/{workdir}/{experiment}.flag"
    fitsidi.convert_flags(AIPSflag, idifiles, outfile=outfile)


def flag_data(basedir, workdir, experiment, vis):
    flagfile = f"{basedir}/{workdir}/{experiment}.flag"
    flagdata(
        vis=vis,
        mode="list",
        inpfile=flagfile,
        reason="any",
        action="apply",
        flagbackup=True,
        savepars=False,
    )


def gen_cal(vis, tsystab, gcaltab):
    gencal(vis, caltable=tsystab, caltype="tsys", uniform=False)
    gencal(vis, caltable=gcaltab, caltype="gc", infile="EVN.gc")


def apply_cal(vis, tsystab, gcaltab):
    applycal(vis=vis, åå=[tsystab, gcaltab], flagbackup=False, parang=True)


# Quick plot
def plotms_phase_freq(vis, ref="EF", field="0", avgtime="600"):
    plotms(
        vis=vis,
        xaxis="frequency",
        yaxis="phase",
        antenna=ref,
        ydatacolumn="corrected",
        iteraxis="baseline",
        correlation="ll,rr",
        coloraxis="spw",
        averagedata=True,
        avgtime=avgtime,
        gridrows=4,
        gridcols=3,
        field=field,
    )


def plotms_freq_amplitude(vis, ref="EF", field="0", avgtime="600"):
    plotms(
        vis=vis,
        xaxis="frequency",
        yaxis="amplitude",
        antenna=ref,
        ydatacolumn="corrected",
        iteraxis="baseline",
        correlation="ll,rr",
        coloraxis="spw",
        averagedata=True,
        avgtime=avgtime,
        gridrows=4,
        gridcols=3,
        field=field,
    )


def plotms_time_phase(vis, ref="EF", field="0", avgchannel="64"):
    plotms(
        vis=vis,
        xaxis="time",
        yaxis="phase",
        antenna=ref,
        ydatacolumn="corrected",
        iteraxis="baseline",
        correlation="ll,rr",
        coloraxis="scan",
        averagedata=True,
        avgchannel=avgchannel,
        avgspw=True,
        gridrows=4,
        gridcols=3,
        field=field,
    )


def plotms_time_amplitude(vis, ref="EF", field="0", avgchannel="64"):
    plotms(
        vis=vis,
        xaxis="time",
        yaxis="amp",
        antenna=ref,
        ydatacolumn="corrected",
        iteraxis="baseline",
        correlation="ll,rr",
        coloraxis="scan",
        averagedata=True,
        avgchannel=avgchannel,
        avgspw=True,
        gridrows=4,
        gridcols=3,
        field=field,
    )


def get_flag_autocorrelation_cmd(vis):
    print("To flag autocorrelation:")
    msmd.open(vis)
    nspw = msmd.nspw()
    nchan = msmd.nchan(1)
    msmd.done()
    flagdata(vis, mode="manual", autocorr=True, flagbackup=False)
    myflags = None
    edgefraction = 0.1
    flagfraction = int(nchan / (100 * edgefraction))
    start = str(flagfraction - 1)
    end = str(nchan - flagfraction)
    spwflag = "*:0~" + start + ";" + end + "~" + str(nchan - 1)


def flagquack_intervals(vis):
    flagdata(vis, mode="quack", quackinterval=5, flagbackup=False)
    flagmanager(
        vis,
        mode="save",
        versionname="precal_flags",
        comment="Flags from Tsys, gaincal, bad data and edge channels",
    )


def gen_list_of_scans(basedir, calibdir, experiment, vis):
    listobsfile = f"{basedir}/{calibdir}/{experiment}.listobs"
    if os.path.isfile(listobsfile) == False:
        listobs(vis, listfile=listobsfile)
    else:
        print("✅ A file with listobs information is already present")


basedir_subdir_experiment = lambda base, sub, experiment: f"{base}/{sub}/{experiment}"


# # *****
# # Fringe fitting
# refant='EF'
# sbdtimer='10:52:30~10:54:30' # found by plotting time vs amp:corrected for field2, EF, (ll,rr), 128 chan, all spectral windows
# fringefit(vis, caltable=sbdtab, timerange=sbdtimer,
#         solint='inf', zerorates=True, refant=refant,minsnr=50,
#         gaintable=[gcaltab,tsystab], corrdepflags=False,
#         interp=['nearest','nearest,nearest'],
#         parang=True)


# applycal(vis=vis,gaintable=[tsystab,gcaltab,sbdtab], flagbackup=False, parang=True)


# # Multi-band delay
# mbdfield='0,2'
# refant='EF,O8'
# fringefit(vis, caltable=mbdtab, field=mbdfield,
#         solint='inf', zerorates=False, refant=refant,
#         combine='spw', minsnr=5, corrdepflags=True,
#         gaintable=[gcaltab, tsystab, sbdtab],
#         parang=True)


# # Apply calibration
# # nspw=8
# applycal(vis,
#     gaintable=[gcaltab, tsystab, sbdtab, mbdtab],
#     interp=['nearest','nearest,nearest','nearest','linear'],
#     spwmap=[[], [], [], int(nspw)*[0]],
#     parang=True)


# # applycal(vis,
# #     gaintable=[gcaltab, tsystab, sbdtab],
# #     interp=['nearest','nearest,nearest','nearest'],
# #     spwmap=[[], [], []],
# #     parang=True)


# # Bandpass
# bpassfield='2'
# bandpass(vis, caltable=bpasstab, field=bpassfield,
#         gaintable=[gcaltab, tsystab, sbdtab, mbdtab],
#         interp=['nearest','nearest,nearest','nearest','linear'],
#         spwmap=[[],[],[], int(nspw)*[0]],
#         solnorm=True, solint='inf', refant=refant,
#         bandtype='B', parang=True)

# applycal(vis,
#     gaintable=[gcaltab, tsystab, sbdtab, mbdtab, bpasstab],
#     interp=['nearest','nearest,nearest','nearest','linear','linear,linear'],
#     spwmap=[[], [], [], int(nspw)*[0],[]],
#     parang=True)
# # ***

# def polarization_calibration(basedir, workdir, experiment):
#     print(f"""tget tclean
#     basename = basedir_subdir_experiment(basedir, workdir, experiment)
#     vis = '{f'{basename}'}.ms'
#     flagfile = '{f'{basename}'}.flag'
#     field = '0'
#     imagename = f'pcal'
#     iminpsize = [4096]
#     cell = ['1mas']
#     niter = 100
#     interactive=True
#     inp
#     go""")
