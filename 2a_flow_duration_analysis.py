# -*- coding: utf-8 -*-
"""
Created on May 25 2021
Flow Duration Script  (v2)
@author: tclarkin (USBR 2021)

This script takes a user supplied daily inflows and user specified seasons and conducts a flow duration analysis,
exporting tables and figures. Uses the equation:
    
    EP = M/(n1 +1)
    
where M is the rank of a flow and n1 is the total number of observations.

This script can be run for all sites simultaneously
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
from functions import annualcombos,monthcombos,allcombos,standard
from functions import analyze_flowdur,plot_monthlyflowdur

### Begin User Input ###
#os.chdir("C://Users//tclarkin//Documents//Projects//Anderson_Ranch_Dam//duration_analyses//")

# Site information and user selections
sites = ["ARD","ARD_USGS"] # list, site or dam names
analyze = ["annual","monthly","custom"] # list of "annual", "monthly", "custom" or "all"
pcts = standard         # list of fractional exceedance probabilities or standard (no quotes)

# If custcomb == True...define combos: {"Name":[months],etc.}
custcombos = {"Winter Season (Nov-Jan)":[1,11,12],
              "Spring Season (Feb-Jun)":[2,3,4,5,6],
              "Late-Summer Season (Jul-Sep)":[7,8,9]}

### Begin Script ###
# Check for output directory
if not os.path.isdir("flow"):
    os.mkdir("flow")

# Loop through sites
for site in sites:
    # Load inflows
    data = pd.read_csv(f"{site}_site_data.csv",parse_dates=True,index_col=0)
    data = data.dropna() # Drop any missing flows

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

        flowdurtable,flowdurraw = analyze_flowdur(data,combos,pcts)
        flowdurtable.to_csv(f"flow/{site}_{a}.csv",index=True,header=True)
        if a=="annual":
            flowdurraw[0].to_csv(f"flow/{site}_{a}_raw.csv",index=True,header=True)
        plt.savefig(f"flow/{site}_{a}_plot.jpg",bbox_inches='tight',dpi=300)
        if monthplot == True:
            plot_monthlyflowdur(flowdurtable,combos)
            plt.savefig(f"flow/{site}_{a}_monthly_plot.jpg",bbox_inches='tight',dpi=300)
