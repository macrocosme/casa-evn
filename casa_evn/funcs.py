import os
from astropy.io import fits as pyfits
from casavlbitools import fitsidi
from casatasks import applycal, flagdata, flagmanager, gencal, importfitsidi, listobs
from casaplotms import plotms


def gunzip(basedir, calibdir, keep=False):
    search_gz = f"{basedir}/{calibdir}"
    for f in os.listdir(search_gz):
        if ".gz" in f:
            cmd = f"gunzip {search_gz}/{f}" if (not keep) else f"gunzip {f} -k"
            print(cmd)
            os.system(cmd)


def get_idifiles(basedir, fitsdir):
    idis = []
    fits = f"{basedir}/{fitsdir}"
    for f in os.listdir(fits):
        if "IDI" in f:
            idis.append(f"{fits}/{f}")
        return idis


def import_fits_idi(basedir, fitsdir, workdir, prj, vis, idifiles):
    importfitsidi(
        fitsidifile=idifiles,
        vis=vis,
        constobsid=True,
        scanreindexgap_s=15.0,
        specframe="GEO",
    )


def convert_flag(basedir, calibdir, workdir, prj, idifiles):
    AIPSflag = f"{basedir}/{calibdir}/{prj}.uvflg"
    outfile = f"{basedir}/{workdir}/{prj}.flag"
    fitsidi.convert_flags(AIPSflag, idifiles, outfile=outfile)


def flag_data(basedir, workdir, prj, vis):
    flagfile = f"{basedir}/{workdir}/{prj}.flag"
    flagdata(
        vis=vis,
        mode="list",
        inpfile=flagfile,
        reason="any",
        action="apply",
        flagbackup=False,
        savepars=False,
    )


def set_working_vars(basedir, workdir, prj):
    """Set working variables

    Parameters
    ----------
        basedir, workdir, prj

    Returns
    -------
        gcaltab, tsystab, sbdtab, mbdtab, bpasstab
    """
    set_working_vars_base = (
        lambda basedir, extradir, prj, extension: f"{basedir}/{extradir}/{prj}.{extension}"
    )
    gcaltab = set_working_vars_base(basedir, workdir, prj, "gcal")
    tsystab = set_working_vars_base(basedir, workdir, prj, "tsys")
    sbdtab = set_working_vars_base(basedir, workdir, prj, "sbd")
    mbdtab = set_working_vars_base(basedir, workdir, prj, "mbd")
    bpasstab = set_working_vars_base(basedir, workdir, prj, "bpass")
    return (gcaltab, tsystab, sbdtab, mbdtab, bpasstab)


def append_tsys_gaincurve(basedir, calibdir, prj, idifiles):
    antabfile = f"{basedir}/{calibdir}/{prj}.antab"
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


def gen_cal(vis, tsystab, gcaltab):
    gencal(vis, caltable=tsystab, caltype="tsys", uniform=False)
    gencal(vis, caltable=gcaltab, caltype="gc", infile="EVN.gc")


def apply_cal(vis, tsystab, gcaltab):
    applycal(vis=vis, åå=[tsystab, gcaltab], flagbackup=False, parang=True)


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


def get_flag_autocorrelation_cmd():
    print(
        "msmd.open(vis)\nnspw=msmd.nspw()\nnchan=msmd.nchan(1)\nmsmd.done()\nflagdata(vis,mode='manual',autocorr=True,flagbackup=False)\nmyflags=None\nedgefraction = 0.1\nflagfraction = int(nchan/(100*edgefraction)) \nstart = str(flagfraction-1)\nend = str(nchan-flagfraction)\nspwflag = '*:0~'+start+';'+end+'~'+str(nchan-1)"
    )


def flagquack_intervals(vis):
    flagdata(vis, mode="quack", quackinterval=5, flagbackup=False)
    flagmanager(
        vis,
        mode="save",
        versionname="precal_flags",
        comment="Flags from Tsys, gaincal, bad data and edge channels",
    )


def gen_list_of_scans(basedir, calibdir, prj, vis):
    listobsfile = f"{basedir}/{calibdir}/{prj}.listobs"
    if os.path.isfile(listobsfile) == False:
        listobs(vis, listfile=listobsfile)
    else:
        print("✅ A file with listobs information is already present")


basedir_subdir_experiment = lambda base, sub, prj: f"{base}/{sub}/{prj}"

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

# def polarization_calibration(basedir, workdir, prj):
#     print(f"""tget tclean
#     basename = basedir_subdir_experiment(basedir, workdir, prj)
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
