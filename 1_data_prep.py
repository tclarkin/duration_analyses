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
from functions import nwis_import,csv_import

### User Input ###
#os.chdir("C://Users//tclarkin//Documents//Projects//El_Vado_Dam//duration_analyses//")

# Site information and user selections
site = 'ElVado_SWE'  # site or dam name
wy_division = "WY" # "WY" or "CY"
site_source = "file" # "usgs" or "file"
site_file = "431.csv" # usgs site number (e.g., "09445000") or .csv data file
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
        site_data = nwis_import(site=site_file,dtype="dv",wy=wy_division)
        var = "flow"
else:
    site_data = csv_import(site_file,wy=wy_division)
    var = site_data.columns[0]

if clean:
    # Remove negative values
    site_data.loc[site_data[var] < 0, var] = 0

    # Remove WYs with less than 300 days of data or if last month is lower than September
    for wy in site_data["wy"].unique():
        if pd.isna(site_data.loc[site_data["wy"] == wy, var]).sum() > 65:
            site_data.loc[site_data["wy"] == wy, var] = np.nan
        if site_data.loc[site_data["wy"]==wy].tail(1).month.item()<9:
            site_data.loc[site_data["wy"] == wy, var] = np.nan

site_data.to_csv(f"{site}_site_data.csv")
fig, ax = plt.subplots(figsize=(6.25, 4))
plt.plot(site_data.index,site_data[var],label="Site Data")

# Deregulate (if applicable)
if deregulate:
    if dereg_source == "usgs":
        if len(dereg_file) != 8:
            print("Must provide valid USGS site number (8-digit string) for dereg data")
        else:
            dereg_data = nwis_import(site=dereg_file,dtype="dv",wy=wy_division)
    else:
        dereg_data = flowcsv_import(dereg_file, wy=wy_division)

    if "dereg_data" is not None:
        if sign == "plus":
            site_dereg = site_data[var] + dereg_data[var]
        if sign == "minus":
            site_dereg = site_data[var] - dereg_data[var]
        site_dereg.loc[site_dereg[var]<0,var] = 0
        site_data[var] = site_dereg
        site_data = site_data.dropna()
    else:
        print("Failed to deregulate.")
    site_data.to_csv(f"{site}_site_data.csv")
    plt.plot(site_data.index, site_data[var],label="Dereg Site Data")

# MOVE (if applicable)
if move:
    if move_source == "usgs":
        if len(move_file) != 8:
            print("Must provide valid USGS site number (8-digit string) for at-site data")
        else:
            move_data = nwis_import(site=move_file, dtype="dv", wy=wy_division)
    else:
        move_data = flowcsv_import(move_file,wy=wy_division)
    move_data.to_csv(f"{site}_move_data.csv")
    plt.plot(site_data.index, site_data[var],linestyle="dashed",label="MOVE Data")

plt.ylabel(var)
ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
plt.savefig(f"{site}_site_data.jpg",bbox_inches='tight',dpi=300)