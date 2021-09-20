# -*- coding: utf-8 -*-
"""
Created on May 25 2021
Data Preparation Script (v1)
@author: tclarkin (USBR 2021)

This script takes user supplied USGS gage or other data in .csv format and compresses into a continuous timeseries
for use in flow, critical and volume duration analyses. Option to "clean" data, by removing WYs with less than 300 days

This script should be run once for each site being analyzed

"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from functions import nwis_daily_import,csv_daily_import

### User Input ###
#os.chdir("C://Users//tclarkin//Documents//Projects//El_Vado_Dam//duration_analyses//")

# Site information and user selections
site = 'ElVado'  # site or dam name
wy_division = "WY" # "WY" or "CY"
site_source = "file" # "usgs" or "file"
site_file = "ElVadoInflows.csv" # usgs site number (e.g., "09445000") or .csv data file
clean = True # remove any WYs with less than 300 days of data

# Deregulation of at-site data
deregulate = False
dereg_source = "usgs" # "usgs" or "file"
dereg_file = "08073700" # usgs site number (e.g., "09445000") or .csv data file
dereg_shift = 0 # days to shift (+ forward, - backward)
sign = "plus" # "plus" or "minus"

# MOVE data prep
move = False
move_source = "usgs" # "usgs" or "file"
move_file = "08073700" # usgs site number (e.g., "09445000") or .csv data file

### Begin Script ###
# Load at-site data
if site_source=="usgs":
    if len(site_file) != 8:
        print("Must provide valid USGS site number (8-digit string) for at-site data")
    else:
        site_daily = nwis_daily_import(site=site_file,dtype="dv",wy=wy_division)
        var = "flow"
else:
    site_daily = csv_daily_import(site_file,wy=wy_division)
    var = site_daily.columns[0]

if clean:
    # Remove negative values
    site_daily.loc[site_daily[var] < 0, var] = 0

    # Remove WYs with less than 300 days of data or if last month is lower than September
    for wy in site_daily["wy"].unique():
        if pd.isna(site_daily.loc[site_daily["wy"] == wy, var]).sum() > 65:
            site_daily.loc[site_daily["wy"] == wy, var] = np.nan
        if site_daily.loc[site_daily["wy"]==wy].tail(1).month.item()<9:
            site_daily.loc[site_daily["wy"] == wy, var] = np.nan

site_daily.to_csv(f"{site}_site_daily.csv")
fig, ax = plt.subplots(figsize=(6.25, 4))
plt.plot(site_daily.index,site_daily[var],label="Site Data")

# Deregulate (if applicable)
if deregulate:
    if dereg_source == "usgs":
        if len(dereg_file) != 8:
            print("Must provide valid USGS site number (8-digit string) for dereg data")
        else:
            dereg_daily = nwis_daily_import(site=dereg_file,dtype="dv",wy=wy_division)
            dvar = "flow"
    else:
        dereg_daily = csv_daily_import(dereg_file, wy=wy_division)
        dvar = dereg_daily.columns[0]

    if "dereg_daily" is not None:
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
    site_daily.to_csv(f"{site}_site_daily.csv")
    plt.plot(site_daily.index, site_daily[var],label="Dereg Site Data")

# MOVE (if applicable)
if move:
    if move_source == "usgs":
        if len(move_file) != 8:
            print("Must provide valid USGS site number (8-digit string) for at-site data")
        else:
            move_daily = nwis_daily_import(site=move_file, dtype="dv", wy=wy_division)
            mvar = "flow"
    else:
        move_daily = csv_daily_import(move_file,wy=wy_division)
        mvar = move_daily.columns[0]
    move_daily.to_csv(f"{site}_move_daily.csv")
    plt.plot(move_daily.index, move_daily[mvar],linestyle="dashed",label="MOVE Data")

plt.ylabel(var)
ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
plt.legend()
plt.savefig(f"{site}_site_daily.jpg",bbox_inches='tight',dpi=300)