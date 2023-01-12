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
from src.flow_functions import plot_dur_ep,standard,plot_wytraces,plot_boxplot,alphabet
from src.data_functions import summarize_daily

### Begin User Input ###
#os.chdir("")

# Site information and user selections
sites = ['unreg08279500','unreg08290000','unreg08313000','unreg08319000','unreg08358400']
labels = ['Embudo (site 1)', 'Chamita (site 3)','Otowi (site 4)','San Felipe (site 5)','San Marcial (site 9)']
ylabel = "Flow (ft$^3$/s)"
colors = ["red","grey","goldenrod","lime","purple"]
linestyles = ["dashed","dotted","solid","dashdot","dashed"]

# Plot water year traces?
wytrace = False
wy_division = "WY" # "WY" or "CY"
quantiles = [0.05,0.5,0.95] # quantiles to include on plot
sharey = False

# Plot box plots?
boxplot = False
outliers = True

# Summary table?
summarize = True

### Begin Script ###
# Check for output directory
for site in sites:
    sitedir = check_dir(site,"flow")
outdir = check_dir("flow_comparison")

# Initiate plot
plot_dur_ep()

# Loop through sites
var = None
for n,site,label in zip(range(0,len(sites)),sites,labels):
    print(f"{n} Adding {site} to flow duration multiplot...")

    data = pd.read_csv(f"{site}/flow/{site}_annual_raw.csv",parse_dates=True,index_col=0)
    if var is None and ylabel is None:
        var = data.columns[1]
        var_label = get_varlabel(var)
    elif ylabel is not None:
        var = data.columns[1]
        if isinstance(ylabel,list):
            var_label = ylabel[n]
        else:
            var_label = ylabel
    else:
        if data.columns[1]!=var:
            var = data.columns[1]
            var_label = f"{var_label} | {get_varlabel(var)}"
    plt.plot(data.exceeded*100,data[var],color=colors[n],linestyle=linestyles[n],label=label)
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
    ncol = int(min([max([1,np.floor(nplot/3)]),2]))
    nrow = int(np.ceil(nplot/ncol))

# If selected, plot wy traces onto same panel
if wytrace:

    fig,axs = plt.subplots(nrow,ncol,sharex=True,sharey=sharey,figsize=(6.25, 2*nrow),squeeze=False)

    if sharey:
        ylim = [10000,1]

    for n,site in enumerate(sites):
        ax = plt.subplot(nrow,ncol,n+1)
        indir = f"{site}/data"
        data = pd.read_csv(f"{indir}/{site}_site_daily.csv",parse_dates=True,index_col=0)
        data = data.dropna()
        ax = plot_wytraces(data,wy_division,quantiles,ax=ax,legend=False)
        plt.annotate(f"({alphabet[n]}) {labels[n]} ({data.index.year.min()}-{data.index.year.max()})", xy=(0, 1.01),
                     xycoords=ax.get_xaxis_transform())
        if sharey:
            ylim[0] = min([ylim[0],10**np.floor(np.log10(max([1,data.iloc[:,0].min()])))])
            ylim[1] = max([ylim[1],10**np.ceil(np.log10(data.iloc[:,0].max()))])

    if sharey:
        for n,site in enumerate(sites):
            ax = plt.subplot(nrow, ncol, n + 1)
            ax.set_ylim(ylim)

    # Add legend
    if n+1==nrow*ncol:
        plt.legend(loc="upper center",bbox_to_anchor=(0.5,-0.2),prop={'size': 8},ncol=2)
    else:
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width, box.height])
        plt.legend(bbox_to_anchor=(1+box.width,1-box.height), loc='center left', prop={'size': 10},ncol=2)
        # Remove blanks
        while n+1 < nrow*ncol:
            n += 1
            ax = plt.subplot(nrow,ncol,n+1)
            ax.set_visible(False)

    # Add row labels:
    if isinstance(ylabel,list):
        for ax,lab in zip(axs[:, 0],ylabel):
            ax.set_ylabel(lab, rotation=90, size='large')
    else:
        fig.text(0, 0.5,ylabel, va='center', rotation='vertical')

    plt.savefig(f"{outdir}/{site}_all_wy_plots.jpg", bbox_inches="tight", dpi=600)


# If selected, plot box plots onto same panel
if boxplot:
    fig,axs = plt.subplots(nrow,ncol,sharex=True,sharey=sharey,figsize=(6.25, 2*nrow),squeeze=False)

    for n,site in enumerate(sites):
        ax = plt.subplot(nrow,ncol,n+1)
        indir = f"{site}/data"
        data = pd.read_csv(f"{indir}/{site}_site_daily.csv",parse_dates=True,index_col=0)
        data = data.dropna()
        plot_boxplot(data,wy_division,outliers,ax=ax,legend=False)
        plt.annotate(f"({alphabet[n]}) {labels[n]} ({data.index.year.min()}-{data.index.year.max()})", xy=(0, 1.01),
                     xycoords=ax.get_xaxis_transform())

    # Remove blanks
    while n+1 < nrow*ncol:
        n += 1
        ax = plt.subplot(nrow,ncol,n+1)
        ax.set_visible(False)

    # Add row labels:
    if isinstance(ylabel,list):
        for ax,lab in zip(axs[:, 0],ylabel):
            ax.set_ylabel(lab, rotation=90, size='large')
    else:
        fig.text(0, 0.5,ylabel, va='center', rotation='vertical')

    plt.savefig(f"{outdir}/{site}_all_boxplot.jpg", bbox_inches="tight", dpi=600)

if summarize:
    summary_df = pd.DataFrame()
    for n,site in enumerate(sites):
        indir = f"{site}/data"
        data = pd.read_csv(f"{indir}/{site}_site_daily.csv",parse_dates=True,index_col=0)
        data = data.dropna()
        data_summary = summarize_daily(data)
        summary_df[site] = data_summary.loc["all",:]

    summary_df.to_csv(f"{outdir}/{site}_all_summaries.csv")