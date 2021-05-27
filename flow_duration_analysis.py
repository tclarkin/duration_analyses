# -*- coding: utf-8 -*-
"""
Created on May 25 2021
Flow Duration Script  (v2)
@author: tclarkin (USBR 2021)

This script takes a user supplied daily inflows and user specified seasons and conducts a flow duration analysis,
exporting tables and figures. Uses the equation:
    
    EP = M/n1
    
where M is the rank of a flow and n1 is the total number of observations.

The user must:
    - Identify the current directory
    - Provide the site name (site)
    - select combiniations of months to analyze
    - Specify exceedence probabilities (pcts) desired, if not standard 23

"""

import os
import pandas as pd
import matplotlib.pyplot as plt
from functions import annualcombos,monthcombos,allcombos,standard
from functions import analyze_flowdur,plot_monthlyflowdur

### Begin User Input ###
os.chdir("C://Users//tclarkin//Documents//Projects//Roosevelt_Dam_IE//duration_analyses//")

# Site information and user selections
site = "TRD" # site or dam name
analyze = ["annual","monthly","custom"] # list of "annual", "monthly", "custom" or "all"
pcts = standard         # list of fractional exceedance probabilities or standard (no quotes)

# If custcomb == True...define combos: {"Name":[months],etc.}
custcombos = {"Flood Season (Dec-Apr)":[1,2,3,4,12],
              "Non-Flood Season (May-Nov)":[5,6,7,8,9,10,11]}

### Begin Script ###
# Load inflows
data = pd.read_csv(f"{site}_site_data.csv",parse_dates=True,index_col=0)

# Check for output directory
if not os.path.isdir("flow"):
    os.mkdir("flow")

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

    flowdurtable = analyze_flowdur(data,combos,pcts)
    flowdurtable.to_csv(f"flow/{site}_{a}.csv",index=True,header=True)
    plt.savefig(f"flow/{site}_{a}_plot.jpg".format(site),bbox_inches='tight',dpi=300)
    if monthplot == True:
        plot_monthlyflowdur(flowdurtable,combos)
        plt.savefig(f"flow/{site}_{a}_monthly_plot.jpg".format(site),bbox_inches='tight',dpi=300)
