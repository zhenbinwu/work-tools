#!/usr/bin/env python
# coding: utf-8

import os
import re
import time
import subprocess
import glob
import tarfile
import shutil
import getpass
import argparse
from collections import defaultdict

DelExe    = '../runSL.py'
OutDir = '/store/user/%s/Stop19/SimpleLH' %  getpass.getuser()
tempdir = '/uscmst1b_scratch/lpc1/3DayLifetime/benwu/TestCondor/'
ProjectName = 'test_v3'
argument = " --model stopmodel --signal %s -o %s.root"

def tar_cmssw():
    print("Tarring up CMSSW, ignoring file larger than 100MB")
    cmsswdir = os.environ['CMSSW_BASE']
    cmsswtar = os.path.abspath('%s/CMSSW.tgz' % tempdir)
    if os.path.exists(cmsswtar):
        ans = raw_input('CMSSW tarball %s already exists, remove? [yn] ' % cmsswtar)
        if ans.lower()[0] == 'y':
            os.remove(cmsswtar)
        else:
            return cmsswtar

    def exclude(tarinfo):
        if tarinfo.size > 100*1024*1024:
            tarinfo = None
            return tarinfo
        exclude_patterns = ['/.git/', '/tmp/', '/jobs.*/', '/logs/', '/.SCRAM/', '.pyc']
        for pattern in exclude_patterns:
            if re.search(pattern, tarinfo.name):
                # print('ignoring %s in the tarball', tarinfo.name)
                tarinfo = None
                break
        return tarinfo

    with tarfile.open(cmsswtar, "w:gz") as tar:
        tar.add(cmsswdir, arcname=os.path.basename(cmsswdir), filter=exclude)
    return cmsswtar

def Condor_Sub(condor_file):
    curdir = os.path.abspath(os.path.curdir)
    os.chdir(os.path.dirname(condor_file))
    print "To submit condor with " + condor_file
    os.system("condor_submit " + condor_file)
    os.chdir(curdir)


def my_process(args):
    ## temp dir for submit
    global tempdir
    global ProjectName
    global Process
    ProjectName = time.strftime('%b%d') + ProjectName
    tempdir = tempdir + os.getlogin() + "/" + ProjectName +  "/"
    try:
        os.makedirs(tempdir)
    except OSError:
        pass

    ## Create the output directory
    outdir = OutDir +  "/" + ProjectName + "/"
    try:
        os.makedirs("/eos/uscms/%s" % outdir)
    except OSError:
        pass

    ## Update RunHT.csh with DelDir and pileups
    RunHTFile = tempdir + "/" + "RunExe.csh"
    with open(RunHTFile, "wt") as outfile:
        for line in open("RunExe.csh", "r"):
            #line = line.replace("DELDIR", os.environ['PWD'])
            line = line.replace("DELSCR", os.environ['SCRAM_ARCH'])
            line = line.replace("DELDIR", os.environ['CMSSW_VERSION'])
            line = line.replace("DELEXE", DelExe.split('/')[-1])
            line = line.replace("OUTDIR", outdir)
            outfile.write(line)

    Tarfiles = []
    tarballnames = []
    Tarfiles.append(os.path.abspath(DelExe))
    tarballname ="%s/%s.tar.gz" % (tempdir, ProjectName)
    with tarfile.open(tarballname, "w:gz", dereference=True) as tar:
        [tar.add(f, arcname=f.split('/')[-1]) for f in Tarfiles]
        tar.close()
    tarballnames.append(tarballname)
    tarballnames.append(tar_cmssw())
    tarballnames.append("/uscms/home/benwu/python-packages.tgz")

    ### Update condor files
    configname = args.config.split("/")[-1].split(".")[0].replace("_signals", "")

    ## Prepare the condor file
    condorfile = tempdir + "/" + "condor_" + ProjectName  + "_"+configname
    with open(condorfile, "wt") as outfile:
        for line in open("condor_template", "r"):
            line = line.replace("EXECUTABLE", os.path.abspath(RunHTFile))
            line = line.replace("TARFILES", ", ".join(tarballnames))
            line = line.replace("TEMPDIR", tempdir)
            line = line.replace("PROJECTNAME", configname)
            line = line.replace("ARGUMENTS", "")
            outfile.write(line)
            
        for i, l_ in enumerate(open(args.config, 'r').readlines()):
            signal = l_.strip()
            line = "\nArguments = " + argument % (signal, signal)+ "\nQueue 1\n"
            outfile.write(line)
            if i == 1:
                break

    Condor_Sub(condorfile)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='NanoAOD postprocessing.')
    parser.add_argument('-c', '--config',
        default = "",
        help = 'Path to the input config file.')
    args = parser.parse_args()
    my_process(args)


