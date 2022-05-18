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
#os.chdir("")

# Site information and user selections
site = 'caliham'  # site or dam name
wy_division = "WY" # "WY" or "CY"
site_source = "08207000" # usgs site number (e.g., "09445000") or .csv data file

# Optional seasonal selection
season = True # True or False
# Dictionary of seasons and months {"name":[months],etc.}
seasons = {"winter":[1,2,11,12],
            "spring":[3,4,5],
            "summer":[6,7,8,9,10]}

### Begin Script ###
if not os.path.isdir("data"):
    os.mkdir("data")

# Load at-site data
if ".csv" in site_source:
    # Load from .csv file
    site_peaks = csv_peak_import(site_source)
    var = site_peaks.columns[1]
else:
    # Load from usgs website
    if len(site_source) != 8:
        print("Must provide valid USGS site number (8-digit string) for at-site data")
    else:
        site_peaks = nwis_peak_import(site=site_source)
        var = "peak"

# Save data
site_peaks.to_csv(f"data/{site}_site_peak.csv")

# Plot data
fig, ax = plt.subplots(figsize=(6.25, 4))
plt.ylabel(get_varlabel(var))
plt.plot(site_peaks["date"],site_peaks[var],marker="o",linewidth=0,label="Site Peaks")
ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
ax.set_ylim([0,None])
plt.legend()
plt.savefig(f"data/{site}_site_peak.jpg",bbox_inches='tight',dpi=600)

if season:
    for s in seasons.keys():
        season_peaks = site_peaks.copy()
        season_peaks.loc[~pd.DatetimeIndex(season_peaks["date"]).month.isin(seasons[s]), var] = np.nan
        plt.plot(season_peaks["date"], season_peaks[var],marker="x",linewidth=0,label=f"{s} Site Data")
        plt.legend()
        plt.savefig(f"data/{site}_site_peak.jpg", bbox_inches='tight', dpi=600)
        season_peaks.to_csv(f"data/{site}_{s}_site_peak.csv")
        print(f"Seasonal peaks saved to data/{site}_{s}_site_peak.csv")

    if os.path.isfile(f"data/{site}_{s}_site_daily.csv"):
        site_daily = pd.read_csv(f"data/{site}_{s}_site_daily.csv",parse_dates=True,index_col=0)
        dvar = site_daily.columns[0]

        fig, ax = plt.subplots(figsize=(6.25, 4))
        plt.plot(site_daily.index, site_daily[dvar], label="Site Daily")
        plt.plot(season_peaks.date, season_peaks[var], marker="x", color="k",linewidth=0, label="Site Peaks")

        plt.legend()
        plt.savefig(f"data/{site}_{s}_site_peak_and_daily.jpg", bbox_inches='tight', dpi=600)

elif os.path.isfile(f"data/{site}_site_daily.csv"):
    site_daily = pd.read_csv(f"data/{site}_site_daily.csv",parse_dates=True,index_col=0)
    dvar = site_daily.columns[0]

    fig, ax = plt.subplots(figsize=(6.25, 4))
    plt.plot(site_daily.index, site_daily[dvar], label="Site Daily")
    plt.plot(site_peaks.date, site_peaks[var], marker="x", color="k",linewidth=0, label="Site Peaks")

    plt.legend()
    plt.savefig(f"data/{site}_site_peak_and_daily.jpg", bbox_inches='tight', dpi=600)