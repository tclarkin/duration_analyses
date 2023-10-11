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
import matplotlib.pyplot as plt
from src.functions import check_dir
from src.vol_functions import analyze_voldur,init_voldurplot,plot_voldur
from itertools import chain

### Begin User Input ###
#os.chdir("")

# Site information and user selections #
sites = ["06468170","06468250","jamr","06470000"]  # list, site or dam names
seasons = None#{"spring":[3,4,5,6],"summer":[7,8,9,10]} # None returns all data, otherwise "season name"
durations = ["peak",1,7,15,30]#{"spring":[1,3,5,7,15],"summer":[1,3,5,7,15]}
wy_division = "WY" # "WY" or "CY"
plot = False  # Will plot each WY with all durations
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

    # Check seasonality
    if seasons is None or seasons == [None]:
        seasons = [None]
        durations = durations
    else:
        # If seasons are identified, make sure the annual is also considered
        if None not in seasons.keys():
            seasons[None] = None
            # also add annual durations
            all_durs = []
            for dur in durations.values():
                all_durs.append(dur)
            durations[None] = list(set(chain(*all_durs)))

    for i,s in enumerate(seasons):
        if s is None:
            s=""
            durations_sel = durations.copy()
        else:
            s=f"_{s}"
            durations_sel = durations.copy()
            durations_sel = list(durations_sel.values())[i]
        durations_sel.insert(0, "WY")

        # Load data
        data = pd.read_csv(f"{indir}/{site}{s}_site_daily.csv",parse_dates=True,index_col=0)

        # Create list to store all duration data
        site_dur = list()
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
            df_dur = analyze_voldur(data,dur)
            site_dur.append(df_dur)
            df_dur.to_csv(f"{outdir}/{site}{s}_{dur}.csv")

            if concat:
                site_df[pd.MultiIndex.from_product([[dur], list(df_dur.columns)],
                                                   names=["dur", "col"])] = df_dur
        if concat:
            # Fix index and multiindex, export
            site_df = site_df.sort_index()
            site_df.columns = pd.MultiIndex.from_tuples(site_df.columns, names=("dur", "col"))
            site_df.to_csv(f"{outdir}/{site}{s}_all_durations.csv")

        if plot:
            print("Plotting WYs")

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


