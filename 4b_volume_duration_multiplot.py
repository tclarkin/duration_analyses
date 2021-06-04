# -*- coding: utf-8 -*-
"""
Created on May 25 2021
Plot Volume Duration Script  (v1)
@author: tclarkin (USBR 2021)

This script aids in volume frequency analysis by plotting the data and, optionally, creating various timeseries and
thresholds for use in analysis.

This script can be run for all sites simultaneously
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
from functions import plot_voldurpp,plot_voldurpdf,plot_voldurmonth

### Begin User Input ###
os.chdir("C://Users//tclarkin//Documents//Projects//Roosevelt_Dam_IE//duration_analyses//")

# Site information and user selections
sites = ["TRD"] # list, site or dam names
durations = [1,3,4,5,7] # Duration in days
wy_division = "WY" # "WY" or "CY"
ppplot = True       # Will create a plot with all durations plotted with plotting positions
pdfplot = True      # Plot probability density function of data
monthplot = True    # Plot monthly distribution of annual peaks
alpha = 0           # alpha for plotting positions

### Begin Script ###

# Check for output directory
if not os.path.isdir("volume"):
    print("No volume directory. Please run 4a_volume_duration_analysis.py before using this script")
if not os.path.isdir("plot"):
    os.mkdir("plot")

# Loop through sites
for site in sites:

    site_dur = list()
    for dur in durations:
        df_dur = pd.read_csv(f"volume/{site}_{dur}.csv",index_col=0)
        df_dur["date"] = pd.to_datetime(df_dur["date"])
        site_dur.append(df_dur)

    # Plot data
    if ppplot:
        print("Plotting with plotting positions")
        plot_voldurpp(site_dur,durations,"avg_flow",alpha)
        plt.savefig(f"plot/{site}_pp_plot.jpg", bbox_inches="tight", dpi=300)

    if pdfplot:
        print("Plotting with probability density function")
        plot_voldurpdf(site_dur,durations,"avg_flow")
        plt.savefig(f"plot/{site}_pdf_plot.jpg", bbox_inches="tight", dpi=300)

    if monthplot:
        print("Plotting with monthly distributions")
        plot_voldurmonth(site_dur,durations,"avg_flow","count",wy_division)
        plt.savefig(f"plot/{site}_month_count_plot.jpg", bbox_inches="tight", dpi=300)

        plot_voldurmonth(site_dur,durations,"avg_flow","mean",wy_division)
        plt.savefig(f"plot/{site}_month_mean_plot.jpg", bbox_inches="tight", dpi=300)

        plot_voldurmonth(site_dur,durations,"avg_flow","max",wy_division)
        plt.savefig(f"plot/{site}_month_max_plot.jpg", bbox_inches="tight", dpi=300)