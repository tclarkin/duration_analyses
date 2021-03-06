# -*- coding: utf-8 -*-
"""
Created on May 25 2021
Duration Script  (v2)
@author: tclarkin (USBR 2021)

This script takes a user supplied daily data and user specified seasons and conducts a duration analysis,
exporting tables and figures. Uses the equation:
    
    EP = M/(n1 +1)
    
where M is the rank of a value and n1 is the total number of observations.

This script can be run for all sites simultaneously
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
from functions import annualcombos,monthcombos,allcombos,standard
from functions import analyze_dur,plot_monthly_dur_ep,plot_wytraces

### Begin User Input ###
#os.chdir("")

# Site information and user selections
sites = ["sanmarc_unreg"] # list, site or dam names
analyze = ["annual","monthly","season"] # list of "annual", "monthly", "season" or "all"
pcts = standard         # list of fractional exceedance probabilities or standard (no quotes)

# If season == True...define combos: {"Name":[months],etc.}
seasons = {"winter":[1,2,11,12],
            "spring":[3,4,5,6,7],
            "summer":[8,9,10]}

# Plot water year traces?
wytrace = True
wy_division = "WY" # "WY" or "CY"
quantiles = [0.05,0.5,0.95] # quantiles to include on plot

### Begin Script ###
# Check for output directory
if not os.path.isdir("flow"):
    os.mkdir("flow")

# Loop through sites
for site in sites:
    # Load data
    data = pd.read_csv(f"data/{site}_site_daily.csv",parse_dates=True,index_col=0)
    data = data.dropna()
    var = data.columns[0]

    # Now, conduct duration analyses for selected combinations:
    for a in analyze:
        monthplot = False
        if a =="annual":
            combos = annualcombos
        if a =="monthly":
            combos = monthcombos
            monthplot = True
        if a =="season":
            combos = seasons
        if a =="all":
            combos = allcombos

        durtable,durraw = analyze_dur(data,combos,pcts,var)
        durtable.to_csv(f"flow/{site}_{a}.csv",index=True,header=True)
        if a=="annual":
            durraw[0].to_csv(f"flow/{site}_{a}_raw.csv",index=True,header=True)
        plt.savefig(f"flow/{site}_{a}_plot.jpg",bbox_inches='tight',dpi=600)
        if monthplot == True:
            plot_monthly_dur_ep(durtable,combos,var)
            plt.savefig(f"flow/{site}_{a}_monthly_plot.jpg",bbox_inches='tight',dpi=600)

# If selected, plot water year traces
if wytrace:
    print("Plotting WY traces")
    doy_data = plot_wytraces(data, wy_division,quantiles)
    plt.savefig(f"flow/{site}_WY_plot.jpg", bbox_inches="tight", dpi=600)

    doy_data.to_csv(f"flow/{site}_doy.csv")