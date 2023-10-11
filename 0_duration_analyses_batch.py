# -*- coding: utf-8 -*-
"""
Created on Oct 5, 2022
Batch Run of Duration Analyses  (v1)
@author: tclarkin (USBR 2022)

...add description...

"""
import subprocess
from src.functions import getsites,createclone

### User Input ###
#os.chdir("")

# Input data file
wy_division = "WY" # "WY" or "CY"

## Script 1a Settings
script1a = True
script1a_input_file = "input_data/gage_unreg.csv"  # single file with columns for each site OR list of USGS gages and/or site names
script1a_dict = {"clean":False,    # remove any WYs with less than 300 days of data
                "zero":'average', # minimum flow value or 'average'
                "seasons": {"spring":[45,196]}}# # False or Dictionary of seasons and months {"name":[months],etc.} or start,stop {"name":[doy,doy]}

## Script 1b Settings
script1b = False
script1b_input_file = ["10139500"] # single file with columns for each site OR list of USGS gages and/or site names

## Script 2a Settings
script2a = False
script2a_dict = {"analyze":["annual","monthly"], # list of "annual", "monthly", "seasons" or "all"
                "wytrace":False, # Boolean to plot wy traces
                "boxplot":False} # Boolean to plot boxplot

## Script 2b Settings
script2b = False
script2b_dict = {"wytrace":True, # Boolean to plot wy traces
                 "boxplot":True, # Boolean to plot boxplot
                 "ylabel":"Flow (ft$^3$/s)", # If str, single ylabel, if list, will assign to each row
                 "outliers":False, # Boolean to show outliers in boxplot
                 "sharey":True} # Boolean to use shared y axis

## Script 3 WILL BE SKIPPED
script3 = False

## Script 4 Settings
script4 = True
script4_dict = {"durations":[90], # Duration in days ("peak" can also be included)
               "plot":True,  # Will plot each WY with all durations
               "concat":True} # Create concat table of all durations and locations

## Script 5 Settings
script5 = True
script5_dict = {"idaplot":True,     # Will create initial data analysis plots
                "ppplot":True,      # Will create a plot with all durations plotted with plotting positions (using alpha below)
                "pdfplot":False,      # Plot probability density function of data
                "monthplot":False,    # Plot monthly distribution of annual peaks
                "eventdate":"start"   # When to plot seasonality: "start", "mid", "end", or "max"
                }

### BEGIN SCRIPT ###
# Second, begin running scripts by creating clones of each and overwriting information in the header
# Script 1a:
# Identify sites and site_sources
sites, site_sources = getsites(script1a_input_file)

if script1a:
    # Add sites and site_sources to script1a_dict
    script1a_dict["sites"] = sites
    script1a_dict["site_sources"] = site_sources
    script1a_dict["wy_division"] = wy_division

    # Clone script
    clone1a = createclone("1a_daily_data_prep.py",script1a_dict)

    # Run clone
    subprocess.call(["python",clone1a])

# Script 1b
if script1b:
    # Identify sites and site_sources
    peak_sites,peak_site_sources = getsites(script1b_input_file)

    # Compare lists:
    if peak_sites != sites:
        print("Peak Sites and Daily Sites are not the same...")
        if len(peak_sites) == len(sites):
            print("Lists have same length; script will continue using daily data site names.")
            peak_sites_sel = sites
        else:
            print("Lists have different lengths; script will continue using peak data site names.")
            peak_sites_sel = peak_sites
    else:
        peak_sites_sel = peak_sites

    # Add sites, site_sources, wy_division, and seasons to script1b_dict
    script1b_dict = dict()
    script1b_dict["sites"] = peak_sites_sel
    script1b_dict["site_sources"] = peak_site_sources
    script1b_dict["wy_division"] = wy_division
    script1b_dict["seasons"] = script1a_dict["seasons"]

    # Clone script
    clone1b = createclone("1b_peak_data_prep.py",script1b_dict)

    # Run clone
    subprocess.call(["python",clone1b])

# Script 2a
if script2a:
    # Add sites, wy_division, and seasons to script2a_dict
    script2a_dict["sites"] = sites
    script2a_dict["wy_division"] = wy_division
    if isinstance(script1a_dict["seasons"],bool)==False:
        if all(script1a_dict["seasons"]):
            script2a_dict["seasons"] = list(script1a_dict["seasons"].keys())
    else:
        script2a_dict["seasons"] = [None]

    # Clone script
    clone2a = createclone("2a_flow_duration_analysis.py",script2a_dict)

    # Run clone
    subprocess.call(["python",clone2a])

# Script 2b
if script2b:
    # Add sites and labels (sites) to script2b_dict
    script2b_dict["sites"] = sites
    script2b_dict["labels"] = sites

    # Clone script
    clone2b = createclone("2b_flow_duration_multiplot.py", script2b_dict)

    # Run clone
    subprocess.call(["python", clone2b])

# Script 3
if script3:
    print("Script 3 not setup to run in batch. Skipping...")

# Script 4
if script4:
    # Add sites, wy_division, and seasons to script4_dict
    script4_dict["sites"] = sites
    script4_dict["wy_division"] = wy_division
    if isinstance(script1a_dict["seasons"],bool)==False:
        if all(script1a_dict["seasons"]):
            script4_dict["seasons"] = script1a_dict["seasons"]
    else:
        script4_dict["seasons"] = [None]

    # Clone script
    clone4 = createclone("4_volume_duration_analysis.py", script4_dict)

    # Run clone
    subprocess.call(["python", clone4])

# Script 5
if script5:
    # Add sites, wy_division, durations, and seasons to script4_dict
    script5_dict["sites"] = sites
    script5_dict["wy_division"] = wy_division
    script5_dict["durations"] = script4_dict["durations"]
    if isinstance(script1a_dict["seasons"],bool)==False:
        if all(script1a_dict["seasons"]):
            script5_dict["seasons"] = list(script1a_dict["seasons"].keys())
    else:
        script5_dict["seasons"] = [None]

    # Clone script
    clone5 = createclone("5_multiplot.py", script5_dict)

    # Run clone
    subprocess.call(["python", clone5])
