# -*- coding: utf-8 -*-
"""
Created on May 25 2021
Daily Data Preparation Script (v1)
@author: tclarkin (USBR 2021)

This script takes user supplied USGS gage or other data in .csv format and compresses into a continuous timeseries
for use in flow, critical and volume duration analyses. Option to "clean" data, by removing WYs with less than 300 days

This script should be run once for each site being analyzed. If input csv files are used, suggest having two columns:
date: (dd-mmm-yyyy)
variable, where variable is "flow", "swe", or "stage" (no spaces)

"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from functions import nwis_import,csv_daily_import,get_varlabel

### User Input ###
#os.chdir("")

# Site information and user selections
site = 'sanmarc_unreg'  # site or dam name
wy_division = "WY" # "WY" or "CY"
site_source = 'sanmarc_unreg.csv' # usgs site number (e.g., "09445000") or .csv data file
clean = True # remove any WYs with less than 300 days of data
zero = 0

# Optional deregulation of at-site data
dereg_source = False # False, usgs site number (e.g., "09445000") or .csv data file
dereg_shift = 0 # days to shift (+ forward, - backward)
sign = "plus" # "plus" or "minus"

# Optional seasonal selection
season = True # True or False
# Dictionary of seasons and months {"name":[months],etc.}
seasons = {"winter":[1,2,11,12],
            "spring":[3,4,5,6,7],
            "summer":[8,9,10]}

### Begin Script ###
if not os.path.isdir("data"):
    os.mkdir("data")

# Load at-site data
if ".csv" in site_source:
    # Load from .csv file
    site_daily = csv_daily_import(site_source, wy=wy_division)
    var = site_daily.columns[0] # infer variable by column name
else:
    # Load from usgs website
    if len(site_source) != 8:
        print("Must provide valid USGS site number (8-digit string) for at-site data")
    else:
        site_daily = nwis_import(site=site_source,dtype="dv",wy=wy_division)
        var = "flow"

# Clean data, if selected
if clean:
    # Remove negative values
    site_daily.loc[site_daily[var] < zero, var] = zero

    # Remove WYs with less than 300 days of data or if last month is lower than September
    for wy in site_daily["wy"].unique():
        if pd.isna(site_daily.loc[site_daily["wy"] == wy, var]).sum() > 65:
            site_daily.loc[site_daily["wy"] == wy, var] = np.nan
        if site_daily.loc[site_daily["wy"] == wy, var].count() < 300:
            site_daily.loc[site_daily["wy"] == wy, var] = np.nan
        if site_daily.loc[site_daily["wy"]==wy].tail(1).month.item()<9:
            site_daily.loc[site_daily["wy"] == wy, var] = np.nan

# Plot data
fig, ax = plt.subplots(figsize=(6.25, 4))
plt.ylabel(get_varlabel(var))
ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
plt.plot(site_daily.index,site_daily[var],label="Site Data")

# Save data
site_daily.to_csv(f"data/{site}_site_daily.csv")
print(f"Site data saved to data/{site}_site_daily.csv")

# Deregulate, if selected
if dereg_source != False:
    if ".csv" in dereg_source:
        # Load from .csv file
        dereg_daily = csv_daily_import(dereg_source, wy=wy_division)
        dvar = dereg_daily.columns[0]
    else:
        # Load from usgs website
        if len(dereg_source) != 8:
            print("Must provide valid USGS site number (8-digit string) for dereg data")
        else:
            dereg_daily = nwis_import(site=dereg_source,dtype="dv",wy=wy_division)
            dvar = "flow"

    # Check if data loaded
    if dereg_daily is not None:
        # Deregulate data
        if sign == "plus":
            site_dereg = pd.DataFrame(site_daily[var] + dereg_daily[dvar])
        if sign == "minus":
            site_dereg = pd.DataFrame(site_daily[var] - dereg_daily[dvar])
        site_dereg.columns=[var]
        site_dereg.loc[site_dereg[var]<0,var] = 0
        site_daily[var] = site_dereg
        site_daily = site_daily.dropna()
    else:
        print("Failed to deregulate.")

    # Save deregulated data
    site_daily.to_csv(f"data/{site}_site_daily.csv")
    print(f"Dereguated data saved to data/{site}_dereg_site_daily.csv")

    # Plot deregulated data
    plt.plot(site_daily.index, site_daily[var],label="Dereg Site Data")

if season:
    for s in seasons.keys():
        season_daily = site_daily.copy()
        season_daily.loc[~season_daily["month"].isin(seasons[s]), var] = np.nan
        plt.plot(season_daily.index, season_daily[var],linestyle="dashed",label=f"{s} Site Data")
        season_daily.to_csv(f"data/{site}_{s}_site_daily.csv")
        print(f"Seasonal data saved to data/{site}_{s}_site_daily.csv")

# Complete and save plot
plt.legend()
if "Stage" not in get_varlabel(var):
    ax.set_ylim([0,None])
plt.savefig(f"data/{site}_site_daily.jpg",bbox_inches='tight',dpi=600)

#TODO add data summary