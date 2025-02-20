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
from src.plot_functions import plot_trendsshifts,plot_normality,plot_voldurpp,plot_voldurpdf,plot_voldurmonth,mannwhitney,plot_date_trend,acf

### Begin User Input ###
#os.chdir("")

# Site information and user selections
sites = ["choke_scale","frio_derby","frio_tilden","sanmiguel","frio_calliham","choke","choke_full"] # list, site or dam names
seasonal = False # Boolean
wy_division = "CY" # "WY" or "CY"
idaplot = True      # Will create initial data analysis plots
ppplot = True       # Will create a plot with all durations plotted with plotting positions
pdfplot = True      # Plot probability density function of data
monthplot = True    # Plot monthly distribution of annual peaks
eventdate = "start"   # When to plot seasonality: "start", "mid", "end", or "max"

### Begin Script ###
# Loop through sites
for site in sites:
    print(f"Preparing plots for {site}...")
    outdir = check_dir(f"{site}/plot")

    # Check for output and input directories
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

    for season in seasons:
        if season is None:
            durations_season = durations
            s=""
            durations_season.append("WY")
        else:
            durations_season = durations[season]
            if season=="all":
                s=""
                durations_season.append("WY")
            else:
                s=f"_{season}"

        if durations_season is None:
            continue

        print(season)

        # Begin analysis
        site_dur = list()
        remove_dur = list()
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

        if "WY" in durations_season and s!="":
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
                # drop empty rows
                df_dur.dropna(how="all", inplace=True)

                if eventdate not in list(df_dur.columns):
                    date_used = "date"
                    if dur == "WY":
                        df_dur[date_used] = df_dur.index

                    df_dur[eventdate] = pd.to_datetime(df_dur[date_used])

            #df_dur = df_dur.dropna()
            site_dur.append(df_dur)
            var = df_dur.columns[1]

        for r in remove_dur:
            durations_sel.remove(r)

        # Plot data
        if idaplot:
            print("Conducting initial data analysis...")
            # Check for output directory
            for evs,dur in zip(site_dur,durations_sel):
                var = evs.columns[1]
                print(f'{dur}...')

                # Check for trends and shifts
                plot_trendsshifts(evs,dur,var)
                plt.savefig(f"{outdir}/{site}{s}_{dur}_trends&shifts_plot.jpg", bbox_inches="tight", dpi=600)

                # Check for trends and shifts
                plot_date_trend(evs,dur,wy_division)
                plt.savefig(f"{outdir}/{site}{s}_{dur}_start_trends&shifts_plot.jpg", bbox_inches="tight", dpi=600)

                # Check for mann whitney
                mannwhitney(evs,dur,var)
                plt.savefig(f"{outdir}/{site}{s}_{dur}_mannwhitney_plot.jpg", bbox_inches="tight", dpi=600)

                # TODO count change points AND add trends and shifts around confirmed change points...

                # Check for autocorrelation
                if len(evs.index) < 20:
                    continue
                acf(evs,var)
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