# -*- coding: utf-8 -*-
"""
Created on May 25 2021
Updated on Oct 12, 2023
Daily Data Preparation Script
@author: tclarkin (USBR 2021)

This script takes user input data and formats in a continuous timeseries for use in the remainin duration analyses.
scripts. This script should be run once for each site being analyzed.

If input csv files are used, suggest having two columns:
date: (dd-mmm-yyyy)
variable, where variable is "flow", "swe", or "stage" (no spaces): no commas

Alternatively, it can handle daily data from online sources:
 - usgs: site number (e.g., "09445000"),
 - hydromet: list of site, var, and region (e.g., ["site","var","region"]), and
 - snotel: triplets and params (e.g., 327_CO_SNTL+PRCP)

Seasons are either False (use entire year) or specified using a dictionary:
 - months {"name":[months],etc.}, or
 - start,stop {"name":[doy,doy]}

"""
import matplotlib.pyplot as plt
from src.functions import check_dir,simple_plot,get_varlabel,save_seasons
from src.data_functions import import_daily,season_subset,summarize_daily

### User Input ###
#os.chdir("")

# Site information and user selections
sites = ["06468170"] # list, site or dam names
wy_division = "WY" # "WY" or "CY"
site_sources = ["06468170"] # .csv file or other site info for supported data

# Optional data cleaning (remove sub "zero" values)
clean = True # remove any WYs with less than 300 days of data
zero = "average" # minimum flow value or "average"

# Optional seasonal selection
# Dictionary of seasons by months {"name":[months],etc.}, start/stop {"name":[start,stop]}, OR False
seasons = {"spring":[3,4,5,6]}

### Begin Script ###
for site,site_source in zip(sites,site_sources):
    print(f"Importing daily data for {site}...")
    # Check directories
    outdir = check_dir(site,"data")

    # Load, plot, and save at-site data
    site_daily = import_daily(site_source,wy_division,clean,zero)
    site_summary = summarize_daily(site_daily)
    simple_plot(site_daily,"Site Daily")
    site_daily.to_csv(f"{outdir}/{site}_site_daily.csv")
    print(f"Site data saved to {outdir}/{site}_site_daily.csv")
    site_summary.to_csv(f"{outdir}/{site}_site_summary.csv")
    print(f"Site summary saved to {outdir}/{site}_site_summary.csv")

    # Subset by season, if selected
    if isinstance(seasons,bool)==False:
        if all(seasons):
            var = site_daily.columns[0]
            # Subset, plot, and save seasonal data
            for s in seasons.keys():
                season_daily = season_subset(site_daily,seasons[s],var)
                plt.plot(season_daily.index, season_daily[var], linestyle="dashed", label=f"{s}")
                season_daily.to_csv(f"{outdir}/{site}_{s}_site_daily.csv")
                print(f"Seasonal data saved to {outdir}/{site}_{s}_site_daily.csv")

    # Save list of seasons
    save_seasons(site,seasons)

    # Complete and save plot
    plt.legend()
    plt.savefig(f"{outdir}/{site}_site_daily.jpg",bbox_inches='tight',dpi=600)

print("Complete")