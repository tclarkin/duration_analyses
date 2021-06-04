# -*- coding: utf-8 -*-
"""
Created on May 25 2021
Volume Duration Script  (v1)
@author: tclarkin (USBR 2021)

This script aids in volume frequency analysis by using user supplied continuous daily inflows and identifying annual
maximum average flows for periods specified (WY always added by default). Additionally, the user may have individual
traces of the WY plotted together.

This script can be run for all sites simultaneously
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
from functions import analyze_voldur,plot_voldur,plot_wyvol

### Begin User Input ###
os.chdir("C://Users//tclarkin//Documents//Projects//Roosevelt_Dam_IE//duration_analyses//")

# Site information and user selections
sites = ["TRD"] # list, site or dam names
durations = [1,3,4,5,7] # Duration in days
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
    # Load inflows
    data = pd.read_csv(f"{site}_site_data.csv",parse_dates=True,index_col=0)

    # Create list to store all duration data
    site_dur = list()
    if move==True:
        move_dur = list()

    # Loop through durations and analyze
    durations.insert(0,"WY")
    for dur in durations:
        print(f'Analyzing duration flows for {dur} days')
        df_dur = analyze_voldur(data,dur)
        site_dur.append(df_dur)
        df_dur.to_csv(f"volume/{site}_{dur}.csv")

        if move:
            print('Analyzing duration flows for move...')
            move_data = pd.read_csv(f"{site}_move_data.csv", parse_dates=True, index_col=0)
            df_movedur = analyze_voldur(move_data,dur)
            df_movedur.to_csv(f"volume/{site}_{dur}_move.csv")

            if dur=="WY":
                var = "annual_volume"
            else:
                var = "avg_flow"
            df_move = pd.DataFrame(index=df_movedur.index)
            df_move[var+"_x"] = df_movedur[var]
            df_move = df_move.dropna(how="any")
            df_move = df_move.merge(df_dur[var],left_index=True,right_index=True,how="left")
            df_move = df_move.fillna("NA")
            df_move.to_csv(f"volume/{site}_{dur}_move_input.txt",sep=" ",index_label="WY")
            move_dur.append(df_move)

    if (plot) & ("WY" in durations):
        print("Plotting WYs")
        for wy in df_dur.index:
            plot_voldur(data,wy,site_dur,durations)
            plt.savefig(f"volume/{site}_{wy}.jpg", bbox_inches="tight", dpi=300)

    if (wyplot) & ("WY" in durations):
        print("Plotting WY traces")
        doy_data = plot_wyvol(data, site_dur[0], wy_division)
        plt.savefig(f"volume/{site}_WY_plot.jpg", bbox_inches="tight", dpi=300)

        doy_data.to_csv(f"volume/{site}_doy.csv")
