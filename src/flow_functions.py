# -*- coding: utf-8 -*-
"""
### FLOW FUNCTIONS ###
@author: tclarkin (USBR 2021)

This script contains the flow duration analysis functions and pre-defined variables used in the duration analyses 2a and b

"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from src.functions import get_varlabel


### FLOW DURATION FUNCTIONS ###
# Define standard monthly combinations
# Annual
annualcombos = {"Annual": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]}
# Monthly
monthcombos = {"Jan": [1],
               "Feb": [2],
               "Mar": [3],
               "Apr": [4],
               "May": [5],
               "Jun": [6],
               "Jul": [7],
               "Aug": [8],
               "Sep": [9],
               "Oct": [10],
               "Nov": [11],
               "Dec": [12]}
# All Monthly
allcombos = dict()
months = {1: "Jan",
          2: "Feb",
          3: "Mar",
          4: "Apr",
          5: "May",
          6: "Jun",
          7: "Jul",
          8: "Aug",
          9: "Sep",
          10: "Oct",
          11: "Nov",
          12: "Dec"}
for m in range(1, 13):
    for n in range(m, 13):
        if n < 10:
            title = str(str(0) + str(m) + "-" + str(0) + str(n) + '.' + months[m] + '-' + months[n])
        if m < 10 and n >= 10:
            title = str(str(0) + str(m) + "-" + str(n) + '.' + months[m] + '-' + months[n])
        elif m >= 10 and n >= 10:
            title = str(str(m) + '.' + months[m] + '-' + months[n])
        if m == n:
            vals = [m]
        else:
            vals = list(range(m, n + 1))
        allcombos.update({title: vals})

# Standard precentages
standard = [0.001,
            0.002,
            0.005,
            0.01,
            0.02,
            0.05,
            0.1,
            0.15,
            0.2,
            0.3,
            0.4,
            0.5,
            0.6,
            0.7,
            0.8,
            0.85,
            0.9,
            0.95,
            0.99,
            0.995,
            0.998,
            0.999]

# Define functions
def calculate_ep(data, combo):
    """
    Calculates exceedance probabilities for flow duration given selected months
    :param data: df, containing at least date, month and flow
    :param combo: list, months being analyzed
    :return: df, sorted values with exceedance probability
    """
    var = data.columns[0]
    x = data.loc[data["month"].isin(combo), var]
    x = x.dropna()
    dur_ep = x.sort_values(ascending=False)
    dur_ep = dur_ep.reset_index()
    dur_ep["exceeded"] = (dur_ep.index.values+1)/(len(dur_ep)+1)

    if dur_ep.empty:
        dur_ep["exceeded"] = [0,1]
        dur_ep["flow"] = [0,0]
    return (dur_ep)

def summarize_ep(dur_ep, pcts):
    """
    Creates table using user defined pcts
    :param durflows: output from flowdur function (sorted variable with exceeded
    :param pcts: list, user supplied decimal pcts for calculation
    :return:
    """
    var = dur_ep.columns[1]
    durtable = pd.DataFrame(index=pcts)
    durtable[var] = np.zeros(len(pcts))
    for p in pcts:
        idx = (np.abs(dur_ep["exceeded"] - p)).idxmin()
        durtable.loc[p, var] = round(dur_ep.loc[idx, var], 0)
    return (durtable)

def plot_dur_ep():
    """
    Initializes standard duration plot
    :return:
    """
    fig, ax = plt.subplots(figsize=(6.25, 4))
    plt.get_cmap("viridis")
    plt.xlabel('Exceedance Probability')
    plt.yscale('log')
    ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
    ax.set_xscale('prob')
    plt.xlim(0.01, 99.99)
    plt.xticks(rotation=90)
    plt.gca().invert_xaxis()
    ax.grid()
    ax.grid(which='minor', linestyle=':', linewidth='0.1', color='black')

def plot_monthly_dur_ep(durtable,combos,var):
    """
    Initializes monthly duration plot
    :return:
    """
    fig, ax = plt.subplots(figsize=(6.25, 4))
    plt.get_cmap("viridis")
    plt.xlabel('Month')
    plt.ylabel(get_varlabel(var))
    plt.yscale('log')
    ax.set_xticks([1,2,3,4,5,6,7,8,9,10,11,12])
    ax.set_xticklabels(["J","F","M","A","M","J","J","A","S","O","N","D"])
    ax.grid()
    ax.grid(which='minor', linestyle=':', linewidth='0.1', color='black')
    ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))

    pcts = [0.001,0.01,0.05,0.1,0.3,0.5,0.7,0.9,0.95,0.99,0.999]
    for p in pcts:
        if pd.isna(durtable.loc[p,:]).all():
            plt.plot(list(combos.values()),durtable.loc[p,:], linestyle="dashed", label=f"{p} (zero)")
        else:
            plt.plot(list(combos.values()),durtable.loc[p,:],label=p)
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.9, box.height])
    plt.legend(title="Ex. Prob.",bbox_to_anchor=(1, 0.5), loc='center left',prop={'size': 10})

def analyze_dur(data,combos,pcts,var):
    """
    Conducts flow duration analysis
    :param data: df, raw data with at least date, month, flow
    :param combos: list, months being analyzed
    :param pcts: list, decimal exceedance probabilities included
    :param var: str, variable name
    :return: df, table of results
    """
    full_table = pd.DataFrame(index=pcts)
    plot_dur_ep()

    b = -1

    all_durflows = list()
    for key in combos:
        b += 1
        print(key)
        combo = combos[key]
        dur_ep = calculate_ep(data, combo)
        all_durflows.append(dur_ep)
        table = summarize_ep(dur_ep, pcts)
        full_table.loc[:, key] = table[var]
        plt.plot(dur_ep["exceeded"] * 100, dur_ep[var], label=key)
        plt.ylabel(get_varlabel(var))

    if len(combos) > 4:
        plt.legend(prop={'size': 8})
    else:
        plt.legend()
    return (full_table,all_durflows)

def plot_wytraces(data,wy_division,quantiles=[0.05,0.5,0.95],sel_wy=None,log=True):
    """
    This function produces a single plot of the WY with all WYs plotted as traces and the max, min, mean and median.
    :param data: df, inflows including at least date, flow
    :param evs: df, output from analyze_voldur() for WY
    :param wy_division: str, "WY" or "CY"
    :param sel_wy: list, selected WYs to plot colored traces for
    :return: figure
    """
    var = data.columns[0]

    fig, ax = plt.subplots(figsize=(6.25, 4))

    if wy_division=="CY":
        ax.set_xticks([1,32,60,91,121,152,182,213,244,274,305,335])
        ax.set_xticklabels(["J","F","M","A","M","J","J","A","S","O","N","D"])
        col = "year"
    else:
        ax.set_xticks([1,32,62,93,124,153,184,214,245,275,306,337])
        ax.set_xticklabels(["O","N","D","J","F","M","A","M","J","J","A","S"])
        col = "wy"

    WYs = data[col].unique().astype(int)
    i=-1
    doy_data = pd.DataFrame(index=range(1,367),columns=WYs)
    dates = pd.date_range("2020-01-01", "2020-12-31", freq="D", tz='UTC')

    for wy in WYs:
        i=+1
        doy_flow = data.loc[data[col]==wy,var]
        doy_idx = np.array(data.loc[data[col]==wy].index.dayofyear)
        if wy_division=="WY":
            doy_idx = doy_idx + 92
            doy_idx[0:92] = np.where(doy_idx[0:92]>365,doy_idx[0:92]-365,doy_idx[0:92])
        doy_data.loc[doy_idx,wy] = doy_flow.values
        plt.plot(doy_idx, doy_flow, color="grey",alpha=0.2)

    # Plot min and max year, volume
    annual_vol = doy_data.sum().sort_values()
    annual_vol = annual_vol[annual_vol.values>0]
    minwy = annual_vol.index[0]
    maxwy = annual_vol.index[len(annual_vol)-1]
    plt.plot(doy_data.index,doy_data[minwy], color="maroon",label=f"Driest, {minwy}")
    plt.plot(doy_data.index, doy_data[maxwy], color="lime", label=f"Wettest, {maxwy}")

    if sel_wy is not None:
        sel_col = ["blue","orange","purple","cyan"]
        for sel in range(0,len(sel_wy)):
            plt.plot(doy_data.index, doy_data[sel_wy[sel]], color=sel_col[sel], linestyle="dashdot", label=f"{sel_wy[sel]}")

    for d in doy_data.index:
        doy_data.loc[d,"mean"] = doy_data.loc[d,WYs].mean()
        for q in quantiles:
            doy_data.loc[d, q] = doy_data.loc[d,WYs].quantile(q)

    plt.plot(doy_data.index, doy_data["mean"], color="black", linestyle="dashed", linewidth=2,label="Mean")
    for q in quantiles:
        plt.plot(doy_data.index, doy_data[q], linestyle="solid",linewidth=2,label=q)

    plt.xlim(1,366)
    plt.xticks(rotation=90)
    if log:
        ax.set_yscale("log")
        if ax.get_ylim()[0]<1:
            ax.set_ylim(bottom = 1)
        ax.set_ylim(top = data[var].max()*1.01)
    ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
    plt.ylabel(get_varlabel(var))
    plt.legend(prop={'size': 8})

    return(doy_data)