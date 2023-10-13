# -*- coding: utf-8 -*-
"""
Created on May 25 2021
Updated on Oct 4, 2022
Peak Data Preparation Script (v1)
@author: tclarkin (USBR 2021)

This script takes user supplied USGS gage or other peak data in .csv format and compresses into a summary of annual
peaks for use script 5 only

This script should be run once for each site being analyzed. If input csv files are used, suggest having three columns:
wy: (yyyy)
date: (dd-mmm-yyyy)
peak: no commas

"""
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from src.data_functions import import_peaks,season_subset,nwis_import
from src.functions import check_dir,simple_plot,save_seasons

### User Input ###
#os.chdir("")

# Site information and user selections
sites = ["06468170"]  # list, site or dam names
wy_division = "WY" # "WY" or "CY"
site_sources = ["06468170"] # .csv file, usgs site numbers (e.g., "09445000") or .csv data files

# Optional seasonal selection
# Dictionary of seasons by months {"name":[months],etc.}, start/stop {"name":[start,stop]}, OR False
seasons = {"spring":[3,4,5,6]}

### Begin Script ###
for site,site_source in zip(sites,site_sources):
    print(f"Importing peak data for {site}...")
    if site_source is None:
        continue
    outdir = check_dir(site,"data")

    # Load, plot, and save at-site data
    site_peaks,var = import_peaks(site_source)
    simple_plot(site_peaks,"Site Peaks",marker="o")
    plt.legend()
    plt.savefig(f"{outdir}/{site}_site_peak.jpg",bbox_inches='tight',dpi=300)

    # Find daily max to match peak
    data = pd.read_csv(f"{outdir}/{site}_site_daily.csv", parse_dates=True, index_col=0)
    dvar = data.columns[0]
    if data.wy.max() > site_peaks.index.max():
        for wy in range(site_peaks.index.max()+1,data.wy.max()):
            site_peaks.loc[wy,:] = [np.nan]*len(site_peaks.columns)

    for wy in site_peaks.index:
        peak_date = pd.to_datetime(site_peaks.loc[wy,"date"])
        if (peak_date>=data.index.min()) and (peak_date<=data.index.max()):
            site_peaks.loc[wy,"daily_flow"] = data.loc[peak_date,dvar]

    site_peaks.to_csv(f"{outdir}/{site}_site_peak.csv")
    print(f"Site data saved to {outdir}/{site}_site_peak.csv")

    if isinstance(seasons,bool)==False:
        if all(seasons):
            # Subset, plot, and save seasonal data
            for s in seasons.keys():
                season_peaks = season_subset(site_peaks,seasons[s],var)

                # Find other peaks (if available)
                data = pd.read_csv(f"{outdir}/{site}_{s}_site_daily.csv", parse_dates=True, index_col=0)
                dvar = data.columns[0]

                for wy in season_peaks.loc[pd.isna(season_peaks.peak)].index:
                    if wy not in data.wy.unique():
                        continue
                    daily_date = data.loc[data["wy"] == wy, dvar].idxmax()
                    if pd.isna(daily_date):
                        continue
                    daily_flow = data.loc[daily_date, dvar].item()
                    season_peaks.loc[wy,"date"] = daily_date
                    season_peaks.loc[wy,"daily_flow"] = daily_flow
                    if wy>=1990:
                        try:
                            inst_flow = nwis_import(site,"iv",f"{wy-1}-10-01",f"{wy}-09-30")
                        except ValueError:
                            continue
                        if inst_flow.empty:
                            continue
                        season_inst = season_subset(inst_flow,seasons[s],dvar)
                        inst_date = season_inst.flow.idxmax()
                        if pd.isna(inst_date):
                            continue
                        season_peaks.loc[wy,"peak"] = season_inst.loc[inst_date,dvar]
                        season_peaks.loc[wy, "date"] = inst_date
                        season_peaks.loc[wy, "daily_flow"] = data.loc[pd.to_datetime(inst_date.date()), dvar].item()

                simple_plot(season_peaks, f"{s} Peaks", marker="o")
                season_peaks.to_csv(f"{outdir}/{site}_{s}_site_peak.csv")
                print(f"Seasonal data saved to {outdir}/{site}_{s}_site_peak.csv")
                plt.legend()
                plt.savefig(f"{outdir}/{site}_{s}_site_peak.jpg", bbox_inches='tight', dpi=300)

    # Save list of seasons
    save_seasons(site, seasons)

print("Script 1b Complete")