# -*- coding: utf-8 -*-
"""
Created on June 04 2021
Flow Duration Multiplot  (v1)
@author: tclarkin (USBR 2021)

This script allows the user to plot multiple annual flow duration curves
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
from functions import plot_flowdur

### Begin User Input ###
#os.chdir("C://Users//tclarkin//Documents//Projects//Anderson_Ranch_Dam//duration_analyses//")

# Site information and user selections
sites = ["ARD","ARD_USGS"] # list, site or dam names
labels = ["Hydromet","USGS"] # labels for sites

### Begin Script ###
# Check for output directory
if not os.path.isdir("flow"):
    print("flow directory does not exist. Please run 2a_flow_duration_analysis.py before using this script.")

# Initiate plot
plot_flowdur()

# Loop through sites
for site,label in zip(sites,labels):
    data = pd.read_csv(f"flow/{site}_annual_raw.csv",parse_dates=True,index_col=0)
    plt.plot(data.exceeded*100,data.flow,label=label)
    plt.legend()
plt.savefig(f"flow/all_annual_multiplot.jpg",bbox_inches='tight',dpi=300)
