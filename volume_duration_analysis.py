# -*- coding: utf-8 -*-
"""
Created on Wed Feb 17 2021
Critical Duration Script  (v3)
@author: tjclarkin (USBR 2020)

This script aids in volume frequency analysis by using user supplied continuous
daily inflows (Ifile) and identifying annual maximum average flows for periods
specified. Additionally, the user may...

This script requires:
    Ifile = continuous record of mean daily flows.

The user must:
    - Identify the working directory
    - Provide the dam name (dam)
    - Specify the above listed file (Ifile)
    - Define the following: durations (list)

"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from functions import analyze_voldur,plot_voldur,plot_wyvol

### Begin User Input ###
os.chdir("C://Users//tclarkin//Documents//Projects//Roosevelt_Dam_IE//duration_analyses//")

# Site information and user selections
site = "TRD"
durations = [1,3,4,5,7] # Duration in days
wy_division = "WY" # "WY" or "CY"
move = False  # Will prepare MOVE3 input files for each duratino
plot = True  # Will each WY with all durations
wyplot = True   # Will create a plot with each WY traced over the same dates

### Begin Script ###
# Load inflows
data = pd.read_csv(f"{site}_site_data.csv",parse_dates=True,index_col=0)

# Check for output directory
if not os.path.isdir("volume"):
    os.mkdir("volume")

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
    for e in df_dur.index:
        plot_voldur(data,site_dur,e,durations)
        plt.savefig(f"volume/{site}_{e}.jpg", bbox_inches="tight", dpi=300)

if (wyplot) & ("WY" in durations):
    print("Plotting WY traces")
    doy_data = plot_wyvol(data, site_dur[0], wy_division)
    plt.savefig(f"volume/{site}_WY_plot.jpg", bbox_inches="tight", dpi=300)

    doy_data.to_csv(f"volume/{site}_doy.csv")