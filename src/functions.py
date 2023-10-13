# -*- coding: utf-8 -*-
"""
Duration Analyses Functions
@author: tclarkin (USBR 2021)

This script contains all of the functions and pre-defined variables used in the duration analyses

"""
import os
import dataretrieval.nwis as nwis
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import probscale
import datetime as dt
from scipy.stats import mannwhitneyu
from scipy.stats import kendalltau
from scipy.stats.mstats import theilslopes
from scipy.stats import norm

def getsites(input_file):
    # First, check for the type of input_file provided
    if isinstance(input_file, list):
        # If we have a list, take the list and make it both the sites (names) and the site_sources
        sites = list()
        for i in input_file:
            if isinstance(i,list):
                sites.append(i[0])
            else:
                # Site names will be the last name, without extension
                sites.append(i.split("/")[len(i.split("/")) - 1].split(".")[0])
        site_sources = input_file
    elif "csv" in input_file:
        # If we have a single file, use the column names as the sites (names) and create site_source files
        input = pd.read_csv(input_file, header=0, index_col=0)
        sites = list(input.columns)
        # Create site_source directory and files
        outdir = check_dir("site_sources")
        site_sources = list()
        for i in input.columns:
            site_source = f"{outdir}/{i}.csv"
            input[i].to_csv(site_source)
            site_sources.append(site_source)
    else:
        sites = site_sources = [input_file]

    return sites,site_sources

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

def save_seasons(site,seasons):
    """

    :param site: site name
    :param seasons: either dictionary of seasons or dataframe from existing seasons file
    :return:
    """
    if isinstance(seasons,pd.DataFrame):
        seasons.to_csv(f"{site}/{site}_seasons.csv")
        print(f"Season list saved to {site}/{site}_seasons.csv")
    else:
        season_df = pd.DataFrame()
        season_df.loc["all","define"] = str([1,2,3,4,5,6,7,8,9,10,11,12])

        if isinstance(seasons,bool)==False:
            if all(seasons):
                for s in seasons.keys():
                    season_df.loc[s,"define"] = str(seasons[s])
        season_df.to_csv(f"{site}/{site}_seasons.csv")
        print(f"Season list saved to {site}/{site}_seasons.csv")

def get_seasons(site):
    season_df = pd.read_csv(f"{site}/{site}_seasons.csv",index_col=0)
    return season_df

def get_list(season_str):
    print(season_str)
    if season_str is None or pd.isna(season_str):
        return None
    season_str_clean = season_str.strip("[").strip("]").replace(" ","")
    season_list = list()
    for s in season_str_clean.split(","):
        if s.isdigit():
            season_list.append(int(s))
        else:
            season_list.append(s.strip("'"))

    return season_list

def check_dir(dir,sub=False):
    """
    Function to check for and create directory
    :param dir: str, directory to be created
    :param sub: str, sub directory to be created
    :return: str, directory
    """
    if not os.path.isdir(dir):
        os.mkdir(dir)
    if sub!=False:
        outdir = f"{dir}/{sub}"
        if not os.path.isdir(outdir):
            os.mkdir(outdir)
    else:
        outdir = dir
    return outdir

def get_varlabel(var):
    """
    Function to create figure label
    :param var: str or df, if df, will infer var from  column 0
    :return: str, figure label
    """
    if isinstance(var,str)==False:
        var = var.columns[0]

    if var in ["flow","Flow","discharge","Discharge","inflow","Inflow","IN","Q","QU","cfs","CFS"]:
        lab = "Flow (ft$^3$/s)"
    elif var in ["peak", "Peak", "peaks", "Peaks","peak discharge","Peak Discharge"]:
        lab = "Peak Flow (ft$^3$/s)"
    elif var in ["stage","Stage","feet","Feet","FT","ft","pool_elevation","elevation","Elevation","elev","Elev"]:
        lab = "Stage (ft)"
    elif var in ["SWE","swe","snowpack","snowdepth","snow","SNWD","WTEQ"]:
        lab = "SWE (in)"
    elif var in ["P","Precip","Rainfall","rainfall","precip","precipitation","Precipitation","PRCP","PREC"]:
        lab = "Precip. (in)"
    else:
        lab = var

    return lab

def simple_plot(data,data_label="",marker=None):
    fig, ax = plt.subplots(figsize=(6.25, 4))
    plt.ylabel(get_varlabel(data))
    ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
    if data.columns[0]=="date":
        idx = 1
    else:
        idx = 0
    if marker is None:
        plt.plot(data.index,data.iloc[:,idx],label=data_label)
    else:
        plt.plot(data.index,data.iloc[:,idx],marker=marker,linewidth=0,label=data_label)

    if "Stage" not in get_varlabel(data):
        ax.set_ylim([0, None])

def interp(x,knownxs,knownys,round=0,verbose=False):
    """
    Interpolation function; if requested value is outside of x range, set to min or max x.
    :param x: float, independent variable value of interest
    :param knownxs: array, known independent variable values
    :param knownys: array, known dependent variable values
    :param round: int, number of decimals to round
    :param verbose: boolean, include printed statements
    :return: float, dependent variable value of interest
    """
    # Convert to arrays
    knownxs = np.array(knownxs)
    knownys = np.array(knownys)

    # Check if x is one of the known xs
    if x in knownxs:
        y = knownys[knownxs==x]
    elif x < knownxs.min():
        # If x is below min known x, set to min known x
        y = knownys[knownxs==knownxs.min()]
        if verbose:
            print("Warning!! Interpolation outside of known values--set to minumum.")
    elif x > knownxs.max():
        # If x is above max known x, set to max known x
        y = knownys[knownxs == knownxs.max()]
        if verbose:
            print("Warning!! Interpolation outside of known values--set to maximum.")
    else:
        # Calculate interpolated value
        relxs = knownxs-x
        lowx_idx = relxs[relxs<0].argmax()
        hix_idx = lowx_idx+1
        lowx = knownxs[lowx_idx].item()
        lowy = knownys[lowx_idx].item()
        hix = knownxs[hix_idx].item()
        hiy = knownys[hix_idx].item()

        y = np.round(lowy + (x-lowx)*(hiy-lowy)/(hix-lowx),round)

    return y.item()
