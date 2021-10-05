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
from functions import analyze_voldur,plot_voldur,plot_wyvol

### Begin User Input ###
#os.chdir("C://Users//tclarkin//Documents//Projects//Anderson_Ranch_Dam//duration_analyses//")

# Site information and user selections
sites = ["coolidge"] # list, site or dam names
durations = ["peak",1,7,15] # Duration in days ("peak" can also be included)
wy_division = "WY" # "WY" or "CY"
move = False  # Will prepare MOVE3 input files for each duration
plot = True  # Will plot each WY with all durations
wyplot = True   # Will create a plot with each WY traced over the same dates

### Begin Script ###
# Check for output directory
if not os.path.isdir("volume"):
    os.mkdir("volume")

# Loop through sites
for site in sites:
    # Load data
    data = pd.read_csv(f"{site}_site_daily.csv",parse_dates=True,index_col=0)

    # Create list to store all duration data
    site_dur = list()
    if move==True:
        move_dur = list()

    # Loop through durations and analyze
    if "peak" in durations:
        if os.path.isfile(f"{site}_site_peak.csv"):
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

    for dur in durations_sel:
        if dur=="peak":
            continue
        print(f'Analyzing duration for {dur} days')
        df_dur = analyze_voldur(data,dur)
        site_dur.append(df_dur)
        df_dur.to_csv(f"volume/{site}_{dur}.csv")

        if move:
            print('Analyzing duration for move...')
            move_data = pd.read_csv(f"{site}_move_daily.csv", parse_dates=True, index_col=0)
            df_movedur = analyze_voldur(move_data,dur)
            df_movedur.to_csv(f"volume/{site}_{dur}_move.csv")

            if dur=="WY":
                var = "annual_sum"
            else:
                var = "avg"
            df_move = pd.DataFrame(index=df_movedur.index)
            df_move[var+"_x"] = df_movedur[var]
            df_move = df_move.dropna(how="any")
            df_move = df_move.merge(df_dur[var],left_index=True,right_index=True,how="left")
            df_move = df_move.fillna("NA")
            df_move.to_csv(f"volume/{site}_{dur}_move_input.txt",sep=" ",index_label="WY")
            move_dur.append(df_move)

    if (plot):
        print("Plotting WYs")
        if (peaks):
            site_peaks = pd.read_csv(f"{site}_site_peak.csv", index_col=0)
            site_peaks["date"] = pd.to_datetime(df_dur["date"])

        for wy in df_dur.index:
            # plot flows and durations
            plot_voldur(data,wy,site_dur,durations_sel)

            # plot peaks
            if (peaks):
                if (wy not in site_peaks.index) or (pd.isnull(site_peaks.loc[wy, "date"])):
                    continue
                plt.plot(site_peaks.loc[wy,"date"],site_peaks.loc[wy,"peak"],marker="x",linewidth=0,label="Peak")
            plt.legend()
            plt.savefig(f"volume/{site}_{wy}.jpg", bbox_inches="tight", dpi=300)

    if (wyplot):
        print("Plotting WY traces")
        doy_data = plot_wyvol(data, site_dur[0], wy_division)
        plt.savefig(f"volume/{site}_WY_plot.jpg", bbox_inches="tight", dpi=300)

        doy_data.to_csv(f"volume/{site}_doy.csv")
