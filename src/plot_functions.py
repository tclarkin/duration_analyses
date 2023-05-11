# -*- coding: utf-8 -*-
"""
### MULTIPLOT FUNCTIONS ###
@author: tclarkin (USBR 2021)

This script contains the plotting functions and pre-defined variables used in the duration analyses 5

"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from scipy.stats import mannwhitneyu
from scipy.stats import kendalltau
from scipy.stats.mstats import theilslopes
from scipy.stats import norm
from src.functions import get_varlabel

def plot_trendsshifts(evs,dur,var):
    """
    This function produces the plots for all durations using plotting positions
    :param evs: df, output from analyze_voldur() for duration
    :param dur: str, duration being plotted
    :param var: str, parameter to plot (e.g., "avg_{parameter}")
    :return: figure
    """
    # calculate plotting positions
    fig, ax = plt.subplots(figsize=(6.25, 4))
    plt.get_cmap("viridis")
    plt.ylabel(get_varlabel(var))
    plt.xlabel('Year')
    ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
    ax.grid(which='minor', linestyle=':', linewidth='0.1', color='black')
    plt.scatter(evs.index,evs[var],label=f"{dur}-day AMS")

    # Theil Slope
    theil = theilslopes(evs[var],evs.index)
    kendall = kendalltau(evs[var],evs.index)
    if theil[0]<1:
        theil_slope = round(theil[0],1)
    else:
        theil_slope = round(theil[0],0)
    plt.plot(evs.index,evs.index*theil[0]+theil[1],"r--",label=f'Theil Slope = {theil_slope} \n (Kendall Tau p-value = {round(kendall.pvalue,3)})')

    plt.legend()

def mannwhitney(evs,dur,var,block):
    if len(evs.index) < 2*block:
        return

    fig, ax = plt.subplots(figsize=(6.25, 4))
    plt.get_cmap("viridis")
    plt.ylabel(f"{dur} {get_varlabel(var)}")
    plt.xlabel('Year')
    plt.title(block)

    mw = pd.DataFrame()
    for i in evs.index[::block]:
        if i > max(evs.index) - 2*block:
            continue
        idx = f'{i}-{i + block} vs {i + block+1}-{i + 2*block+1}'
        mw.loc[idx,"wy"] = i
        mx = mannwhitneyu(evs.loc[i:i + block, var], evs.loc[i + block+1:i + 2*block+1, var])
        mw.loc[idx,"pvalue"] = mx.pvalue

    plt.plot(mw.wy,mw.pvalue)
    plt.plot([evs.index.min(),evs.index.max()],[0.05]*2,linestyle="dashed",label="0.05 significance")
    plt.legend()

def plot_normality(evs,dur,var):
    """
    This function produces the plots for all durations using plotting positions
    :param evs: df, output from analyze_voldur() for duration
    :param dur: str, duration being plotted
    :param var: str, the variable being plotted
    :param var: str, parameter to plot (e.g., "avg_{parameter}")
    :return: figure
    """
    # calculate plotting positions
    if dur=="WY":
        return
    else:
        fig, ax = plt.subplots(figsize=(6.25, 4))
        plt.get_cmap("viridis")
        plt.ylabel(f'Log10 {get_varlabel(var)}')
        plt.xlabel('Normal Quantile')
        ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
        ax.grid(which='minor', linestyle=':', linewidth='0.1', color='black')

        peaks_sorted = calc_pp(evs[var], 0)
        peaks_sorted["log"] = np.log10(peaks_sorted[var])
        peaks_sorted["norm"] = norm.ppf(1-peaks_sorted["pp"])
        plt.scatter(peaks_sorted["norm"],peaks_sorted["log"],label=f"{dur}-day AMS (n = {len(peaks_sorted)})")
        ols = np.polyfit(peaks_sorted["norm"],peaks_sorted["log"],deg=1)
        corr = np.corrcoef(peaks_sorted["log"],peaks_sorted["norm"]*ols[0]+ols[1])
        plt.plot(peaks_sorted["norm"],peaks_sorted["norm"]*ols[0]+ols[1],"r--",label=f"OLS fit (R={round(corr[0][1],3)})")
        plt.legend()

def calc_pp(peaks,alpha=0):
    """
    This function calculates plotting positions
    :param peaks: df, peaks with index defining year (or unique events)
    :param alpha: float, value used in plotting positions
    :return: df, pp and flow
    """
    peaks_clean = peaks.dropna()
    peaks_sorted = peaks_clean.sort_values(ascending=False)
    peaks_sorted = peaks_sorted.reset_index()
    peaks_sorted["pp"] = (peaks_sorted.index+1-alpha)/(len(peaks_sorted)+1-2*alpha)
    return(peaks_sorted)

def plot_voldurpp(site,site_dur,durations,alpha=0):
    """
    This function produces the plots for all durations using plotting positions
    :param data: df, inflows including at least date, variable
    :param site_dur: list,
        contains dfs, output from analyze_voldur() for each duration listed in durations
    :param durations: list, durations to plot
    :param alpha: float, alpha value for plotting positions
    :return: figure
    """
    if not os.path.isdir("plot"):
        os.mkdir("plot")

    fig, ax = plt.subplots(figsize=(6.25, 4))
    plt.get_cmap("viridis")
    plt.xlabel('Exceedance Probability')
    plt.yscale('log')
    ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
    ax.set_xscale('prob')
    plt.xlim(0.01, 99.99)

    plt.gca().invert_xaxis()
    ax.grid()
    ax.grid(which='minor', linestyle=':', linewidth='0.1', color='black')

    minp = 1000000
    maxp = 0

    for d in range(0,len(durations)):
        dur = durations[d]
        evs = site_dur[d]
        var = evs.columns[1]

        # calculate plotting positions
        if dur=="WY":
            continue
        else:
            peaks_sorted = calc_pp(evs[var],alpha)
            if "index" in peaks_sorted.columns:
                peaks_all = peaks_sorted.merge(evs, left_on="index", right_index=True, how="outer")
            else:
                peaks_all = peaks_sorted.merge(evs,left_on="wy",right_index=True,how="outer")
            peaks_all.to_csv(f"{site}/plot/{site}_{dur}_pp.csv")
            plt.scatter(peaks_sorted["pp"]*100,peaks_sorted[var],label=f"{dur}-day {var}")

            if peaks_sorted[var].min() < minp:
                minp = peaks_sorted[var].min()
            if peaks_sorted[var].max() > maxp:
                maxp = peaks_sorted[var].max()

    plt.ylim(minp,maxp)
    plt.legend()

def plot_voldurpdf(site_dur,durations):
    """
    This function produces the pdf plots for all durations
    :param site_dur: list,
        contains dfs, output from analyze_voldur() for each duration listed in durations
    :param durations: list, durations to plot
    :return: figure
    """
    if not os.path.isdir("plot"):
        os.mkdir("plot")

    var = site_dur[0].columns[1]

    dat = list()
    for d in range(0, len(durations)):
        dur = durations[d]
        if dur == "WY":
            continue
        data = site_dur[d].iloc[:,1]
        data = data[data>0]
        dat.append(np.log10(data))

    fig, ax = plt.subplots(figsize=(6.25, 4))
    plt.get_cmap("viridis")
    plt.ylabel('Probability')
    plt.xlabel(f'Log10 {get_varlabel(var)}')
    plt.hist(dat,density=True,label=durations)
    plt.legend()

def plot_voldurmonth(site_dur,durations,stat,eventdate="mid",wy_division="WY"):
    """
    This function produces the pdf plots for all durations
    :param site_dur: list,
        contains dfs, output from analyze_voldur() for each duration listed in durations
    :param durations: list, durations to plot
    :return: figure
    """
    if not os.path.isdir("plot"):
        os.mkdir("plot")

    var = site_dur[0].columns[1]

    width = 0.8/len(durations)

    fig, ax = plt.subplots(figsize=(6.25, 4))
    plt.get_cmap("viridis")
    plt.ylabel(f"{stat} {get_varlabel(var)}")
    plt.xlabel('Month')

    for d in range(0, len(durations)):
        dur = durations[d]
        if dur == "WY":
            continue
        name = f"{durations[d]}"
        data = site_dur[d]
        data = data.dropna()

        if eventdate not in list(data.columns):
            date_used = "date"
        else:
            date_used = eventdate

        data.index = pd.to_datetime(data[date_used])
        var = data.columns[1]

        if "month" not in data.columns:
            data.index = pd.to_datetime(data[date_used])

        if stat=="count":
            summary = pd.DataFrame(data.groupby([data.index.month],sort=False).count().eval(var))
        if stat=="mean":
            summary = pd.DataFrame(data.groupby([data.index.month], sort=False).mean().eval(var))
        if stat=="max":
            summary = pd.DataFrame(data.groupby([data.index.month], sort=False).max().eval(var))
        if wy_division=="WY":
            summary.loc[summary.index >= 10,"plot"] = summary.loc[summary.index >= 10].index - 9
            summary.loc[summary.index < 10,"plot"] = summary.loc[summary.index < 10].index + 3
        plt.bar(summary["plot"]+0.1+width*d,summary[var],width=width,label=name)

    if wy_division=="WY":
        month_names = ["Oct","Nov","Dec","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep"]
    else:
        month_names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    plt.xticks([1,2,3,4,5,6,7,8,9,10,11,12],month_names)
    plt.legend()
