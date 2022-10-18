# -*- coding: utf-8 -*-
"""
Created on June 04 2021
Updated on Oct 4, 2022
Flow Duration Multiplot  (v1)
@author: tclarkin (USBR 2021)

This script allows the user to plot multiple annual duration curves
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from src.functions import get_varlabel,check_dir
from src.flow_functions import plot_dur_ep,standard,plot_wytraces,plot_boxplot

### Begin User Input ###
#os.chdir("")

# Site information and user selections
sites = ["UNREGelephant","REGelephant","UNREGembudo","REGembudo"] # list, site or dam names
labels = ["Elephant Butte","Elephant Butte Reg","Yes","No"] # labels for sites

# Plot water year traces?
wytrace = True
wy_division = "WY" # "WY" or "CY"
quantiles = [0.05,0.5,0.95] # quantiles to include on plot

# Plot box plots?
boxplot = True

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
    print(f"Adding {site} to flow duration multiplot...")

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
plt.savefig(f"{outdir}/{site}_all_annual_multiplot.jpg",bbox_inches='tight',dpi=300)

# Combined table
all_data = pd.DataFrame(index=standard)
for site in sites:
    print(site)

    data = pd.read_csv(f"{site}/flow/{site}_annual.csv",parse_dates=True,index_col=0)
    all_data.loc[:,site] = data["Annual"]
all_data.to_csv(f"{outdir}/{site}_allplot_combine.csv")

#
if wytrace or boxplot:
    # determine number of subplots
    nplot = len(sites)
    ncol = int(min([max([1,np.floor(nplot/2)]),3]))
    nrow = int(np.ceil(nplot/ncol))

# If selected, plot wy traces onto same panel
if wytrace:
    fig,axs = plt.subplots(nrow,ncol,sharex=True,sharey=True,figsize=(3*ncol, 3*nrow))

    for n,site in enumerate(sites):
        ax = plt.subplot(nrow,ncol,n+1)
        indir = f"{site}/data"
        data = pd.read_csv(f"{indir}/{site}_site_daily.csv",parse_dates=True,index_col=0)
        data = data.dropna()
        ax = plot_wytraces(data,wy_division,quantiles,ax=ax,legend=False)
        plt.annotate(f"({n+1}) {site} ({data.index.year.min()}-{data.index.year.max()})", xy=(0, 1.01),
                     xycoords=ax.get_xaxis_transform())

    plt.gca().set_ylim(bottom=0)
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width, box.height])
    plt.legend(bbox_to_anchor=(0, -box.height*0.5), loc='upper center', prop={'size': 10},ncol=2)
    plt.savefig(f"{outdir}/{site}_all_wy_plots.jpg", bbox_inches="tight", dpi=600)

# If selected, plot box plots onto same panel
if boxplot:
    fig,axs = plt.subplots(nrow,ncol,sharex=True,sharey=True,figsize=(3*ncol, 3*nrow))

    for n,site in enumerate(sites):
        ax = plt.subplot(nrow,ncol,n+1)
        indir = f"{site}/data"
        data = pd.read_csv(f"{indir}/{site}_site_daily.csv",parse_dates=True,index_col=0)
        data = data.dropna()
        plot_boxplot(data,wy_division,ax=ax,legend=False)
        plt.annotate(f"({n+1}) {site} ({data.index.year.min()}-{data.index.year.max()})", xy=(0, 1.01),
                     xycoords=ax.get_xaxis_transform())

    plt.savefig(f"{outdir}/{site}_all_boxplot.jpg", bbox_inches="tight", dpi=600)
