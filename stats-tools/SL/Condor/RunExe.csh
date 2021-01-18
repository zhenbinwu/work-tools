#!/bin/csh -v

set SCRAM = DELSCR
set CMSSW = DELDIR
set EXE   = DELEXE
set OUTPUT = OUTDIR

#============================================================================#
#-----------------------------   Setup the env   ----------------------------#
#============================================================================#
echo "============  Running on" $HOST " ============"
cd ${_CONDOR_SCRATCH_DIR}
source /cvmfs/cms.cern.ch/cmsset_default.csh
setenv SCRAM_ARCH ${SCRAM}
eval `scramv1 project CMSSW ${CMSSW}`
tar -xzf ${_CONDOR_SCRATCH_DIR}/CMSSW.tgz
cd ${CMSSW}
ls
eval `scramv1 runtime -csh` # cmsenv is an alias not on the workers
echo "CMSSW: "$CMSSW_BASE



setenv PYTHONPATH  ${_CONDOR_SCRATCH_DIR}/site-packages:${CMSSW_BASE}/src
setenv XDG_CONFIG_HOME ${_CONDOR_SCRATCH_DIR}/.config
setenv XDG_CACHE_HOME ${_CONDOR_SCRATCH_DIR}/.cache

if ! $?LD_LIBRARY_PATH then
    setenv LD_LIBRARY_PATH ./
else
    setenv LD_LIBRARY_PATH ./:${LD_LIBRARY_PATH}
endif

echo "------------"

ls
cd src/work-tools/stats-tools/SL
echo "------------"
ls
#============================================================================#
#--------------------------   To Run the Process   --------------------------#
#============================================================================#
echo $EXE $argv
python $EXE $argv

if ($? == 0) then
  foreach outfile (`ls *root`)
    echo "Copying ${outfile} to ${OUTPUT}"
    xrdcp -f $outfile "root://cmseos.fnal.gov/${OUTPUT}"
    if ($? == 0) then
      rm $outfile
    endif
  end
endif
