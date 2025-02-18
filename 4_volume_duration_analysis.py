# -*- coding: utf-8 -*-
"""
Created on May 25 2021
Updated on Oct 4, 2022
Volume Duration Script  (v1)
@author: tclarkin (USBR 2021)

This script aids in volume frequency analysis by using user supplied continuous daily data and identifying annual
maximum average values for periods specified (WY always added by default). Additionally, the user may have individual
traces of the WY plotted together.

This script can be run for all sites simultaneously
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from src.functions import check_dir,get_seasons,save_seasons
from src.vol_functions import analyze_voldur,init_voldurplot,plot_voldur,cfs2af

### Begin User Input ###
#os.chdir("")

# Site information and user selections #
sites = ["choke_scale","frio_derby","frio_tilden","sanmiguel","frio_calliham","choke_full"] # list, site or dam names
seasonal = False # Boolean
durations = [1,3,7,15,30] # list uses same durations for all seasons, dict will apply specificly to each season included, use "all" for annual
wy_division = "CY" # "WY" or "CY"
plot_vol = True  # Will plot all WY volumes on a single plot
plot_wy = True  # Will plot each WY with all durations
concat = True # Will combine all tables

### Begin Script ###
# Check site directories
for site in sites:
    sitedir = check_dir(site, "flow")

# Loop through sites
for site in sites:
    print(f"Analyzing volume duration for {site}...")

    # Check for output and input directories
    outdir = check_dir(site, "volume")
    indir = f"{site}/data"
    if not os.path.isdir(indir):
        print("Input data directory not found.")

    # Import seasons
    season_df = get_seasons(site)
    seasons = season_df.index.to_list()

    # Check seasonality
    if seasonal:
        # If list, duplicate for each season
        if isinstance(durations, list):
            print("List of durations provided; repeating for each season...")
            dur_dict = dict()
            for season in seasons:
                dur_dict[season] = durations
                season_df.loc[season, "durations"] = str(durations)
            durations_season = dur_dict
        # If dict, check again season list, only analyze seasons with durations
        else:
            print("Dict of durations provided; parsing by season...")
            dur_dict = dict()
            season_analyze = list()
            for i,season in enumerate(seasons):
                print(season)
                if season in durations.keys():
                    dur_dict[season] = durations[season]
                    season_df.loc[season, "durations"] = str(durations[season])
                    season_analyze.append(season)
                else:
                    print(f"No durations provided for {season}. Durations must be provided for 'all' and each season...")
                    quit("Script run ended...")
            durations_season = dur_dict
            seasons = season_analyze
    else:
        seasons = [None]
        if isinstance(durations, dict):
            if "all" in durations.keys():
                durations_season = durations["all"]
            else:
                print(f"No durations provided for 'all'. Durations must be provided for 'all' and each season...")
                quit("Script run ended...")
        else:
            durations_season = durations
        season_df.loc["all", "durations"] = str(durations_season)

    # Save seasons
    save_seasons(site,season_df)

    for i,season in enumerate(seasons):
        if season is None:
            s=""
            durations_sel = durations_season.copy()
            if "WY" not in durations_sel:
                durations_sel.insert(0, "WY")
        else:
            if season=="all":
                s = ""
                durations_sel = durations_season[season]
                if "WY" not in durations_sel:
                    durations_sel.insert(0, "WY")
            else:
                s=f"_{season}"
                if "WY" in durations_sel:
                    durations_sel.remove("WY")
                durations_sel = durations_season[season]
        print(season)

        # Load data
        data = pd.read_csv(f"{indir}/{site}{s}_site_daily.csv",parse_dates=True,index_col=0)
        var = data.columns[0]
        decimal = str(data[var].head(1).item()).find('.')

        # Create list to store all duration data
        site_dur = list()
        site_sum = pd.DataFrame()

        if concat:
            site_df = pd.DataFrame()

        # Import peaks
        if "peak" in durations_sel:
            if os.path.isfile(f"{indir}/{site}{s}_site_peak.csv"):
                peaks = True
                print("Importing peak data")
                site_peaks = pd.read_csv(f"{indir}/{site}{s}_site_peak.csv", index_col=0)
                site_peaks["date"] = pd.to_datetime(site_peaks["date"])
                if concat:
                    site_df[pd.MultiIndex.from_product([["peaks"], list(site_peaks.columns)],
                                                names=["dur", "col"])] = site_peaks
            else:
                peaks = False
            durations_sel.remove("peak")
        else:
            peaks = False

        # Loop through durations and analyze
        for dur in durations_sel:
            # handle volumes
            print(f'Analyzing duration for {dur}')
            df_dur,dur_data = analyze_voldur(data,dur,decimal)
            dur_var = df_dur.columns[1]
            site_dur.append(df_dur)
            df_dur.to_csv(f"{outdir}/{site}{s}_{dur}.csv")
            if dur_data is not None:
                dur_data.to_csv(f"{outdir}/{site}{s}_{dur}_data.csv")

            if dur != "WY":
                site_sum.loc[dur,"N"] = len(df_dur)
                site_sum.loc[dur, "mean"] = df_dur[dur_var].mean()
                site_sum.loc[dur, "median"] = df_dur[dur_var].median()
                site_sum.loc[dur, "sd"] = df_dur[dur_var].std()
                site_sum.loc[dur, "skew"] = df_dur[dur_var].skew()
                site_sum.loc[dur, "log_mean"] = np.log10(df_dur[dur_var]).mean()
                site_sum.loc[dur, "log_median"] = np.log10(df_dur[dur_var]).median()
                site_sum.loc[dur, "log_sd"] = np.log10(df_dur[dur_var]).std()
                site_sum.loc[dur, "log_skew"] = np.log10(df_dur[dur_var]).skew()

            if concat:
                site_df[pd.MultiIndex.from_product([[dur], list(df_dur.columns)],
                                                   names=["dur", "col"])] = df_dur
        site_sum.to_csv(f"{outdir}/{site}{s}_stats_summary.csv")

        if concat:
            # Fix index and multiindex, export
            site_df = site_df.sort_index()
            site_df.columns = pd.MultiIndex.from_tuples(site_df.columns, names=("dur", "col"))
            site_df.to_csv(f"{outdir}/{site}{s}_all_durations.csv")

        if plot_vol:
            print("Plotting WYs")

            if "WY" in durations_sel:
                cum_data = data.copy()
                cum_data[var] = cfs2af(cum_data[var].cumsum())
                init_voldurplot(cum_data)
                if wy_division=="WY":
                    wy_start = cum_data.loc[(cum_data.index.month==10) & (cum_data.index.day==1)].index
                else:
                    wy_start = cum_data.loc[(cum_data.index.month == 1) & (cum_data.index.day == 1)].index
                plt.plot(cum_data.loc[wy_start,var],label="Water Year Data")
                plt.legend()
                plt.savefig(f"{outdir}/{site}{s}_wy_cumulative_plot.jpg", bbox_inches="tight", dpi=300)

        if plot_wy:
            for wy in df_dur.index:
                print(f"  {wy}")

                # plot flows and durations
                if pd.isna(data.loc[data["wy"]==wy]).all().any():
                    print("  Missing data. Skipping...")
                    continue
                else:
                    # Initialize plot
                    init_voldurplot(data,wy)
                    plot_voldur(f"{s.replace('_','')}",wy,site_dur,durations_sel)

                    # plot peaks
                    if peaks:
                        if (wy not in site_peaks.index) or (pd.isnull(site_peaks.loc[wy, "date"])):
                            continue
                        plt.plot(site_peaks.loc[wy,"date"],site_peaks.loc[wy,f"peak"],marker="x",linewidth=0,label=f"{s.replace('_','')} Peak")
                    plt.legend()
                    plt.savefig(f"{outdir}/{site}{s}_{wy}.jpg", bbox_inches="tight", dpi=300)

if concat and len(sites)>1:
    print("Preparing concatination tables")
    # Check for output directory
    outdir = check_dir("volume_concat")

    # Loop through seasons and all durations, concat all sites
    for s in seasons:
        if s is None:
            s = ""
        else:
            s = f"_{s}"

        for dur in durations_sel:
            print(dur)
            # If Peaks
            if dur=="peak" and peaks:
                peak_concat = pd.DataFrame()
                for site in sites:
                    indir = f"{site}/data"
                    if os.path.isfile(f"{indir}/{site}{s}_site_peak.csv"):
                        site_peaks = pd.read_csv(f"{indir}/{site}{s}_site_peak.csv", index_col=0)
                        site_peaks["date"] = pd.to_datetime(site_peaks["date"])
                        if peak_concat.empty:
                            peak_concat[pd.MultiIndex.from_product([[site], list(site_peaks.columns)],
                                                                   names=["dur", "col"])] = site_peaks
                        else:
                            site_peaks.columns = pd.MultiIndex.from_product([[site], list(site_peaks.columns)],
                                                                   names=["dur", "col"])
                            peak_concat = peak_concat.merge(site_peaks,left_index=True,right_index=True,how="outer")

                # Fix index and multiindex, export
                peak_final = pd.DataFrame(index=pd.Index(range(peak_concat.index.min(),peak_concat.index.max()+1)))
                peak_final = peak_final.merge(peak_concat,left_index=True,right_index=True,how="left")
                peak_final.columns = pd.MultiIndex.from_tuples(peak_concat.columns, names=("dur", "col"))
                peak_final.to_csv(f"{outdir}/{site}{s}_all_peaks.csv")

            # Volumes
            else:
                dur_concat = pd.DataFrame()
                for site in sites:
                    indir = f"{site}/volume"
                    if os.path.isfile(f"{indir}/{site}{s}_{dur}.csv"):
                        site_dur = pd.read_csv(f"{indir}/{site}{s}_{dur}.csv",index_col=0)
                        if dur_concat.empty:
                            dur_concat[pd.MultiIndex.from_product([[site], list(site_dur.columns)],
                                                                   names=["dur", "col"])] = site_dur
                        else:
                            site_dur.columns = pd.MultiIndex.from_product([[site], list(site_dur.columns)],
                                                                            names=["dur", "col"])
                            dur_concat = dur_concat.merge(site_dur, left_index=True, right_index=True, how="outer")

                if dur_concat.empty:
                    print("Nothing")
                else:
                    # Fix index and multiindex, export
                    dur_final = pd.DataFrame(index=pd.Index(range(dur_concat.index.min(),dur_concat.index.max()+1)))
                    dur_final = dur_final.merge(dur_concat,left_index=True,right_index=True,how="left")
                    dur_final.columns = pd.MultiIndex.from_tuples(dur_concat.columns, names=("dur", "col"))
                    dur_concat.to_csv(f"{outdir}/{site}{s}_all_{dur}.csv")

print("Script 4 Complete")
