import os
import ast
import csv
import argparse
import numpy as np
import ROOT
from NuRadioReco.modules.RNO_G import channelBlockOffsetFitter

# load the RNO-G library
ROOT.gSystem.Load(os.environ.get('RNO_G_INSTALL_DIR')+"/lib/libmattak.so")

# make sure we have enough arguments to proceed
parser = argparse.ArgumentParser(description='daqstatus example')
parser.add_argument('--file', dest='file', required=True)

args = parser.parse_args()
filename = args.file

fIn = ROOT.TFile.Open(filename)
combinedTree = fIn.Get("combined")

d = ROOT.mattak.DAQStatus()
wf = ROOT.mattak.Waveforms()
hdr = ROOT.mattak.Header()

combinedTree.SetBranchAddress("daqstatus", ROOT.AddressOf(d))
combinedTree.SetBranchAddress("waveforms", ROOT.AddressOf(wf))
combinedTree.SetBranchAddress("header", ROOT.AddressOf(hdr))

num_events = combinedTree.GetEntries()

rms_all = []


chs = [0,1,2,3]
rms_all = dict()

for ch in chs:
    rms_all[ch] = []

diff = num_events//3
station = filename.split("/")[-3]
run = filename.split("/")[-2]

for event in range(num_events):
    combinedTree.GetEntry(event)

    if (hdr.trigger_info.force_trigger == True):
        for ch in chs:
            g = wf.makeGraph(ch)
            voltage = g.GetY()
            time = g.GetX()

            sampling_freq = 1/(time[1] - time[0])
            offset, output = channelBlockOffsetFitter.fit_block_offsets(voltage, sampling_rate = sampling_freq, return_trace = True)


            voltage_sq = []

            for v in output:
                voltage_sq.append(v**2)

            rms = np.sqrt(np.mean(voltage_sq))
            rms_all[ch].append(rms)

            del g


rms_avg = []
for ch in chs:
    rms = rms_all[ch]
    rms_avg.append(np.average(rms))

for event in range(1):
    combinedTree.GetEntry(event)
    time_readout = d.readout_time_lt
    time = hdr.trigger_time

def run_num(run):
    nums = []
    for char in run:
        if (char.isdigit() == True):
            nums.append(char)
    num = 0

    for i in range(len(nums)):
        num += float(nums[i])*(10**(len(nums)-i-1))
    return int(num)

#change station number

stat = run_num(station)

#change path to rms_bounds folder 

bounds_path = f"/data/condor_builds/users/avijai/RNO/tutorials-rnog/get_daqstatus/rms_bounds/stat{stat}_rms_bounds.csv"
ch_yr_bounds = {}
years = []

with open(bounds_path) as f:
     reader = csv.reader(f)
     count = 0
     for row in reader:
         if (count == 0):
             for yr in row:
                 if (len(yr) > 0):
                     ch_yr_bounds[int(yr)] = []
                     years.append(int(yr))
         else:
             subcount = 0
             for bound in row:
                 if (subcount > 0):
                     ch_yr_bounds[years[subcount-1]].append(ast.literal_eval(bound))
                 subcount += 1
         subcount = 0
         count += 1 

             
bound_yrs = [1609459200, 1640995200, 1672531200, 1704067200]
if (stat == 12):
    bound_yrs.append([1719304136.3])
elif (stat == 23):
    bound_yrs.append([1720186367.9])
elif (stat == 13):
    bound_yrs.append([1720949861.3])
else:
    bound_yrs.append([1719134085.4])

def check_bounds(bounds):
    for i in range(len(bounds)):
        upper = bounds[i][0]
        lower = bounds[i][1]
        if (rms_avg[i] < lower or rms_avg[i] > upper):
            return False
    return True
    
if (time >= bound_yrs[0] and  time < bound_yrs[1]):
    bounds = ch_yr_bounds[1]
elif (time >= bound_yrs[1] and time < bound_yrs[2]):
    bounds = ch_yr_bounds[2]
elif (time >= bound_yrs[2] and time < bound_yrs[3]):
    bounds = ch_yr_bounds[3]
elif (time >= bound_yrs[3] and time < bound_yrs[4]):
    bounds = ch_yr_bounds[4]
elif (time > bound_yrs[4]):
    bounds = ch_yr_bounds[5]


print(check_bounds(bounds))



