import os
import numpy as np
import funcs as _f

basedir, workdir = os.path.split(os.path.abspath('.'))
fitsdir='fits'
calibdir='pipeline_calibration'

set_vis = lambda experiment, basedir=basedir, workdir=workdir: f'{basedir}/{workdir}/{experiment}.ms'
get_steps = lambda: ['unzip_gz',
                     'check_tsys_gaincurve',
                     'gen_list_of_scans'
                     'convert_flag',
                     'import_fits_idi', 
                     'flag_data', 
                     'gen_cal', 
                     'apply_cal', 
                     'flag_autocorrelation', 
                     'flagquack_intervals'] 
dict_as_list = lambda _dict: (_dict[v] for v in _dict.keys())

def get_variables(experiment, refant = 'EF', return_as_dict=False):
    """Get values for common variables

    Parameters
    ----------
        experiment: str
            experiment code
        refant: str
            Reference antenna (default: 'EF')
        return_as_dict: bool
            Returns variables as a list (default) 
            or as a dict (to know what's what)
    Returns
    -------
        dict: vis, refant, gcaltab, tsystab, sbdtab, mbdtab, bpasstab, idifiles
    """
    refant = refant
    vis = set_vis(experiment)
    gcaltab, tsystab, sbdtab, mbdtab, bpasstab = _f.set_working_vars(basedir, workdir, experiment)
    idifiles = _f.get_idifiles(basedir, fitsdir, experiment)
    
    d = {'vis': vis,
         'refant': refant, 
         'gcaltab': gcaltab, 
         'tsystab': tsystab, 
         'sbdtab': sbdtab, 
         'mbdtab': mbdtab, 
         'bpasstab': bpasstab,
         'idifiles': idifiles}
    
    if return_as_dict:
        return d
    else: 
        return dict_as_list(d)

def run_steps(experiment, 
              steps=get_steps()):
    """Generate strings matching function calls

    Parameters
    ----------
        experiment, steps

    """
    idifiles = _f.get_idifiles(basedir, fitsdir, experiment)
    is_in_steps = lambda step, steps=steps: (step in steps)
    vis, \
        refant, \
        gcaltab, tsystab, sbdtab, mbdtab, bpasstab, \
        idifiles = get_variables(experiment)

    if is_in_steps('unzip_gz'):
        _f.gunzip(basedir, calibdir)

    if is_in_steps('import_fits_idi'):
        _f.import_fits_idi(basedir, fitsdir, workdir, experiment, vis, idifiles)

    if is_in_steps('check_tsys_gaincurve'):  
        _f.append_tsys_gaincurve(basedir, calibdir, experiment, idifiles)

    if is_in_steps('gen_list_of_scans'):
        _f.gen_list_of_scans(basedir, calibdir, experiment, vis)

    if is_in_steps('flag_data'):
        _f.flag_data(basedir, workdir, experiment, vis)

    if is_in_steps('convert_flag'):
        _f.convert_flag(basedir, calibdir, workdir, experiment, idifiles)

    if is_in_steps('gen_cal'):
        _f.gen_cal(vis, tsystab, gcaltab, vis)

    if is_in_steps('apply_cal'):
        _f.apply_cal(vis, tsystab, gcaltab)

    if is_in_steps('flag_autocorrelation'):
        _f.get_flag_autocorrelation_cmd()

    if is_in_steps('flagquack_intervals'):
        _f.flagquack_intervals(vis) 

    if is_in_steps(''):
        pass

    # if is_in_steps(''):
    #     pass
    


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('experiment', nargs='+', type=str,
                        help='project id (in lower case)')
    parser.add_argument("-s", "--steps", 
                        nargs='+', 
                        type=str, 
                        default=get_steps(),
                            help="Steps to be run")

    args = parser.parse_args()
    run_steps(args.experiment, args.steps)


# FRINGE FITTING
# ...