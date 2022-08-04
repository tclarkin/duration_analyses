# -*- coding: utf-8 -*-
"""
Created on May 25 2021
Volume Duration Script  (v1)
@author: tclarkin (USBR 2021)

This script aids in volume frequency analysis by using user supplied continuous daily data and identifying annual
maximum average values for periods specified (WY always added by default). Additionally, the user may have individual
traces of the WY plotted together.

This script can be run for all sites simultaneously
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
from functions import analyze_voldur,plot_voldur

### Begin User Input ###
#os.chdir("")

# Site information and user selections
sites = ["for"] # list, site or dam names
durations = [] # Duration in days ("peak" can also be included)
wy_division = "WY" # "WY" or "CY"
plot = True  # Will plot each WY with all durations

### Begin Script ###
# Check for output directory
if not os.path.isdir("volume"):
    os.mkdir("volume")

# Loop through sites
for site in sites:
    # Load data
    data = pd.read_csv(f"data/{site}_site_daily.csv",parse_dates=True,index_col=0)

    # Create list to store all duration data
    site_dur = list()

    # Loop through durations and analyze
    if "peak" in durations:
        if os.path.isfile(f"data/{site}_site_peak.csv"):
            peaks = True
            durations_sel = durations
            durations_sel.remove("peak")
        else:
            peaks = False
            durations_sel = durations
    else:
        peaks = False
        durations_sel = durations

    durations_sel.insert(0,"WY")

    #TODO add all data
    for dur in durations_sel:
        if dur=="peak":
            continue
        print(f'Analyzing duration for {dur} days')
        df_dur = analyze_voldur(data,dur)
        site_dur.append(df_dur)
        df_dur.to_csv(f"volume/{site}_{dur}.csv")

    if (plot):
        print("Plotting WYs")
        if peaks:
            site_peaks = pd.read_csv(f"data/{site}_site_peak.csv", index_col=0)
            site_peaks["date"] = pd.to_datetime(site_peaks["date"])

        for wy in df_dur.index:
            print(f"  {wy}")
            # plot flows and durations
            if pd.isna(data.loc[data["wy"]==wy]).all().any():
                print("  Missing data. Skipping...")
                continue
            else:
                plot_voldur(data,wy,site_dur,durations_sel)

                # plot peaks
                if peaks:
                    if (wy not in site_peaks.index) or (pd.isnull(site_peaks.loc[wy, "date"])):
                        continue
                    plt.plot(site_peaks.loc[wy,"date"],site_peaks.loc[wy,"peak"],marker="x",linewidth=0,label="Peak")
                plt.legend()
                plt.savefig(f"volume/{site}_{wy}.jpg", bbox_inches="tight", dpi=600)

