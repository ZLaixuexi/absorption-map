#!/bin/bash
# Run ISRF+CMB absorption calculation
# Usage: ./run_absorb.sh <distance_kpc> <l_deg> <b_deg> [output_file]
# Example: ./run_absorb.sh 2.0 184.55 -5.80 crab_abs.txt

if [ $# -lt 3 ]; then
    echo "Usage: $0 <dist_kpc> <l_deg> <b_deg> [outfile]"
    echo "Example: $0 2.0 184.55 -5.80 crab_abs.txt"
    exit 1
fi

DIST=$1
L=$2
B=$3
OUT=${4:-absorption_${DIST}kpc_l${L}_b${B}.txt}

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export LD_LIBRARY_PATH=/share06/soft/anaconda3/lib:$LD_LIBRARY_PATH

$SCRIPT_DIR/all8_cmb_galpropall_interpolationN_argvZ $DIST $L $B > $OUT 2>&1
echo "Saved: $OUT"
