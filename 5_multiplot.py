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
from src.functions import check_dir,get_seasons,get_list
from src.plot_functions import plot_trendsshifts,plot_normality,plot_voldurpp,plot_voldurpdf,plot_voldurmonth,mannwhitney
from statsmodels.graphics import tsaplots

### Begin User Input ###
#os.chdir("")

# Site information and user selections
sites = ["06468170"]  # list, site or dam names
seasonal = True # Boolean
wy_division = "WY" # "WY" or "CY"
decimal = 1 # number of decimal places to use in data
idaplot = True      # Will create initial data analysis plots
ppplot = True       # Will create a plot with all durations plotted with plotting positions
pdfplot = True      # Plot probability density function of data
monthplot = True    # Plot monthly distribution of annual peaks
eventdate = "start"   # When to plot seasonality: "start", "mid", "end", or "max"

### Begin Script ###
# Loop through sites
for site in sites:
    print(f"Preparing plots for {site}...")

    # Check for output and input directories
    outdir = check_dir(site, "plot")
    indir = f"{site}/data"
    if not os.path.isdir(indir):
        print("Input data directory not found.")
    voldir = f"{site}/volume"
    if not os.path.isdir(voldir):
        print("Input volume directory not found.")

    # Import seasons
    season_df = get_seasons(site)
    seasons = season_df.index.to_list()

    # Get durations for seasons
    if seasonal:
        dur_dict = dict()
        for season in seasons:
            dur_dict[season] = get_list(season_df.loc[season,"durations"])
        durations = dur_dict
    else:
        seasons = [None]
        dur_dict = dict()
        durations = get_list(season_df.loc["all","durations"])

    print(durations)

    for season in seasons:
        if season is None:
            durations_season = durations
            s=""
        else:
            durations_season = durations[season]
            if season=="all":
                s=""
            else:
                s=f"_{season}"

        if durations_season is None:
            continue

        print(season)

        # Begin analysis
        site_dur = list()
        remove_dur = list()
        site_sum = pd.DataFrame()
        data = pd.read_csv(f"{indir}/{site}{s}_site_daily.csv", parse_dates=True, index_col=0)

        if "peak" in durations_season:
            if os.path.isfile(f"{indir}/{site}{s}_site_peak.csv"):
                peaks = True
                durations_sel = durations_season
                durations_sel.remove("peak")
                durations_sel.append("peak")
            else:
                peaks = False
                durations_sel = durations_season
                durations_sel.remove("peak")
        else:
            peaks = False
            durations_sel = durations_season

        if "WY" in durations_season:
            print("Removing WY from list of durations.")
            durations_sel = durations_season
            durations_sel.remove("WY")

        for dur in durations_sel:
            if dur is None:
                continue
            print(dur)
            if dur == "peak":
                try:
                    df_dur = pd.read_csv(f"{indir}/{site}{s}_site_peak.csv",index_col=0)
                except FileNotFoundError:
                    print(f"{indir}/{site}{s}_site_peak.csv not found...")
                    continue
            else:
                try:
                    df_dur = pd.read_csv(f"{voldir}/{site}{s}_{dur}.csv",index_col=0)
                except FileNotFoundError:
                    print(f"{voldir}/{site}{s}_{dur}.csv not found...")
                    continue

            if df_dur.empty:
                remove_dur.append(dur)
                continue
            else:
                if eventdate not in list(df_dur.columns):
                    date_used = "date"
                else:
                    date_used = eventdate

                df_dur[date_used] = pd.to_datetime(df_dur[date_used])

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

        for r in remove_dur:
            durations_sel.remove(r)
        site_sum.to_csv(f"{voldir}/{site}{s}_stats_summary.csv")

        # Plot data
        if idaplot:
            print("Conducting initial data analysis...")
            # Check for output directory
            for evs,dur in zip(site_dur,durations_sel):
                var = evs.columns[1]
                print(f'{dur}...')

                #TODO Need to improve the trends, shifts tests

                # Check for trends and shifts
                plot_trendsshifts(evs,dur,var)
                plt.savefig(f"{outdir}/{site}{s}_{dur}_trends&shifts_plot.jpg", bbox_inches="tight", dpi=600)

                # Check for mann whitney
                mannwhitney(evs,dur,var,10)
                plt.savefig(f"{outdir}/{site}{s}_{dur}_mannwhitney_plot.jpg", bbox_inches="tight", dpi=600)

                # Check for autocorrelation
                if len(evs.index) < 20:
                    continue
                fig = tsaplots.plot_acf(evs[var], lags=20)
                fig.set_size_inches(6.25, 4)
                plt.ylabel("Autocorrelation")
                plt.xlabel("Lag K, in years")
                plt.savefig(f"{outdir}/{site}{s}_{dur}_acf_plot.jpg", bbox_inches="tight", dpi=600)

                # Check for normality
                plot_normality(evs,dur,var)
                plt.savefig(f"{outdir}/{site}{s}_{dur}_normality_plot.jpg", bbox_inches="tight", dpi=600)

        if ppplot:
            print("Plotting with plotting positions")
            plot_voldurpp(site,site_dur,durations_sel,alpha=0)
            plt.savefig(f"{outdir}/{site}{s}_pp_plot.jpg", bbox_inches="tight", dpi=600)

        if pdfplot:
            print("Plotting with probability density function")
            plot_voldurpdf(site_dur,durations_sel)
            plt.savefig(f"{outdir}/{site}{s}_pdf_plot.jpg", bbox_inches="tight", dpi=600)

        if monthplot:
            print("Plotting with monthly distributions")
            for stat in ["count","mean","max"]:
                plot_voldurmonth(site_dur,durations_sel,stat,eventdate,wy_division)
                plt.savefig(f"{outdir}/{site}{s}_{eventdate}_month_{stat}_plot.jpg", bbox_inches="tight", dpi=600)

print("Script 5 Complete")