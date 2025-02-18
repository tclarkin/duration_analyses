# -*- coding: utf-8 -*-
"""
Created on May 25 2021
Updated on Oct 4, 2022
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
from src.functions import check_dir,get_seasons,get_list
from src.flow_functions import annualcombos, monthcombos, allcombos, standard
from src.flow_functions import analyze_dur, plot_monthly_dur_ep, plot_wytraces, plot_boxplot

### Begin User Input ###
# os.chdir("")

# Site information and user selections
sites = ["choke_scale"]#"frio_derby","frio_tilden","sanmiguel","frio_calliham","choke"] # list, site or dam names
analyze = ["annual", "monthly"]  # list of "annual", "monthly", "seasonal" or "all"
pcts = standard  # list of fractional exceedance probabilities or standard (no quotes)

# Plot water year traces?
wytrace = True
wy_division = "CY"  # "WY" or "CY"
quantiles = [0.05, 0.5, 0.95]  # quantiles to include on plot

# Plot box plots?
boxplot = True

### Begin Script ###
# Loop through sites
for site in sites:
    print(f"Analyzing flow duration for {site}...")

    # Check for output and input directories
    outdir = check_dir(site, "flow")
    indir = f"{site}/data"
    if not os.path.isdir(indir):
        print("Input data directory not found.")

    # Now, conduct duration analyses for selected combinations:
    for a in analyze:
        print(f"Analyzing {a}")
        # Select combos
        if a == "seasonal":
            # Import seasons
            season_df = get_seasons(site)
            seasons = season_df.index.to_list()

            # Loop through seasons
            for season in seasons:
                # Skip annual
                if season=="all":
                    continue
                print(season)
                s = f"_{season}"

                # Load data
                data = pd.read_csv(f"{indir}/{site}{s}_site_daily.csv", parse_dates=True, index_col=0)
                var = data.columns[0]
                data = data.loc[data[var].dropna().index,:]
                decimal = str(data[var].head(1).item()).find('.')

                # Load combos
                combos = dict()
                combos[season] = annualcombos["Annual"]

                # Build duration tables and plot
                durtable, durraw = analyze_dur(data,combos,pcts,var,decimal)
                durraw[0].to_csv(f"{outdir}/{site}{s}_annual_raw.csv", index=True, header=True)
                durtable.to_csv(f"{outdir}/{site}{s}_{a}.csv", index=True, header=True)
                plt.savefig(f"{outdir}/{site}{s}_{a}_plot.jpg", bbox_inches='tight', dpi=300)

                # If selected, plot water year traces
                if wytrace:
                    print("Plotting WY traces")
                    doy_data = plot_wytraces(data,wy_division,quantiles,ax=None)
                    plt.savefig(f"{outdir}/{site}{s}_WY_plot.jpg", bbox_inches="tight", dpi=300)

                    doy_data.to_csv(f"{outdir}/{site}{s}_doy.csv")

                # If selected, plot water year box and whisker plots
                if boxplot:
                    print("Ploting WY box and whisker")
                    plot_boxplot(data, wy_division)
                    plt.savefig(f"{outdir}/{site}{s}_boxplot.jpg", bbox_inches="tight", dpi=300)
        else:
            monthplot = False
            if a == "annual":
                combos = annualcombos
            if a == "monthly":
                combos = monthcombos
                monthplot = True
            if a == "all":
                combos = allcombos
            # Load data
            data = pd.read_csv(f"{indir}/{site}_site_daily.csv", parse_dates=True, index_col=0)
            var = data.columns[0]
            data = data.loc[data[var].dropna().index, :]
            decimal = str(data[var].head(1).item()).find('.')

            # Build duration tables and plot
            durtable, durraw = analyze_dur(data,combos,pcts,var,decimal)
            durtable.to_csv(f"{outdir}/{site}_{a}.csv", index=True, header=True)
            if a == "annual":
                durraw[0].to_csv(f"{outdir}/{site}_{a}_raw.csv", index=True, header=True)
            plt.savefig(f"{outdir}/{site}_{a}_plot.jpg", bbox_inches='tight', dpi=300)
            if monthplot == True:
                plot_monthly_dur_ep(durtable, combos, var)
                plt.savefig(f"{outdir}/{site}_{a}_monthly_plot.jpg", bbox_inches='tight', dpi=300)

        # If selected, plot water year traces
        if wytrace and a == "annual" :
            print("Plotting WY traces")
            doy_data = plot_wytraces(data,wy_division,quantiles,ax=None)
            plt.savefig(f"{outdir}/{site}_WY_plot.jpg", bbox_inches="tight", dpi=300)

            doy_data.to_csv(f"{outdir}/{site}_doy.csv")

        # If selected, plot water year box and whisker plots
        if boxplot and a == "annual":
            print("Ploting WY box and whisker")
            plot_boxplot(data, wy_division)
            plt.savefig(f"{outdir}/{site}_boxplot.jpg", bbox_inches="tight", dpi=300)

print("Script 2a Complete")