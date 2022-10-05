# -*- coding: utf-8 -*-
"""
Created on Oct 5, 2022
Batch Run of Duration Analyses  (v1)
@author: tclarkin (USBR 2022)

...add description...

"""
import pandas as pd
import subprocess
from src.functions import check_dir

def createclone(script_name,dict):
    # Read script
    with open(script_name,"r") as script:
        script_lines = script.readlines()
    # Create new script
    clone_dir = check_dir("clones")
    with open(f"{clone_dir}/{script_name}","w+") as clone:
        # Find beginning of code:
        for line in script_lines:
            clone.write(line)
            if "### Begin Script ###" in line:
                # cycle through dictionary replacing text in user input
                for d in dict.keys():
                    key = d
                    if isinstance(dict[d],str):
                        setting = f"\"{dict[d]}\""
                    else:
                        setting = dict[d]
                    clone.write(f"{key} = {setting}\n")
    return f"{clone_dir}/{script_name}"

### User Input ###
#os.chdir("")

# Input data file
input_file = 'input_data/test.csv'  # single file with columns for each site OR list of USGS gages and/or site names
wy_division = "WY" # "WY" or "CY"

## Script 1a Settings
script1a = True
script1adict = {"clean":False,    # remove any WYs with less than 300 days of data
                "zero":'average', # minimum flow value or 'average'
                "seasons":{"winter":[1,2,11,12], # False or Dictionary of seasons and months {"name":[months],etc.} or start,stop {"name":[doy,doy]}
                            "spring":[3,4,5,6,7],
                            "summer":[8,9,10],
                           "doy":[30,150]
                           }
                }

## Script 1b WILL BE SKIPPED
script1b = False
## Script 2a Settings
script2a = True
script2adict = {"analyze":["annual","monthly"], # list of "annual", "monthly", "seasons" or "all"
                "wytrace":True} # Boolean to plot wy traces

## Script 2b Settings
script2b = True

## Script 3 WILL BE SKIPPED
script3 = False

## Script 4 Settings
script4 = True
script4dict = {"durations":["peak",1,5,15,30,60,90,120], # Duration in days ("peak" can also be included)
               "plot":True}  # Will plot each WY with all durations

## Script 5 Settings
script5 = True
script5dict = {"idaplot":True,     # Will create initial data analysis plots
                "ppplot":True,      # Will create a plot with all durations plotted with plotting positions (using alpha below)
                "pdfplot":True,      # Plot probability density function of data
                "monthplot":True,    # Plot monthly distribution of annual peaks
                "eventdate":"start"   # When to plot seasonality: "start", "mid", "end", or "max"
                }

### BEGIN SCRIPT ###
# First, check for the type of input_file provided
if isinstance(input_file,list):
    # If we have a list, take the list and make it both the sites (names) and the site_sources
    sites = list()
    for i in input_file:
        # Site names will be the last name, without extension
        sites.append(i.split("/")[len(i.split("/"))-1].split(".")[0])
    site_sources = sites
else:
    # If we have a single file, use the column names as the sites (names) and create site_source files
    input = pd.read_csv(input_file,header=0,index_col=0)
    sites = list(input.columns)
    # Create site_source directory and files
    outdir = check_dir("site_sources")
    site_sources = list()
    for i in input.columns:
        site_source = f"{outdir}/{i}.csv"
        input[i].to_csv(site_source)
        site_sources.append(site_source)


# Second, begin running scripts by creating clones of each and overwriting information in the header
# Script 1a:
if script1a:
    # Add sites and site_sources to script1adict
    script1adict["sites"] = sites
    script1adict["site_sources"] = site_sources
    script1adict["wy_division"] = wy_division

    # Clone script
    clone = createclone("1a_daily_data_prep.py",script1adict)

    # Run clone
    subprocess.call(["python",clone])

# Set seasons for 2a
