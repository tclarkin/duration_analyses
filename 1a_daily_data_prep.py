# -*- coding: utf-8 -*-
"""
Created on May 25 2021
Updated on Oct 3, 2022
Daily Data Preparation Script (v1)
@author: tclarkin (USBR 2021)

This script takes user supplied USGS gage or other data in .csv format and compresses into a continuous timeseries
for use in flow, critical and volume duration analyses. Option to "clean" data, by removing WYs with less than 300 days

This script should be run once for each site being analyzed. If input csv files are used, suggest having two columns:
date: (dd-mmm-yyyy)
variable, where variable is "flow", "swe", or "stage" (no spaces)

"""
import matplotlib.pyplot as plt
from src.functions import check_dir,simple_plot
from src.data_functions import import_daily,season_subset

### User Input ###
#os.chdir("")

# Site information and user selections
sites = ['REGelephant',]  # list, site or dam names
wy_division = "WY" # "WY" or "CY"
site_sources = ['input_data/elephant_reg.csv'] # usgs site numbers (e.g., "09445000") or .csv data files

# Optional data cleaning (remove sub "zero" values)
clean = False # remove any WYs with less than 300 days of data
zero = "average" # minimum flow value or "average"

# Optional seasonal selection
season = False # True or False
# Dictionary of seasons and months {"name":[months],etc.}
seasons = {"winter":[1,2,11,12],
            "spring":[3,4,5,6,7],
            "summer":[8,9,10],
           "doy":[30,150]}

### Begin Script ###
for site,site_source in zip(sites,site_sources):
    print(site)
    # Check directories
    outdir = check_dir(site,"data")

    # Load, plot, and save at-site data
    site_daily,site_summary = import_daily(site_source,wy_division,clean,zero)
    simple_plot(site_daily,"Site Daily")
    site_daily.to_csv(f"{outdir}/{site}_site_daily.csv")
    print(f"Site data saved to {outdir}/{site}_site_daily.csv")
    site_summary.to_csv(f"{outdir}/{site}_site_summary.csv")
    print(f"Site summary saved to {outdir}/{site}_site_summary.csv")

    # Subset by season, if selected
    if season:
        var = site_daily.columns[0]
        # Subset, plot, and save seasonal data
        for s in seasons.keys():
            season_daily = season_subset(site_daily,seasons[s],var)
            plt.plot(season_daily.index, season_daily[var], linestyle="dashed", label=f"{s}")
            season_daily.to_csv(f"{outdir}/{site}_{s}_site_daily.csv")
            print(f"Seasonal data saved to {outdir}/{site}_{s}_site_daily.csv")

    # Complete and save plot
    plt.legend()
    plt.savefig(f"{outdir}/{site}_site_daily.jpg",bbox_inches='tight',dpi=600)
