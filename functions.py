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

### DATA PREP FUNCTIONS ###
def csv_daily_import(filename,wy="WY"):
    """
    Imports data in a .csv files with two columns: date, variable (user specified)
    :param filename: str, filename or file path
    :param wy: str, "WY
    :return: dataframe with date index, dates, (user specified), month, year and water year
    """
    data = pd.read_csv(filename)
    if len(data.columns) != 2:
        print("Two columns are needed! Exiting.")
        return
    var = data.columns[1]
    data.columns = ["date",var]
    # Remove blank spaces...replace with nan, convert to float
    data.loc[data[var] == ' ', var] = np.nan
    data = data.dropna(how="all")
    data[var] = data[var].astype('float')

    # Convert first column to dates
    data["date"] = pd.to_datetime(data["date"])
    if data["date"].max().year>dt.date.today().year:
        print("Dates exceed current date. Please check dates are correct and in dd-mmm-yyyy format.")
        return
    data.index = data.date

    # Create date index and out dataframe
    date_index = pd.date_range(data.date.min(),data.date.max(),freq="D")
    out = pd.DataFrame(index=date_index)
    out = out.merge(data[var],left_index=True,right_index=True,how="left")

    # Add year, month and wy
    out["year"] = pd.DatetimeIndex(out.index).year
    out["month"] = pd.DatetimeIndex(out.index).month
    out["wy"] = out["year"]
    if wy == "WY":
        out.loc[out["month"] >= 10, "wy"] = out.loc[out["month"] >= 10, "year"] + 1

    return(out)

def nwis_daily_import(site, dtype, start=None, end=None, wy="WY"):
    """
    Imports flows from NWIS site
    :param site: str, USGS site number
    :param dtype: str, "dv" or "iv"
    :param start: str, start date (default is None)
    :param end: str, end date (default is None)
    :param wy: str, "WY
    :return: dataframe with date index, dates, flows, month, year and water year
    """
    if dtype == "dv":
        parameter = "00060_Mean"
    elif dtype == "iv":
        parameter = "00060"

    if (start!=None) & (end!=None):
        try:
            data = nwis.get_record(sites=site, start=start, end=end, service=dtype, parameterCd='00060')
        except ValueError:
            data[var] = np.nan
    else:
        if (start==None) & (end==None):
            try:
                data = nwis.get_record(sites=site, start="1800-01-01",service=dtype, parameterCd='00060')
            except ValueError:
                data["flow"] = np.nan
        else:
            if end==None:
                try:
                    data = nwis.get_record(sites=site, start=start, end="3000-01-01", service=dtype, parameterCd='00060')
                except ValueError:
                    data["flow"] = np.nan
            if start==None:
                try:
                    data = nwis.get_record(sites=site, start="1800-01-01", end=end, service=dtype, parameterCd='00060')
                except ValueError:
                    data["flow"] = np.nan

        data = data.tz_localize(None)
        end = data.index.max()
        start = data.index.min()

    if dtype == "dv":
        date_index = pd.date_range(start, end, freq="D")
    elif dtype == "iv":
        date_index = pd.date_range(start, end, freq="15T")

    out = pd.DataFrame(index=date_index)
    out = out.tz_localize(None)
    out["flow"] = out.merge(data[parameter], left_index=True, right_index=True, how="left")

    out.loc[out["flow"]==-999999,"flow"] = np.nan

    # Add year, month and wy
    out["year"] = pd.DatetimeIndex(out.index).year
    out["month"] = pd.DatetimeIndex(out.index).month
    out["wy"] = out["year"]
    if wy=="WY":
        out.loc[out["month"] >= 10, "wy"] = out.loc[out["month"] >= 10, "year"] + 1

    return(out)

def csv_peak_import(filename):
    """
    Imports data in a .csv files with two columns: wy, date, variable (user specified)
    :param filename: str, filename or file path
    :return: dataframe with date index, dates, (user specified), month, year and water year
    """
    data = pd.read_csv(filename,index_col=0)
    var = data.columns[len(data.columns)-1]
    data.columns = ["date",var]
    # Remove blank spaces...replace with nan, convert to float
    data.loc[data[var] == ' ', var] = np.nan
    data = data.dropna(how="all")
    data[var] = data[var].astype('float')

    # Convert first column to dates
    data["date"] = pd.to_datetime(data["date"], errors='coerce')
    if data["date"].max().year>dt.date.today().year:
        print("Dates exceed current date. Please check dates are correct and in dd-mmm-yyyy format.")
        return
    out = data

    if type(data.index) != pd.core.indexes.numeric.Int64Index:
        # Add year, month and wy
        out["year"] = pd.DatetimeIndex(out.index).year
        out["month"] = pd.DatetimeIndex(out.index).month
        out["wy"] = out["year"]
        if wy == "WY":
            out.loc[out["month"] >= 10, "wy"] = out.loc[out["month"] >= 10, "year"] + 1

        out = out.reset_index(drop=False)
        out.index = out.wy
        out = out.drop(["year", "month", "wy"], axis=1)

    return(out)

def nwis_peak_import(site):
    """
    Imports flows from NWIS site
    :param site: str, USGS site number
    :return: dataframe with date index, dates, flows, month, year and water year
    """
    parameter = "00060"
    dtype = "peaks"

    data = nwis.get_record(sites=site, service=dtype, parameterCd=parameter)

    out = pd.DataFrame(index=data.index)
    out["peak"] = data.peak_va

    # Add year, month and wy
    out["year"] = pd.DatetimeIndex(out.index).year
    out["month"] = pd.DatetimeIndex(out.index).month
    out["wy"] = out["year"]
    out.loc[out["month"] >= 10, "wy"] = out.loc[out["month"] >= 10, "year"] + 1

    out = out.reset_index(drop=False)
    out.index = out.wy

    out = out.drop(["year","month","wy"],axis=1)
    out.columns = ["date","peak"]

    return(out)

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

def plot_wytraces(data,wy_division,sel_wy=None,log=True):
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
    else:
        ax.set_xticks([1,32,62,93,124,153,184,214,245,275,306,337])
        ax.set_xticklabels(["O","N","D","J","F","M","A","M","J","J","A","S"])

    WYs = data["wy"].unique().astype(int)
    i=-1
    doy_data = pd.DataFrame(index=range(1,367),columns=WYs)
    dates = pd.date_range("2020-01-01", "2020-12-31", freq="D", tz='UTC')

    for wy in WYs:
        i=+1
        doy_flow = data.loc[data["wy"]==wy,var]
        doy_idx = np.array(data.loc[data["wy"]==wy].index.dayofyear)
        if wy_division=="WY":
            doy_idx = doy_idx + 92
            doy_idx[0:92] = np.where(doy_idx[0:92]>365,doy_idx[0:92]-365,doy_idx[0:92])
        doy_data.loc[doy_idx,wy] = doy_flow.values
        plt.plot(doy_idx, doy_flow, color="grey",alpha=0.2)
    for d in doy_data.index:
        doy_data.loc[d,"mean"] = doy_data.loc[d,WYs].mean()
        doy_data.loc[d, "median"] = doy_data.loc[d, WYs].median()

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

    plt.plot(doy_data.index, doy_data["mean"], color="black", linestyle="dashed", linewidth=2,label="Mean")
    plt.plot(doy_data.index, doy_data["median"], color="black", linestyle="solid",linewidth=2,label="Median")

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

### CRITICAL DURATION FUNCTIONS ###
def countdur(data, thresh):
    """
    This function loops through daily data and identifies periods of time when data exceed the threshold provided.
    :param data: df, data including at least date, variable
    :param thresh: float, variable value threshold
    :return: df, list of events with indices, date, duration and peak
    """
    var = data.columns[0]
    evs = pd.DataFrame(columns=("start_idx", "end_idx", "month","duration", "peak"))
    ev = False
    ex = -1
    for l in data.index:
        if data.loc[l,var] > thresh and ev == False:
            ev = True
            ex += 1
            dur = 0
            evs.loc[ex, "start_idx"] = l
            if "month" not in data.columns:
                evs.loc[ex, "month"] = data.loc[l].name.month
            else:
                evs.loc[ex, "month"] = data.loc[l,"month"]
        if data.loc[l,var] <= thresh and ev == True:
            ev = False
            evs.loc[ex, "end_idx"] = l - dt.timedelta(days=1)
            evs.loc[ex, "duration"] = dur
            evs.loc[ex, "peak"] = max(data.loc[l - dt.timedelta(days=dur):l,var])
        if ev:
            dur += 1
        else:
            continue

    return (evs)

def analyze_critdur(evs, min_dur, min_peak, plot_max):
    """
    This function plots events defined by countdur() by their peak and volume and calculates critical duration
    :param evs: df, output from coutndur()
    :param min_dur: int, user specified duration limit
    :param min_peak: int, user specified peak limit
    :param plot_max: int, user specified limit on plotting of durations
    :return: figure
    """
    # PLot peaks vs durations
    fig, ax = plt.subplots(figsize=(6.25, 4))
    plt.title("Flow vs Duration (n=" + str(len(evs)) + ")")
    plt.ylabel('Flow ($ft^3$/s)')
    if plot_max == 0:
        plt.xlim(0.5, max(evs.duration)+0.5)
    else:
        plt.xlim(0.5, plot_max)
    ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
    plt.xlabel('Duration (days)')
    # Plot all data
    plt.scatter(evs["duration"], evs["peak"], facecolors='none', edgecolors='grey', label="_nolegend_")

    # Calculate screened data and screened averages
    print("Screening data...")
    evs_lim = evs.loc[(evs["duration"]>min_dur)&(evs["peak"]>min_peak)]
    print("Calculating screened averages...")
    lim_dur = sum(evs_lim["duration"] * evs_lim["peak"]) / sum(evs_lim["peak"])
    lim_peak = sum(evs_lim["duration"] * evs_lim["peak"]) / sum(evs_lim["duration"])
    lim_n = len(evs_lim)
    lim_dur_avg = np.mean(evs_lim["duration"])
    lim_dur_geo = (np.prod(evs_lim["duration"])) ** (1 / lim_n)

    # Plot screened data and limits
    if (min_dur > 0) & (min_peak == 0):
        col = "red"
        scatter_label = "Screened Events"
        plt.plot((min_dur, min_dur), (0, max(evs_lim["peak"])), 'r--', label="Duration Limit")
    if (min_peak > 0) & (min_dur == 0):
        col = "blue"
        scatter_label = "Screened Events"
        plt.plot((0, max(evs_lim["duration"])+1), (min_peak, min_peak), 'b--', label="Peak Limit")
    if (min_peak > 0) & (min_dur > 0):
        col = "black"
        scatter_label = "Screened Events"
        plt.plot((min_dur, min_dur), (0, max(evs_lim["peak"])), 'r--', label="Screening Limits")
        plt.plot((0, max(evs_lim["duration"])), (min_peak, min_peak), 'b--', label="_nolegend_")
    if (min_peak == 0) & (min_dur == 0):
        col = "black"
        scatter_label = "Events"

    # Plot data and duration estimates
    plt.scatter(evs_lim["duration"],evs_lim["peak"],facecolors='none', edgecolors=col, label=scatter_label)
    print("Peak Weighted Screened Avg: {}".format(lim_dur))
    plt.plot(lim_dur, lim_peak, color=col,marker='x',linestyle="None",label="Peak Weighted Avg: {}".format(round(lim_dur, 1)))
    print("Screened A. Avg: {}".format(lim_dur_avg))
    plt.plot(lim_dur_avg, lim_peak * 1.1, color=col,marker='+',linestyle="None",label="Arithmetic Avg: {}".format(round(lim_dur_avg, 1)))
    print("Screened G. Avg: {}".format(lim_dur_geo))
    plt.plot(lim_dur_geo, lim_peak * 1.2, color=col,marker='^',linestyle="None",label="Geometric Avg: {}".format(round(lim_dur_geo, 1)))

    # Annotate
    plt.annotate((str(np.round(lim_dur, 1)) + " (n=" + str(lim_n) + ")"),
                 (lim_dur, lim_peak), color=col)
    plt.annotate(str(np.round(lim_dur_avg, 1)),
                 (lim_dur_avg, lim_peak * 1.2), color=col)
    plt.annotate(str(np.round(lim_dur_geo, 1)),
                 (lim_dur_geo, lim_peak * 1.3), color=col)

    plt.legend(loc="best", prop={'size': 9})

def durationplot(data, evs, e, thresh):
    """
    This function produces the duration plots for all events provided
    :param data: df, data including at least date, variable
    :param evs: df, output from coutndur()
    :param e: int, the event index
    :param thresh: float, data value threshold
    :return: figure
    """
    var = data.columns[0]
    xs = pd.date_range(evs.loc[e, "start_idx"] - dt.timedelta(days=1), evs.loc[e, "end_idx"] + dt.timedelta(days=1))
    indata = data.loc[xs, var]
    cum_indata = data.loc[xs, var]

    for s in xs:
        if s == min(xs):
            cum_indata[s] = 0
        if s == evs.loc[e, "start_idx"]:
            cum_indata[s] = indata[s]
        elif s > evs.loc[e, "start_idx"]:
            cum_indata[s] = indata[s] + cum_indata[s - dt.timedelta(days=1)]

    cum_outdata = data.loc[xs, var]
    for s in reversed(xs):
        if s > evs.loc[e, "end_idx"]:
            cum_outdata[s] = cum_indata[evs.loc[e, "end_idx"]] + thresh
        if s == evs.loc[e, "end_idx"]:
            cum_outdata[s] = cum_indata[s]
            tangency = cum_indata[s]
        elif s < evs.loc[e, "end_idx"]:
            cum_outdata[s] = cum_outdata[s + dt.timedelta(days=1)] - thresh

    plot_dur = range(0, evs.loc[e, "duration"] + 2)
    fig, ax = plt.subplots(figsize=(6.25, 4))
    plt.title("Event Beginning " + evs.loc[e, "start_idx"].strftime("%d-%b-%Y") + " | Duration: " + str(
        evs.loc[e, "duration"]) + " days")
    plt.ylabel('Flow ($ft^3$/s) | Cumulative Flow ($ft^3$/s days) ')
    plt.ylim(0, round(max(cum_outdata), -4) + 10000)
    ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
    plt.xlabel('Duration (days)')
    plt.xlim(min(plot_dur), max(plot_dur))


    plt.bar(plot_dur, indata, width=1,color='blue',alpha=0.5,label="_nolegend_")
    plt.plot(plot_dur, indata, 'blue',label=var)
    plt.plot(plot_dur, cum_indata, "black",label=f"Cum. {var}")
    plt.plot(plot_dur, [thresh]*len(plot_dur),'red', label="Event Threshold")
    plt.plot(plot_dur, cum_outdata, color='maroon',linestyle="dashed",label="Cum. Threshold Flow")
    plt.plot(evs.loc[e, "duration"],tangency,"rx",label="Point of Tangency")
    plt.legend()

### VOLUME DURATION FUNCTIONS
def analyze_voldur(data, dur):
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
        print('Analyzing by WY')
        for wy in WYs:
            if sum(pd.isna(data.loc[data["wy"] == wy, var])) > 365*0.1:
                continue
            else:
                if dur == "WY":
                    max_idx = data.loc[data["wy"] == wy, var].idxmax()
                    evs.loc[wy, "date"] = max_idx
                    evs.loc[wy, "annual_sum"] = round(data.loc[data["wy"] == wy, var].sum(), 0)
                    evs.loc[wy, "annual_acft"] = round(data.loc[data["wy"] == wy, var].sum() * 86400 / 43560, 0)
                    evs.loc[wy, "max"] = round(data.loc[max_idx, var].max(), 0)
                    evs.loc[wy, "count"] = len(data.loc[data["wy"]==wy, var])
    else:
        dur_data = data[var].rolling(dur,min_periods=int(np.ceil(dur*0.90))).mean()
        #max_data = data[var].rolling(dur,min_periods=int(np.ceil(dur*0.90))).max()
        data["wy_shift"] = data["wy"].shift(+(int(dur/2)))

        for wy in WYs:
                try:
                    max_idx = dur_data.loc[data["wy_shift"]==wy].idxmax()
                except ValueError:
                    continue
                if pd.isna(max_idx):
                    continue
                evs.loc[wy,"start"] = max_idx-dt.timedelta(days=int(dur)-1) # place date as start of window
                evs.loc[wy,f"avg_{var}"] = round(dur_data[max_idx],0)
                evs.loc[wy, "mid"] = max_idx - dt.timedelta(days=int(dur / 2) - 1)  # place date as middle of window
                evs.loc[wy, "end"] = max_idx  # place date as end of window
                evs.loc[wy, "max"] = dur_data.loc[evs.loc[wy, "start"]:evs.loc[wy, "end"]].idxmax() # TODO FIX MAX!
                evs.loc[wy,f"max_{var}"] = data.loc[evs.loc[wy,"max"],var]
                evs.loc[wy,"count"] = len(data.loc[data["wy"] == wy, var])


    return (evs)

def plot_voldur(data,wy,site_dur,durations):
    """
    This function produces the duration plots for all durations for WY provided
    :param data: df, inflows including at least date, flow
    :param wy: int, the event or wy index
    :param site_dur: list,
        contains dfs, output from analyze_voldur() for each duration listed in durations
    :param durations: list, durations to plot
    :return: figure
    """
    var = data.columns[0]
    for d in range(0,len(durations)):
        dur = durations[d]
        evs = site_dur[d]
        if dur=="WY":
            if (wy < 0) or (pd.isna(evs.loc[wy, "count"])):
                #return
                print("eat slugs!")
            fig, ax = plt.subplots(figsize=(6.25, 4))
            plt.title(wy)
            plt.ylabel(get_varlabel(var))
            ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
            plt.xticks(rotation=90)
            dates = data.index[data["wy"]==wy]
            inflow = data.loc[dates,var]
            plt.plot(dates, inflow, color='black',label=var)
        else:
            idx_s = evs.loc[wy,"start"]
            idx_e = evs.loc[wy,"end"]
            avg_val = evs.loc[wy,f"avg_{var}"]
            plt.plot([idx_s,idx_s,idx_e,idx_e],[0,avg_val,avg_val,0],label=f"{dur}-day {var}",alpha=0.75)

### PLOT VOLUME DURATION MULTIPLOT FUNCTIONS ###

def plot_trendsshifts(evs,dur,var):
    """
    This function produces the plots for all durations using plotting positions
    :param evs: df, output from analyze_voldur() for duration
    :param dur: str, duration being plotted
    :param var: str, parameter to plot (e.g., "avg_{parameter}")
    :return: figure
    """
    # calculate plotting positions
    if dur=="WY":
        return
    else:
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
        plt.plot(evs.index,evs.index*theil[0]+theil[1],"r--",label=f'Theil Slope = {int(theil[0])} \n (Kendall Tau p-value = {round(kendall.pvalue,3)})')

        for i in evs.index[::10]:
            if i>max(evs.index)-20:
                continue
            print(f'{i}-{i+10} vs {i+11}-{i+21}')
            mw = mannwhitneyu(evs.loc[i:i+10,var],evs.loc[i+11:i+21,var])
            print(mw)

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
    plt.xticks(rotation=90)
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
            peaks_sorted.to_csv(f"plot/{site}_{dur}_pp.csv")
            plt.scatter(peaks_sorted["pp"]*100,peaks_sorted[var],label=f"{dur}-day Flow")

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

        if eventdate not in str(data.columns):
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

def get_varlabel(var):
    if var in ["flow","Flow","discharge","Discharge","inflow","Inflow","IN","Q","cfs","CFS"]:
        lab = "Flow (ft$^3$/s)"
    elif var in ["peak", "Peak", "peaks", "Peaks"]:
        lab = "Peak Flow (ft$^3$/s)"
    elif var in ["stage","Stage","feet","Feet","FT","ft","pool_elevation","elevation","Elevation","elev","Elev"]:
        lab = "Stage (ft)"
    elif var in ["SWE","swe","snowpack","snowdepth","snow","SNWD","WTEQ"]:
        lab = "SWE (in)"
    else:
        lab = var
    return lab

# INCOMPLETE.
#     if mixed:
#         if not os.path.isdir("mixed"):
#             os.mkdir("mixed")
#
#         from sklearn.mixture import GaussianMixture
#
#         def GMM_sklearn(x, weights=None, means=None, covariances=None):
#             model = GaussianMixture(n_components=2,
#                                     covariance_type='full',
#                                     tol=0.01,
#                                     max_iter=1000,
#                                     weights_init=weights,
#                                     means_init=means,
#                                     precisions_init=covariances)
#             model.fit(x)
#             print("\nscikit learn:\n\tphi: %s\n\tmu_0: %s\n\tmu_1: %s\n\tsigma_0: %s\n\tsigma_1: %s"
#                   % (model.weights_[1], model.means_[0, :], model.means_[1, :], model.covariances_[0, :],
#                      model.covariances_[1, :]))
#             return model.predict(x), model.predict_proba(x)[:, 1]
#
#
#         for dur, dat in zip(durations_sel, site_dur):
#             print(dur)
#             x = np.reshape(dat[var].values, (len(dat), 1))
#             sklearn_forecasts, posterior_sklearn = GMM_sklearn(x)
#
#             dat["forecast"] = sklearn_forecasts
#             dat.to_csv(f"mixed/{site}_{dur}_forecast.csv")