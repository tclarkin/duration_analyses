# -*- coding: utf-8 -*-
"""
### VOLUME FUNCTIONS ###
@author: tclarkin (USBR 2021)

This script contains the volume analysis functions and pre-defined variables used in the duration analyses 4

"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import datetime as dt
from src.functions import get_varlabel

### VOLUME DURATION FUNCTIONS
def cfs2af(cfs):
    af = cfs * 86400 / 43560
    return af

def af2cfs(af):
    cfs = af / (86400 / 43560)
    return cfs

def analyze_voldur(data,dur,decimal):
    """
    This function calculates a rolling mean and then identifies the ann. max. for each WY
    :param data: df, data including at least date, variable
    :param dur: int or "WY", duration to analyze
    :return: df, list of events with date, avg_flow and peak
    """
    var = data.columns[0]
    WYs = data["wy"].unique().astype(int)
    evs = pd.DataFrame(index=WYs)
    if dur=="WY":
        dur_data = None
        print('Analyzing by WY')
        for wy in WYs:
            if sum(pd.isna(data.loc[data["wy"] == wy, var])) > 365*0.1:
                continue
            else:
                if dur == "WY":
                    evs.loc[wy, "annual_sum"] = round(data.loc[data["wy"] == wy, var].sum(),decimal)
                    if var in ["flow","Flow","discharge","Discharge","inflow","Inflow","IN","Q","QU","cfs","CFS"]:
                        evs.loc[wy, "annual_acft"] = round(cfs2af(data.loc[data["wy"] == wy, var].sum()),decimal)
                    evs.loc[wy, "count"] = len(data.loc[data["wy"]==wy, var])
                    max_idx = data.loc[data["wy"] == wy, var].idxmax()
                    evs.loc[wy, "max"] = max_idx
                    evs.loc[wy, f"max_{var}"] = round(data.loc[max_idx, var],decimal)
                    # TODO Add centroid calc
                    #evs.loc[wy,f"centroid_{var}"] = data.loc[data["wy"] == wy].index.astype('int64')*data.loc[data["wy"] == wy, var]/data.loc[data["wy"] == wy].index.astype('int64').sum
    else:
        # Calculate rolling before parsing years
        dur_data = data
        dur_data[var] = dur_data[var].rolling(dur, min_periods=int(np.ceil(dur))).mean()
        for wy in WYs:
            try:
                max_idx = dur_data.loc[dur_data["wy"] == wy, var].idxmax()
            except ValueError:
                continue
            if pd.isna(max_idx):
                continue
            evs.loc[wy,"start"] = max_idx-dt.timedelta(days=int(dur)-1) # place date as start of window
            evs.loc[wy,f"avg_{var}"] = round(dur_data.loc[max_idx,var],decimal)
            if var in ["flow", "Flow", "discharge", "Discharge", "inflow", "Inflow", "IN", "Q", "QU", "cfs", "CFS"]:
                evs.loc[wy,f"volume_acft"] = round(evs.loc[wy,f"avg_{var}"]*dur * 86400 / 43560,decimal)
            evs.loc[wy, "mid"] = max_idx - dt.timedelta(days=max([0,int(dur / 2) - 1]))  # place date as middle of window
            evs.loc[wy, "end"] = max_idx  # place date as end of window
            evs.loc[wy, "max"] = data.loc[evs.loc[wy, "start"]:evs.loc[wy, "end"],var].idxmax()
            evs.loc[wy,f"max_{var}"] = data.loc[evs.loc[wy,"max"],var]
            evs.loc[wy,"count"] = len(data.loc[data["wy"] == wy, var])
            #TODO Add centroid calc
            #evs.loc[wy, f"centroid_{var}"] = data.loc[evs.loc[wy,"start"]:evs.loc[wy,"end"]].index.astype('int64') * data.loc[evs.loc[wy,"start"]:evs.loc[wy,"end"], var] / \
            #                                 data.loc[evs.loc[wy,"start"]:evs.loc[wy,"end"]].index.astype('int64').sum

            # Check start
            if dur_data.loc[evs.loc[wy, "start"], "wy"] < wy:
                evs.loc[wy,"warning"] = "Start in previous WY"
                print(f"{wy} start in previous WY. Check!!!")
            # Check end
            if dur_data.loc[evs.loc[wy, "end"], "wy"] > wy:
                evs.loc[wy,"warning"] = "End in next WY"
                print(f"{wy} end in next WY. Check!!!")

    # TODO: Seasonal split?

    return evs,dur_data

def init_voldurplot(data,wy=None):
    """

    :param data: df, flow timeseries
    :param wy: int, selected wy
    :return: figure
    """
    var = data.columns[0]
    fig, ax = plt.subplots(figsize=(6.25, 4))
    if wy is not None:
        plt.title(wy)
    plt.ylabel(get_varlabel(var))
    ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
    plt.xticks(rotation=90)
    if wy is not None:
        dates = data.index[data["wy"]==wy]
    else:
        dates = data.index
    inflow = data.loc[dates,var]
    plt.plot(dates, inflow, color='black',label=var)

def plot_voldur(s,wy,site_dur,durations):
    """
    This function produces the duration plots for all durations for WY provided
    :param wy: int, the event or wy index
    :param site_dur: list,
        contains dfs, output from analyze_voldur() for each duration listed in durations
    :param durations: list, durations to plot
    :return: figure
    """
    for d in range(0,len(durations)):
        dur = durations[d]
        if dur=="WY":
            continue
        else:
            evs = site_dur[d]
            var = evs.columns[1]
            if pd.isna(evs.loc[wy,:]).all():
                continue
            idx_s = evs.loc[wy,"start"]
            idx_e = evs.loc[wy,"end"]
            avg_val = evs.loc[wy,var]
            if s is None:
                plt.plot([idx_s,idx_s,idx_e,idx_e],[0,avg_val,avg_val,0],label=f"{dur}-day {var}",alpha=0.75)
            else:
                plt.plot([idx_s, idx_s, idx_e, idx_e], [0, avg_val, avg_val, 0], label=f"{s} {dur}-day {var}",alpha=0.75)