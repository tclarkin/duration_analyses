# -*- coding: utf-8 -*-
"""
Created on May 25 2021
Peak Data Preparation Script (v1)
@author: tclarkin (USBR 2021)

This script takes user supplied USGS gage or other peak data in .csv format and compresses into a summary of annual
peaks for use scripts 4a and 4b only

This script should be run once for each site being analyzed. If input csv files are used, suggest having three columns:
wy: (yyyy)
date: (dd-mmm-yyyy)
"peak"

"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from functions import nwis_peak_import,csv_peak_import,get_varlabel

### User Input ###
#os.chdir("C://Users//tclarkin//Documents//Projects//El_Vado_Dam//duration_analyses//")

# Site information and user selections
site = 'ElVado'  # site or dam name
wy_division = "WY" # "WY" or "CY"
site_source = "usgs" # "usgs" or "file"
site_file = "08284100" # usgs site number (e.g., "09445000") or .csv data file

# MOVE data prep
move = True
move_source = "file" # "usgs" or "file"
move_file = 'ElVado_site_peak_x.csv' # usgs site number (e.g., "09445000") or .csv data file

### Begin Script ###
# Load at-site data
if site_source=="usgs":
    if len(site_file) != 8:
        print("Must provide valid USGS site number (8-digit string) for at-site data")
    else:
        site_peaks = nwis_peak_import(site=site_file)
        var = "peak"
else:
    site_peaks = csv_peak_import(site_file)
    var = site_peaks.columns[0]

site_peaks.to_csv(f"{site}_site_peak.csv")
fig, ax = plt.subplots(figsize=(6.25, 4))
plt.plot(site_peaks.index,site_peaks[var],marker="o",linewidth=0,label="Site Peaks")

# MOVE (if applicable)
if move:
    if move_source == "usgs":
        if len(move_file) != 8:
            print("Must provide valid USGS site number (8-digit string) for at-site data")
        else:
            move_peaks = nwis_import(site=move_file)
            mvar = "peak"
    else:
        move_peaks = csv_peak_import(move_file)
        mvar = move_peaks.columns[1]
    move_peaks.to_csv(f"{site}_move_peak.csv")
    plt.plot(move_peaks.index, move_peaks[mvar],marker="x",linewidth=0,label="MOVE Peaks")

plt.ylabel(get_varlabel(var))
ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
plt.legend()
plt.savefig(f"{site}_site_peak.jpg",bbox_inches='tight',dpi=300)