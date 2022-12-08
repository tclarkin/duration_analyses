# -*- coding: utf-8 -*-
"""
Created on May 25 2021
Updated on Oct 4, 2022
Peak Data Preparation Script (v1)
@author: tclarkin (USBR 2021)

This script takes user supplied USGS gage or other peak data in .csv format and compresses into a summary of annual
peaks for use scripts 4a and 4b only

This script should be run once for each site being analyzed. If input csv files are used, suggest having three columns:
wy: (yyyy)
date: (dd-mmm-yyyy)
"peak"

"""
import matplotlib.pyplot as plt
from src.data_functions import import_peaks,season_subset
from src.functions import check_dir,simple_plot

### User Input ###
#os.chdir("")

# Site information and user selections
sites = ['08329500']  # list, site or dam names
wy_division = "WY" # USGS Peaks are only available for WY
site_sources = ['08329500'] # usgs site numbers (e.g., "09445000") or .csv data files

# Optional seasonal selection
# Dictionary of seasons and months {"name":[months],etc.}
seasons = {"winter":[1,2,11,12],
            "spring":[3,4,5],
            "summer":[6,7,8,9,10],
           "doy":[30,150]}

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
    site_peaks.to_csv(f"{outdir}/{site}_site_peak.csv")
    print(f"Site data saved to {outdir}/{site}_site_peak.csv")

    if isinstance(seasons,bool)==False:
        if all(seasons):
            # Subset, plot, and save seasonal data
            for s in seasons.keys():
                season_peaks = season_subset(site_peaks,seasons[s],var)
                simple_plot(season_peaks, f"{s} Peaks", marker="o")
                season_peaks.to_csv(f"{outdir}/{site}_{s}_site_peak.csv")
                print(f"Seasonal data saved to {outdir}/{site}_{s}_site_peak.csv")
            plt.legend()
            plt.savefig(f"{outdir}/{site}_{s}_site_peak.jpg", bbox_inches='tight', dpi=300)