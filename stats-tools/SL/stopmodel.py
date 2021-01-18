#!/usr/bin/env python
# encoding: 

# File        : test.py
# Author      : Zhenbin Wu
# Contact     : zhenbin.wu@gmail.com
# Date        : 2021 Jan 08
#
# Description : 

from collections import defaultdict
import numpy
import array
import uproot
import pickle
import json
import subprocess
import tarfile
import os


### Background and Data
sr = defaultdict(list)
f = open("pred_sr.tex", 'r')
for l in f.readlines():
    if l.count("&") != 7:
        continue
    ps = l.split("&")
    if "Search bin" in ps[0]:
        continue
    binNO = int(ps[0])
    bg_ = float(ps[-2].split("\\")[0].replace("$", ""))
    data_ = int(ps[-1].split("\\")[0])
    sr[binNO] = [bg_, data_]

datalist = []
bglist  = []
for k, v in sr.items():
    bglist.append(v[0])
    datalist.append(v[1])

name = "CMS-NOTE-2017-001 dummy model"
nbins = len(datalist)
data = array.array('d',datalist)
background = array.array('d',bglist)

## Cov Matrix
import ROOT
ROOT.gROOT.SetBatch(True)
# f = ROOT.TFile("./Matrix/Minos.root", "r")
f = ROOT.TFile("./Hesse.root", "r")
th2 = f.Get("test")
readout = []
for i in range(1, th2.GetNbinsX()+1):
    for j in range(1, th2.GetNbinsY()+1):
        readout.append(th2.GetBinContent(i, j))
        if th2.GetBinContent(i, j) == 0.0:
            print(i, j, th2.GetBinContent(i, j))
covariance= array.array('d',readout)

signal = None

### signal
def LoadSignal(signame):
    global signal
    ## folder
    js = json.load(open("combine_bkgPred.json"))
    if not os.path.exists('tmp'):
        os.makedirs('tmp')

    dtfolder = "/store/user/benwu/13TeV/"
    susy = signame.split("_")[0]
    tgzfile = "%s/CombineDataCard_%s_081820_UnblindRun2/%s.tgz" % (dtfolder, susy, signame)
    p = subprocess.Popen("xrdcp root://cmseos.fnal.gov/%s tmp/" % tgzfile, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err= p.communicate()
    print(out, err)
    tar = tarfile.open("tmp/%s.tgz" %signame,  "r:gz")
    signalmap = {}
    for r in tar.getmembers():
        if "root" not in r.name or "txt" in r.name or "lepcr" in r.name or "qcdcr" in r.name or "phocr" in r.name:
            continue
        r.name = os.path.basename(r.name)
        t = tar.extract(r, "tmp/")
        f = uproot.open("tmp/%s" % r.name)
        if b'signal;1' in f.keys():
            signalmap[int(js['binNum'][r.name.split(".")[0]])] = f[b'signal;1'].values[0]
    signal = array.array('d',signalmap.values())

