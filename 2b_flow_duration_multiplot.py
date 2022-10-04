# -*- coding: utf-8 -*-
"""
Created on June 04 2021
Updated on Oct 4, 2022
Flow Duration Multiplot  (v1)
@author: tclarkin (USBR 2021)

This script allows the user to plot multiple annual duration curves
"""

import pandas as pd
import matplotlib.pyplot as plt
from src.functions import get_varlabel,check_dir
from src.flow_functions import plot_dur_ep,standard

### Begin User Input ###
#os.chdir("")

# Site information and user selections
sites = ["UNREGelephant","UNREGembudo"] # list, site or dam names
labels = ["Elephant Butte","Embudo"] # labels for sites

### Begin Script ###
# Check for output directory
for site in sites:
    sitedir = check_dir(site,"flow")
outdir = check_dir("flow_comparison")

# Initiate plot
plot_dur_ep()

# Loop through sites
var = None
for site,label in zip(sites,labels):
    data = pd.read_csv(f"{site}/flow/{site}_annual_raw.csv",parse_dates=True,index_col=0)
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
plt.savefig(f"{outdir}/all_annual_multiplot.jpg",bbox_inches='tight',dpi=300)

# Combined table
all_data = pd.DataFrame(index=standard)
for site in sites:
    data = pd.read_csv(f"{site}/flow/{site}_annual.csv",parse_dates=True,index_col=0)
    all_data.loc[:,site] = data["Annual"]
all_data.to_csv(f"{outdir}/{site}_allplot_combine.csv")
