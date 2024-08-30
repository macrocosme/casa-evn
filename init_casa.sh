#!/usr/bin/env bash

HELP="$(basename $0) -l <base data location> -o <obs code> -p <project code> [-d <data location>] [-c <n cpus cores>] [-i (init flags,tsys,gc)] [-w <working directory>]"
if [[ $1 == "-h" || $1 == "--help" ]]; then
    echo "Usage:"
    echo $HELP
    exit 0
fi

while getopts ":l:o:p:d:c:i:w:" opt; do
    case $opt in
        l) DATA="$OPTARG"
        ;;
        o) obscode="$OPTARG"
        ;;
        p) prj="$OPTARG"
        ;;
        d) DATA="$OPTARG"
        ;;
        c) cpu="$OPTARG"
        ;;
        i) init_flags_tst_gc="$OPTARG"
        ;;
        w) workdir="$OPTARG"
        ;;
        e) EXTRAOPTS="$OPTARG"
        ;;
        \?) echo "Invalid option -$OPTARG" >&2
            echo
            echo "Usage:"
            echo $HELP
        exit 1
        ;;
    esac
done

calibration="pipeline_calibration"

obs="$DATA/$obscode"

if [[ -n "$init_flags_tst_gc" && [$init_flags_tst_gc == True || $init_flags_tst_gc == 1] ]]; then
    echo "Init flags, TSYS and GC\n\n"
    echo "python3 ~/casa-vlbi/flag.py  $obs/$calibration/$prj.uvflg  $obs/fits/$prj_targets_1_1.IDI1 $obs/fits/$prj_targets_1_1.IDI2 $obs/fits/$prj_targets_1_1.IDI3 $obs/fits/$prj_targets_1_1.IDI4 > $obs/fits/$prj.flag"
    python3 ~/casa-vlbi/flag.py  $obs/$calibration/$prj.uvflg  $obs/fits/$prj_targets_1_1.IDI1 $obs/fits/$prj_targets_1_1.IDI2 $obs/fits/$prj_targets_1_1.IDI3 $obs/fits/$prj_targets_1_1.IDI4 > $obs/fits/$prj.flag

    echo "casa --nogui -c ~/casa-vlbi/append_tsys.py  $obs/$calibration/$prj.antab $obs/fits/$prj_targets_1_1.IDI*"
    casa --nogui -c ~/casa-vlbi/append_tsys.py  $obs/$calibration/$prj.antab $obs/$fits/$prj_targets_1_1.IDI*

    echo "casa --nogui -c ~/casa-vlbi/gc.py $obs/$calibration$prj.antab $obs/$calibration/EVN.gc"
    casa --nogui -c ~/casa-vlbi/gc.py $obs/$calibration/$prj.antab $obs/$calibration/EVN.gc
fi 

if [ -z "$workdir" ]; then
    workdir=$obs/run
fi
if [ ! -d $workdir ]; then
    mkdir -p $workdir
fi
cd $workdir

export PYTHONPATH=$DATA/scripts:/home/matchmkr-dvohl/casa-vlbi:$PYTHONPATH

# Launch casa with n processes
if [[ -z "$cpu" || $cpu -le 1 ]]; then
    echo "casa"
    casa
else
    echo "mpicasa -n $cpu casa"
    mpicasa -n $cpu casaimport 
fi
