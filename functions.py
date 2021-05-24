# -*- coding: utf-8 -*-
"""
Duration Analyses Functions
@author: tclarkin (USBR 2021)

This script contains all of the functions and pre-defined variables used in the duration analyses

"""

import dataretrieval.nwis as nwis
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import probscale
import datetime as dt

### DATA PREP FUNCTIONS ###
def flowcsv_import(filename,wy="WY"):
    """
    Imports flow data in a .csv files with two columns: date, flow
    :param filename: str, filename or file path
    :param wy: str, "WY
    :return: dataframe with date index, dates, flows, month, year and water year
    """
    data = pd.read_csv(filename)
    if len(data.columns) != 2:
        print("Two columns are needed! Exiting.")
        return
    data.columns = ["date","flow"]
    # Remove blank spaces...replace with nan, convert to float
    data.loc[data["flow"] == ' ', "flow"] = np.nan
    data = data.dropna(how="all")
    data["flow"] = data["flow"].astype('float')

    # Convert first column to dates
    data["date"] = pd.to_datetime(data["date"], errors='coerce')
    data.index = data.date

    # Create date index and out dataframe
    date_index = pd.date_range(data.date.min(),data.date.max(),freq="D")
    out = pd.DataFrame(index=date_index)
    out = out.merge(data["flow"],left_index=True,right_index=True,how="left")

    # Add year, month and wy
    out["year"] = pd.DatetimeIndex(out.index).year
    out["month"] = pd.DatetimeIndex(out.index).month
    out["wy"] = out["year"]
    if wy == "WY":
        out.loc[out["month"] >= 10, "wy"] = out.loc[out["month"] >= 10, "year"] + 1

    return(out)

def nwis_import(site, dtype, start=None, end=None, wy="WY"):
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
            data["flow"] = np.nan
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

        end = data.index.max()
        start = data.index.min()

    if dtype == "dv":
        date_index = pd.date_range(start, end, freq="D", tz='UTC')
    elif dtype == "iv":
        date_index = pd.date_range(start, end, freq="15T", tz='UTC')

    out = pd.DataFrame(index=date_index)
    out["flow"] = out.merge(data[parameter], left_index=True, right_index=True, how="left")

    out.loc[out["flow"]==-999999,"flow"] = np.nan

    # Add year, month and wy
    out["year"] = pd.DatetimeIndex(out.index).year
    out["month"] = pd.DatetimeIndex(out.index).month
    out["wy"] = out["year"]
    if wy=="WY":
        out.loc[out["month"] >= 10, "wy"] = out.loc[out["month"] >= 10, "year"] + 1

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
    x = data.loc[data["month"].isin(combo), "flow"]
    y = x.sort_values(ascending=False)
    y = y.reset_index()
    y["exceeded"] = (y.index.values+1)/(len(y)+1)
    return (y)

def summarize_ep(durflows, pcts):
    """
    Creates table using user defined pcts
    :param durflows: output from flowdur function (sorted "flow" with exceeded
    :param pcts: list, user supplied decimal pcts for calculation
    :return:
    """
    z = pd.DataFrame(index=pcts)
    z["flow"] = np.zeros(len(pcts))
    for p in pcts:
        idx = (np.abs(durflows["exceeded"] - p)).idxmin()
        z.loc[p, "flow"] = round(durflows.loc[idx, "flow"], 0)
    return (z)

def plot_flowdur():
    """
    Initializes flow duration plot
    :return:
    """
    fig, ax = plt.subplots(figsize=(8, 6))
    plt.get_cmap("viridis")
    plt.ylabel('Flow ($ft^3/s$)')
    plt.xlabel('Exceedance Probability')
    plt.yscale('log')
    ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
    ax.set_xscale('prob')
    plt.xlim(0.01, 99.99)
    plt.xticks(rotation=90)
    plt.gca().invert_xaxis()
    ax.grid()
    ax.grid(which='minor', linestyle=':', linewidth='0.1', color='black')

def analyze_flowdur(data,combos,pcts):
    """
    Conducts flow duration analysis
    :param data: df, raw data with at least date, month, flow
    :param combos: list, months being analyzed
    :param pcts: list, decimal exceedance probabilities included
    :return: df, table of results
    """
    full_table = pd.DataFrame(index=pcts)
    plot_flowdur()

    b = -1
    for key in combos:
        b += 1
        print(key)
        combo = combos[key]
        durflows = calculate_ep(data, combo)
        table = summarize_ep(durflows, pcts)
        full_table.loc[:, key] = table["flow"]
        plt.plot(durflows["exceeded"] * 100, durflows["flow"], label=key)

    plt.legend()
    return (full_table)

### CRITICAL DURATION FUNCTIONS ###
def countdur(data, thresh):
    """
    This function loops through daily flows and identifies periods of time when flows exceed the threshold provided.
    :param data: df, inflows including at least date, flow
    :param thresh: float, flow value threshold
    :return: df, list of events with indices, date, duration and peak
    """
    evs = pd.DataFrame(columns=("start_idx", "end_idx", "month","duration", "peak"))
    ev = False
    ex = -1
    for l in data.index:
        if data.loc[l,"flow"] > thresh and ev == False:
            ev = True
            ex += 1
            dur = 0
            evs.loc[ex, "start_idx"] = l
            evs.loc[ex, "month"] = data.loc[l,"month"]
        if data.loc[l,"flow"] <= thresh and ev == True:
            ev = False
            evs.loc[ex, "end_idx"] = l - dt.timedelta(days=1)
            evs.loc[ex, "duration"] = dur
            evs.loc[ex, "peak"] = max(data.loc[l - dt.timedelta(days=dur):l,"flow"])
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
    fig, ax = plt.subplots(figsize=(7, 5))
    plt.title("Peak Flow vs Duration (n=" + str(len(evs)) + ")")
    plt.ylabel('Peak Flow ($ft^3$/s)')
    if plot_max == 0:
        plt.xlim(0, max(evs.duration))
    else:
        plt.xlim(0, plot_max)
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
        plt.plot((0, max(evs_lim["duration"])), (min_peak, min_peak), 'b--', label="Peak Limit")
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

def analyze_monthlydur(evs):
    """
    Thie function plots events defined by countdur() by their appropriate month to help identify annual patterns
    :param evs: df, output from coutndur()
    :return: figure
    """
    stats = pd.DataFrame(columns=("month", "avg. dur", "count", "fraction"))
    stats["month"] = range(1, 13)

    # Average duration by month, number of events and fraction of all
    for m in range(0, 12):
        stats.loc[m, "avg. dur"] = np.mean(evs.loc[evs["month"] == m + 1, "duration"])
        stats.loc[m, "count"] = len(evs[evs["month"] == m + 1])
        stats.loc[m, "fraction"] = stats.loc[m, "count"] / len(evs)

        # PLot durations vs month
    fig = plt.subplots(figsize=(6, 4))
    plt.title("Durations vs Month (n=" + str(len(evs)) + ")")
    plt.ylabel('Duration (days)')
    x_ticks = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    plt.xticks(range(1, 14), x_ticks)

    # Plot all data
    plt.scatter(evs["month"], evs["duration"], facecolors='none', edgecolors='grey',alpha=0.5, label="Events")
    plt.plot(stats["month"], stats["avg. dur"], 'r+', label="Average Duration (Fraction of Total)")

    for m in range(0, 12):
        if pd.isna(stats.loc[m, "avg. dur"]):
            continue
        else:
            y = int(stats.loc[m, "avg. dur"]) + 0.05
            x =int(stats.loc[m, "month"]) + 0.05

        plt.annotate((str(round(stats.loc[m, "avg. dur"],1)) + " (" + str(np.round(stats.loc[m, "fraction"], 2)) + ")"),[x, y], color="red")

    plt.legend(loc="best")

    return(stats)

def analyze_monthlypeak(evs):
    """
    Thie function plots events defined by countdur() by their appropriate month to help identify annual patterns
    :param evs: df, output from coutndur()
    :return: figure
    """
    stats = pd.DataFrame(columns=("month", "avg. peak", "count", "fraction"))
    stats["month"] = range(1, 13)

    # Average duration by month, number of events and fraction of all
    for m in range(0, 12):
        stats.loc[m, "avg. peak"] = np.mean(evs.loc[evs["month"] == m + 1, "peak"])
        stats.loc[m, "count"] = len(evs[evs["month"] == m + 1])
        stats.loc[m, "fraction"] = stats.loc[m, "count"] / len(evs)

        # PLot durations vs month
    fig = plt.subplots(figsize=(6, 4))
    plt.title("Peaks vs Month (n=" + str(len(evs)) + ")")
    plt.ylabel('Peaks (ft$^3$/s)')
    x_ticks = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    plt.xticks(range(1, 14), x_ticks)

    # Plot all data
    plt.scatter(evs["month"], evs["peak"], facecolors='none', edgecolors='grey',alpha=0.5,label="Events")
    plt.plot(stats["month"], stats["avg. peak"], 'r+', label="Average Peak (Fraction of Total)")

    for m in range(0, 12):
        if pd.isna(stats.loc[m, "avg. peak"]):
            continue
        else:
            y = int(stats.loc[m, "avg. peak"]) + 0.05
            x = int(stats.loc[m, "month"]) + 0.05

        plt.annotate((str(int(stats.loc[m, "avg. peak"])) + " (" + str(np.round(stats.loc[m, "fraction"], 2)) + ")"),[x,y],color="red")

    plt.legend(loc="best")

    return(stats)

def durationplot(data, evs, e, thresh):
    """
    This function produces the duration plots for all events provided
    :param data: df, inflows including at least date, flow
    :param evs: df, output from coutndur()
    :param e: int, the event index
    :param thresh: float, flow value threshold
    :return: figure
    """
    xs = pd.date_range(evs.loc[e, "start_idx"] - dt.timedelta(days=1), evs.loc[e, "end_idx"] + dt.timedelta(days=1))
    inflow = data.loc[xs, "flow"]
    cum_inflow = data.loc[xs, "flow"]

    for s in xs:
        if s == min(xs):
            cum_inflow[s] = 0
        if s == evs.loc[e, "start_idx"]:
            cum_inflow[s] = inflow[s]
        elif s > evs.loc[e, "start_idx"]:
            cum_inflow[s] = inflow[s] + cum_inflow[s - dt.timedelta(days=1)]

    cum_outflow = data.loc[xs, "flow"]
    for s in reversed(xs):
        if s > evs.loc[e, "end_idx"]:
            cum_outflow[s] = cum_inflow[evs.loc[e, "end_idx"]] + thresh
        if s == evs.loc[e, "end_idx"]:
            cum_outflow[s] = cum_inflow[s]
        elif s < evs.loc[e, "end_idx"]:
            cum_outflow[s] = cum_outflow[s + dt.timedelta(days=1)] - thresh

    plot_dur = range(0, evs.loc[e, "duration"] + 2)
    fig, ax = plt.subplots(figsize=(6, 4))
    plt.title("Event Beginning " + evs.loc[e, "start_idx"].strftime("%d-%b-%Y") + " | Duration: " + str(
        evs.loc[e, "duration"]))
    plt.ylabel('Cumulative Flow / Flow ($ft^3$/s)')
    plt.ylim(0, round(max(cum_outflow), -4) + 10000)
    ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
    plt.xlabel('Duration (days)')
    plt.xlim(min(plot_dur), max(plot_dur))
    plt.plot(plot_dur, inflow, 'blue')
    plt.plot(plot_dur, cum_inflow, "black")
    plt.plot(plot_dur, cum_outflow, 'r--')
    plt.legend(["Inflow", "Cum. Inflow", "Cum. Release"])

### VOLUME DURATION FUNCTIONS
def analyze_voldur(data, dur):
    """
    This function calculates a rolling mean and then identifies the ann. max. for each WY
    :param data: df, inflows including at least date, flow
    :param dur: int or "WY", duration to analyze
    :return: df, list of events with date, avg_flow and peak
    """
    WYs = data["wy"].unique().astype(int)
    evs = pd.DataFrame(index=WYs)
    if dur=="WY":
        print('Analyzing by WY')
    else:
        dur_flows = data["flow"].rolling(dur).mean()
        max_flows = data["flow"].rolling(dur).max()
    for wy in WYs:
        if sum(pd.isna(data.loc[data["wy"]==wy,"flow"]))>50:
            continue
        else:
            if dur=="WY":
                max_idx = data.loc[data["wy"]==wy,"flow"].idxmax()
                evs.loc[wy, "date"] = max_idx
                evs.loc[wy, "annual_volume"] = round(data.loc[data["wy"]==wy, "flow"].sum()*86400/43560, 0)
                evs.loc[wy, "peak"] = round(data.loc[max_idx, "flow"].max(), 0)
                evs.loc[wy, "count"] = len(data.loc[data["wy"]==wy, "flow"])
            else:
                try:
                    max_idx = dur_flows.loc[data["wy"]==wy].idxmax()
                except ValueError:
                    continue
                if pd.isna(max_idx):
                    continue
                evs.loc[wy,"date"] = max_idx-dt.timedelta(days=dur-1)
                evs.loc[wy,"avg_flow"] = round(dur_flows[max_idx],0)
                evs.loc[wy,"peak"] = round(max_flows[max_idx],0)

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
    for d in range(0,len(durations)):
        dur = durations[d]
        evs = site_dur[d]
        if dur=="WY":
            if (wy < 0) or (pd.isna(evs.loc[wy, "count"])):
                return
            fig, ax = plt.subplots(figsize=(6, 4))
            plt.title(wy)
            plt.ylabel('Flow ($ft^3$/s)')
            ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
            plt.xticks(rotation=90)
            dates = data.index[data["wy"]==wy]
            inflow = data.loc[dates,"flow"]
            plt.plot(dates, inflow, color='black',label="Daily Flow")
        else:
            idx_s = evs.loc[wy,"date"]
            idx_e = idx_s+dt.timedelta(days=dur-1)
            avg_flow = evs.loc[wy,"avg_flow"]
            plt.plot([idx_s,idx_s,idx_e,idx_e],[0,avg_flow,avg_flow,0],label=f"{dur}-day Flow",alpha=0.75)
    plt.legend()

def plot_wyvol(data,evs,wy_division,sel_wy=None):
    """
    This function produces a single plot of the WY with all WYs plotted as traces and the max, min, mean and median.
    :param data: df, inflows including at least date, flow
    :param evs: df, output from analyze_voldur() for WY
    :param wy_division: str, "WY" or "CY"
    :param sel_wy: list, selected WYs to plot colored traces for
    :return: figure
    """
    fig, ax = plt.subplots(figsize=(6, 4))
    plt.ylabel('Flow ($ft^3$/s)')
    ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
    ax.set_yscale("log")
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
        wy_len = len(data[data["wy"] == wy])
        doy = range(1,wy_len+1)
        doy_flow = data.loc[data["wy"]==wy,"flow"]
        doy_data.loc[doy,wy] = doy_flow.values
        plt.plot(doy, doy_flow, color="grey",alpha=0.5)
    for d in doy_data.index:
        doy_data.loc[d,"mean"] = doy_data.loc[d,WYs].mean()
        doy_data.loc[d, "median"] = doy_data.loc[d, WYs].median()

    # Plot min and max year, volume
    minwy = evs["annual_volume"].idxmin()
    plt.plot(doy_data.index,doy_data[minwy], color="maroon",label=f"Driest, {minwy}")
    maxwy = evs["annual_volume"].idxmax()
    plt.plot(doy_data.index, doy_data[2019], color="lime", label=f"Wettest, {maxwy}")

    if sel_wy is not None:
        sel_col = ["blue","orange","purple","cyan"]
        for sel in range(0,len(sel_wy)):
            plt.plot(doy_data.index, doy_data[sel_wy[sel]], color=sel_col[sel], linestyle="dashdot", label=f"{sel_wy[sel]}")

    plt.plot(doy_data.index, doy_data["mean"], color="black", linestyle="dashed", linewidth=2,label="Mean")
    plt.plot(doy_data.index, doy_data["median"], color="black", linestyle="solid",linewidth=2,label="Median")

    plt.xticks(rotation=90)
    plt.legend(prop={'size': 8})

    return(doy_data)

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

def plot_voldurpp(data,site_dur,durations,param,alpha=0):
    """
    This function produces the plots for all durations using plotting positions
    :param data: df, inflows including at least date, flow
    :param site_dur: list,
        contains dfs, output from analyze_voldur() for each duration listed in durations
    :param durations: list, durations to plot
    :param param: str, parameter to plot (e.g., "avg_flow")
    :param alpha: float, alpha value for plotting positions
    :return: figure
    """
    if not os.path.isdir("plot"):
        os.mkdir("plot")

    fig, ax = plt.subplots(figsize=(8, 6))
    plt.get_cmap("viridis")
    plt.ylabel('Flow ($ft^3/s$)')
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


        # calculate plotting positions
        if dur=="WY":
            continue
        else:
            peaks_sorted = calc_pp(evs[param],alpha)
            peaks_sorted.to_csv(f"plot/{dur}_pp.csv")
            plt.scatter(peaks_sorted.index,peaks_sorted[param],label=f"{dur}-day Flow")

            if peaks_sorted[param].min() < minp:
                minp = peaks_sorted[param].min()
            if peaks_sorted[param].max() > maxp:
                maxp = peaks_sorted[param].max()

    plt.ylim(minp,maxp)
    plt.legend()