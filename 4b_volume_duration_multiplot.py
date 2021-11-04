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
import numpy as np
import matplotlib.pyplot as plt
from functions import plot_trendsshifts,plot_normality,plot_voldurpp,plot_voldurpdf,plot_voldurmonth
from statsmodels.graphics import tsaplots

### Begin User Input ###
#os.chdir("C://Users//tclarkin//Documents//Projects//Anderson_Ranch_Dam//duration_analyses//")

# Site information and user selections
sites = ["ARD_swe"] # list, site or dam names
durations = ["WY",1] # Duration in days ("peak" can also be included)
wy_division = "WY" # "WY" or "CY"
idaplot = True      # Will create initial data analysis plots
ppplot = True       # Will create a plot with all durations plotted with plotting positions (using alpha below)
alpha = 0           # alpha for plotting positions
pdfplot = True      # Plot probability density function of data
monthplot = True    # Plot monthly distribution of annual peaks
eventdate = "max"   # When to plot seasonality: "start", "mid", "end", or "max"

### Begin Script ###

# Check for output directory
if not os.path.isdir("volume"):
    print("No volume directory. Please run 4a_volume_duration_analysis.py before using this script")
if not os.path.isdir("plot"):
    os.mkdir("plot")

# Loop through sites
for site in sites:
    print(f"Analyzing {site}")
    site_dur = list()
    site_sum = pd.DataFrame()
    data = pd.read_csv(f"data/{site}_site_daily.csv", parse_dates=True, index_col=0)

    if "peak" in durations:
        if os.path.isfile(f"data/{site}_site_peak.csv"):
            peaks = True
            durations_sel = durations
            durations_sel.remove("peak")
            durations_sel.append("peak")
        else:
            peaks = False
            durations_sel = durations
            durations_sel.remove("peak")
    else:
        peaks = False
        durations_sel = durations

    if "WY" in durations:
        print("Removing WY from list of durations.")
        durations_sel = durations
        durations_sel.remove("WY")

    for dur in durations_sel:
        if dur == "peak":
            df_dur = pd.read_csv(f"data/{site}_site_peak.csv",index_col=0)
            df_dur["date"] = pd.to_datetime(df_dur["date"])
        else:
            df_dur = pd.read_csv(f"volume/{site}_{dur}.csv",index_col=0)

            if eventdate not in str(data.columns):
                date_used = "date"
            else:
                date_used = eventdate

            df_dur[eventdate] = pd.to_datetime(df_dur[eventdate])

        df_dur = df_dur.dropna()
        site_dur.append(df_dur)
        var = df_dur.columns[1]

        site_sum.loc[dur,"N"] = len(df_dur)
        site_sum.loc[dur, "mean"] = df_dur[var].mean()
        site_sum.loc[dur, "median"] = df_dur[var].median()
        site_sum.loc[dur, "sd"] = df_dur[var].std()
        site_sum.loc[dur, "skew"] = df_dur[var].skew()
        site_sum.loc[dur, "log_mean"] = np.log10(df_dur[var]).mean()
        site_sum.loc[dur, "log_median"] = np.log10(df_dur[var]).median()
        site_sum.loc[dur, "log_sd"] = np.log10(df_dur[var]).std()
        site_sum.loc[dur, "log_skew"] = np.log10(df_dur[var]).skew()

    site_sum.to_csv(f"volume/{site}_stats_summary.csv")

    # Plot data
    if idaplot:
        print("Conducting initial data analysis...")
        # Check for output directory
        if not os.path.isdir("ida"):
            os.mkdir("ida")
        for d in range(0,len(durations_sel)):
            evs = site_dur[d]
            dur = durations_sel[d]
            var = evs.columns[1]
            print(f'{dur}...')

            # Check for trends and shifts
            plot_trendsshifts(evs,dur,var)
            plt.savefig(f"ida/{site}_{dur}_trends&shifts_plot.jpg", bbox_inches="tight", dpi=600)

            # Check for autocorrelation
            fig = tsaplots.plot_acf(evs[var], lags=20)
            fig.set_size_inches(6.25, 4)
            plt.ylabel("Autocorrelation")
            plt.xlabel("Lag K, in years")
            plt.savefig(f"ida/{site}_{dur}_acf_plot.jpg", bbox_inches="tight", dpi=600)

            # Check for normality
            plot_normality(evs,dur,var)
            plt.savefig(f"ida/{site}_{dur}_normality_plot.jpg", bbox_inches="tight", dpi=600)

    if ppplot:
        print("Plotting with plotting positions")
        plot_voldurpp(site,site_dur,durations_sel,alpha)
        plt.savefig(f"plot/{site}_pp_plot.jpg", bbox_inches="tight", dpi=600)

    if pdfplot:
        print("Plotting with probability density function")
        plot_voldurpdf(site_dur,durations_sel)
        plt.savefig(f"plot/{site}_pdf_plot.jpg", bbox_inches="tight", dpi=600)

    if monthplot:
        print("Plotting with monthly distributions")
        for stat in ["count","mean","max"]:
            plot_voldurmonth(site_dur,durations_sel,stat,eventdate,wy_division)
            plt.savefig(f"plot/{site}_{eventdate}_month_{stat}_plot.jpg", bbox_inches="tight", dpi=600)

