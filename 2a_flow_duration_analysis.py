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
from functions import analyze_dur,plot_monthly_dur_ep

### Begin User Input ###
#os.chdir("C://Users//tclarkin//Documents//Projects//El_Vado_Dam//duration_analyses//")

# Site information and user selections
sites = ["ElVado"] # list, site or dam names
analyze = ["annual","monthly","custom"] # list of "annual", "monthly", "custom" or "all"
pcts = standard         # list of fractional exceedance probabilities or standard (no quotes)

# If custcomb == True...define combos: {"Name":[months],etc.}
custcombos = {"February":[2],
              "March":[3],
              "April":[4],
              "Early-Spring Season (Feb-Apr)":[2,3,4],
              "Late-Spring Season (May-Jul)":[5,6,7],
              "Other":[1,8,9,10,11,12]}

### Begin Script ###
# Check for output directory
if not os.path.isdir("duration"):
    os.mkdir("duration")

# Loop through sites
for site in sites:
    # Load data
    data = pd.read_csv(f"{site}_site_daily.csv",parse_dates=True,index_col=0)
    data = data.dropna()

    # Now, conduct duration analyses for selected combinations:
    for a in analyze:
        monthplot = False
        if a =="annual":
            combos = annualcombos
        if a =="monthly":
            combos = monthcombos
            monthplot = True
        if a =="custom":
            combos = custcombos
        if a =="all":
            combos = allcombos

        durtable,durraw = analyze_dur(data,combos,pcts)
        durtable.to_csv(f"duration/{site}_{a}.csv",index=True,header=True)
        if a=="annual":
            durraw[0].to_csv(f"duration/{site}_{a}_raw.csv",index=True,header=True)
        plt.savefig(f"duration/{site}_{a}_plot.jpg",bbox_inches='tight',dpi=300)
        if monthplot == True:
            plot_monthly_dur_ep(durtable,combos)
            plt.savefig(f"duration/{site}_{a}_monthly_plot.jpg",bbox_inches='tight',dpi=300)
