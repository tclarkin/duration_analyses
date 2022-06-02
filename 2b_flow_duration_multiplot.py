# -*- coding: utf-8 -*-
"""
Created on June 04 2021
Flow Duration Multiplot  (v1)
@author: tclarkin (USBR 2021)

This script allows the user to plot multiple annual duration curves
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from functions import plot_dur_ep,get_varlabel,standard,interp

### Begin User Input ###
#os.chdir("")

# Site information and user selections
sites = ["example15","example15_ext"] # list, site or dam names
labels = ["Flow (at-site)","Flow (downstream)"] # labels for sites
map = True # map flows from one curve to another

### Begin Script ###
# Check for output directory
if not os.path.isdir("flow"):
    print("duration directory does not exist. Please run 2a_flow_duration_analysis.py before using this script.")

# Initiate plot
plot_dur_ep()

# Loop through sites
var = None
for site,label in zip(sites,labels):
    data = pd.read_csv(f"flow/{site}_annual_raw.csv",parse_dates=True,index_col=0)
    if var is None:
        var = data.columns[1]
        var_label = get_varlabel(var)
    else:
        if data.columns[1]!=var:
            var = data.columns[1]
            var_label = f"{var_label} | {get_varlabel(var)}"
    plt.plot(data.exceeded*100,data[var],label=label)
plt.ylabel(var_label)
plt.legend()
plt.savefig(f"flow/all_annual_multiplot.jpg",bbox_inches='tight',dpi=600)

# Combined table
all_data = pd.DataFrame(index=standard)
for site in sites:
    data = pd.read_csv(f"flow/{site}_annual.csv",parse_dates=True,index_col=0)
    all_data.loc[:,site] = data["Annual"]
all_data.to_csv(f"flow/{site}_allplot_combine.csv")

# Map flows
for site in sites:
    site_data = pd.read_csv(f"data/{site}_site_daily.csv", parse_dates=True, index_col=0)
    var = site_data.columns[0]

    fig, ax = plt.subplots(figsize=(6.25, 4))
    plt.ylabel(get_varlabel(var))
    ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
    plt.plot(site_data[var],color="blue", label=f"{site} Data")
    for alt in sites:
        if alt==site:
            continue
        else:
            alt_data = pd.read_csv(f"data/{alt}_site_daily.csv", parse_dates=True, index_col=0)
            alt_var = alt_data.columns[0]
            plt.plot(alt_data[alt_var],label=f"{alt} data")

            ext_data = alt_data.copy()
            for d in alt_data.index:
                ext_data.loc[d,alt_var] = interp(alt_data.loc[d,alt_var],all_data.loc[:,alt].values,all_data.loc[:,site].values)
            plt.plot(ext_data[alt_var],linestyle="dashed",color="blue",label=f"{site} Mapped Data")

