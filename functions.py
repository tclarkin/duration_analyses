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
def csv_daily_import(filename,wy="WY",single=True):
    """
    Imports data in a .csv files with two columns: date, variable (user specified)
    :param filename: str, filename or file path
    :param wy: str, "WY
    :return: dataframe with date index, dates, (user specified), month, year and water year
    """
    data = pd.read_csv(filename)
    if single:
        if len(data.columns) != 2:
            print("Two columns are needed! Exiting.")
            return
    data = data.rename(columns={data.columns[0]:"date"})
    vars = data.columns[1:len(data.columns)]
    for var in vars:
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
    out = out.merge(data[vars],left_index=True,right_index=True,how="left")

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

    data = pd.DataFrame()

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

### CRITICAL DURATION FUNCTIONS ###
def identify_thresh_events(data, thresh):
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

def init_duration_plot(evs,plot_max):
    """
    This function initializes plots for output from identify_thresh_events() by their peak and volume and calculates averages
    :param evs: df, output from identify_thresh_events()
    :param plot_max: int, maximum duration for plots
    :return: figure
    """
    # Plot peaks vs durations
    fig, ax = plt.subplots(figsize=(6.25, 4))
    plt.ylabel('Flow ($ft^3$/s)')
    plt.ylim(0,evs["peak"].max()*1.1)
    if (plot_max == 0) or (plot_max is None):
        plt.xlim(0.5, max(evs.duration)+0.5)
    else:
        plt.xlim(0.5, plot_max)
    ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
    plt.xlabel('Duration (days)')

def plot_and_calc_durations(evs, min_dur, min_peak,calc=False,scatter_label="Events",col="grey",fill="none"):
    """
    This function plots events defined by identify_thresh_events() by their peak and volume and calculates critical duration
    :param evs: df, output from identify_thresh_events()
    :param min_dur: int, user specified duration limit
    :param min_peak: int, user specified peak limit
    :param calc: str, False or str "arithmetic", "geometric", "peak-weight"
    :param scatter_label: str, label
    :param col: str, color for plotted data
    :param fill: str, fill color for plotted data
    :return: figure
    """
    # Check screening limits and plot
    if min_peak > 0:
        plt.plot((0, max(evs["duration"])+1),(min_peak,min_peak),color='blue',linestyle="dashed",label="Peak Limit")
        col = fill = "blue"
    if min_dur > 0:
        plt.plot((min_dur, min_dur), (0, max(evs["peak"])), color='red', linestyle="dashed", label="Duration Limit")
        col = fill = "red"
    if (min_peak > 0) & (min_dur > 0):
        col = fill = "purple"

    # Screen data
    print("Screening data...")
    evs_lim = evs.loc[(evs["duration"]>min_dur)&(evs["peak"]>min_peak)]
    lim_n = len(evs_lim)

    # Plot screened data
    plt.scatter(evs_lim["duration"],evs_lim["peak"],facecolors=fill,edgecolors=col,label=f"{scatter_label} (n={lim_n})")

    # Calculate averages
    if calc!=False:
        print("Calculating screened average...")
        if calc=="geometric":
            lim_dur_geo = (evs_lim["duration"].astype("float").prod()) ** (1 / lim_n)
            print(f"Screened G. Mean: {lim_dur_geo}")
            plt.plot([lim_dur_geo]*2, [0,evs["peak"].max()*1.1], color=col,linestyle="dashdot",alpha=0.75,label=f"Geometric Mean: {round(lim_dur_geo, 1)}")
        elif calc=="peak-weight":
            lim_dur_pw = sum(evs_lim["duration"] * evs_lim["peak"]) / sum(evs_lim["peak"])
            print(f"Peak Weighted Screened Mean: {lim_dur_pw}")
            plt.plot([lim_dur_pw]*2, [0,evs["peak"].max()*1.1], color=col,linestyle="dashdot",linewidth=2,alpha=0.75,label=f"Peak Weighted Mean: {round(lim_dur_pw, 1)}")
        else:
            lim_dur_avg = evs_lim["duration"].mean()
            print(f"Screened A. Mean: {lim_dur_avg}")
            plt.plot([lim_dur_avg]*2, [0,evs["peak"].max()*1.1], color=col,linestyle="dashdot",alpha=0.75,label=f"Arithmetic Mean: {round(lim_dur_avg, 1)}")


def plot_thresh_duration(data,evs,e,thresh,buffer=1,tangent=True):
    """
    This function produces the duration plots for all events provided
    :param data: df, data including at least date, variable
    :param evs: df, output from coutndur()
    :param e: int, the event index
    :param thresh: float, data value threshold
    :param buffer: int, number of days before/after for plots
    :param tangent: boolean, include cumulative flows and tangent on plots
    :return: figure
    """
    var = data.columns[0]
    xs = pd.date_range(evs.loc[e, "start_idx"] - dt.timedelta(days=buffer), evs.loc[e, "end_idx"] + dt.timedelta(days=buffer))
    indata = data.loc[xs, var]
    cum_indata = data.loc[xs, var]
    cum_outdata = data.loc[xs, var]

    # Calculate cumulatives
    if tangent:
        cum_indata[cum_indata.index<evs.loc[e, "start_idx"]] = 0
        for s in xs[xs>min(xs)]:
            cum_indata[s] = indata[s] + cum_indata[s - dt.timedelta(days=1)]

        tangency = cum_indata[evs.loc[e, "end_idx"]]
        cum_outdata[evs.loc[e, "end_idx"]] = tangency
        for s in xs[xs>evs.loc[e, "end_idx"]]:
            cum_outdata[s] = thresh + cum_outdata[s - dt.timedelta(days=1)]
        for s in reversed(xs[xs<evs.loc[e, "end_idx"]]):
            cum_outdata[s] = cum_outdata[s + dt.timedelta(days=1)] - thresh

    # Prepare plot
    plot_dur = range(1-buffer, evs.loc[e, "duration"] + buffer + 1)
    fig, ax = plt.subplots(figsize=(6.25, 4))
    plt.title("Event Beginning " + evs.loc[e, "start_idx"].strftime("%d-%b-%Y") + " | Duration: " + str(
        evs.loc[e, "duration"]) + " days")
    ylab = get_varlabel(var)
    varname = ylab.split(" ")[0]
    ymax = round(max(cum_outdata), -4) + 10000
    plt.ylim(0, ymax)
    ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
    plt.xlabel('Duration (days)')
    plt.xlim(min(plot_dur), max(plot_dur))

    # Plot data
    plt.bar(plot_dur, indata, width=1,color='blue',alpha=0.5,label="_nolegend_")
    plt.plot(plot_dur, indata, 'blue',label=varname)
    plt.plot(plot_dur, [thresh] * len(plot_dur), 'red', label="Event Threshold")

    if tangent:
        plt.plot(plot_dur, cum_indata, "black",label=f"Cum. {varname}")
        plt.plot(plot_dur, cum_outdata, color='maroon',linestyle="dashed",label="Cum. Threshold Flow")
        plt.plot(evs.loc[e, "duration"],tangency,"rx",label="Point of Tangency")
        ylab = f"{ylab} | Cumulative {ylab} ($ft^3$/s days)"

    # Plot duration window
    plt.plot([0]*2,[0,ymax],color="r",linestyle="dashed",linewidth=0.5,label="Duration Window")
    plt.plot([max(plot_dur)-buffer]*2,[0,ymax],color="r",linestyle="dashed",linewidth=0.5,label="_nolegend_")

    plt.ylabel(ylab)
    plt.legend()

def analyze_volwindow_duration(data,evs,e,resdat,buffer=1,plot=True):
    """
    This function produces volume-window plots as used for the Folsom WCM
    :param data: df, data including at least date, variable
    :param evs: df, output from coutndur()
    :param e: int, the event index
    :param resdat: df, data including at least date, QD, AF
    :param timestep: int, number of days for each timestep to use for analyzing duration
    :return: evs2
    """
    # Find max storage
    vol_peak_idx = resdat.loc[evs.loc[e,"start_idx"]:evs.loc[e,"end_idx"],"AF"].idxmax()
    vol_peak_dur = (vol_peak_idx-evs.loc[e,'start_idx']).days+1

    # Find duration, based on date of max storage
    duration = evs.loc[e,"duration"]
    windows = list()
    timestep = 1

    # Define durations to analyze
    ts = timestep
    windows.append(ts)
    while ts+timestep <= duration-timestep:
        ts = ts + timestep
        windows.append(ts)
    windows.append(duration)

    # Calculate inflow volumes for windows:
    var = data.columns[0]
    volumes = pd.DataFrame()

    for w in windows:
        dur_data = data.loc[evs.loc[e,"start_idx"]:evs.loc[e,"end_idx"],var].rolling(w, min_periods=w).sum()*(24*60*60)/43560
        try:
            max_idx = dur_data.idxmax()
        except ValueError:
            continue
        if pd.isna(max_idx):
            continue

        volumes.loc[w,"start"] = max_idx - dt.timedelta(days=w - 1)  # place date as start of window
        volumes.loc[w,"end"] = max_idx  # place date as end of window
        volumes.loc[w, "avg"] = data.loc[volumes.loc[w,"start"]:volumes.loc[w,"end"],var].mean()
        volumes.loc[w,"vol"] = round(dur_data[max_idx], 0)
        volumes.loc[w, "vol_peak"] = round(data.loc[volumes.loc[w, "start"]:vol_peak_idx, var].sum() * (24 * 60 * 60) / 43560, 0)
        volumes.loc[w, "vw"] = volumes.loc[w, "vol_peak"] / volumes.loc[w,"vol"]


    crit_dur = abs(volumes["vw"]-1).idxmin()
    edate = evs.loc[e, "start_idx"].strftime("%Y-%m-%d")
    volumes.to_csv(f"critical/{edate}_volumes.csv")

    # Plot event
    if plot:
        xs = pd.date_range(evs.loc[e, "start_idx"] - dt.timedelta(days=buffer),
                           evs.loc[e, "end_idx"] + dt.timedelta(days=buffer+5))
        inflow = data.loc[xs, var]
        storage = resdat.loc[xs, "AF"]
        outflow = resdat.loc[xs, "QD"]

        # Prepare plot
        fig, ax1 = plt.subplots(figsize=(6.25, 4))
        plt.title("Event Beginning " + evs.loc[e, "start_idx"].strftime("%d-%b-%Y") + " | Duration: " + str(
            crit_dur) + " days")
        ylab = get_varlabel(var)

        ax1.set_ylabel(ylab)
        ax1.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
        ax1.set_xticklabels(ax1.get_xticklabels(), rotation = 15)

        # Plot flow data
        ax1.plot(xs, inflow, 'blue', label=f"Inflow ({duration}-days)")
        ax1.plot(xs, outflow, 'red', linestyle="dashed", label="Outflow")

        # Plot volume data
        ax2 = ax1.twinx()
        ax2.plot(xs, storage, 'green', label="Storage (acre-feet)")
        ax2.plot([vol_peak_idx]*2,[0,resdat.loc[vol_peak_idx,"AF"]*1.1],"black",linestyle="dashed",label=f"Storage Peak ({vol_peak_dur}-days)")
        ax2.set_ylabel("Storage (acre-feet)")
        ax2.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))

        volumes_plot = list()
        for i in [1,5,10,25,50,75,100,125,150,175,200]:
            if i in volumes.index:
                volumes_plot.append(i)
        if crit_dur not in volumes_plot:
            near = [x for x in volumes_plot if abs(x-crit_dur)<5]
            for n in near:
                volumes_plot.remove(n)
            volumes_plot.append(crit_dur)

        for w in volumes_plot:
            if w==crit_dur:
                alp = 1
                col = str(0)
            else:
                alp = max(1-abs(volumes.loc[w,"vw"]-1)*2,0.25)
                col = str(0)

            ax1.plot([volumes.loc[w,"start"],volumes.loc[w,"end"]],[volumes.loc[w,"avg"]]*2, color=col, alpha=alp, label="_nolegend_")
            ax1.annotate(f"{w}-days: {round(volumes.loc[w,'vw'],2)}",[volumes.loc[w,"end"],volumes.loc[w,"avg"]], alpha=alp,color=col)

        ax2.legend(loc="upper right")
        ax1.legend(loc="upper left")

    return crit_dur


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
                    evs.loc[wy, "annual_sum"] = round(data.loc[data["wy"] == wy, var].sum(), 0)
                    evs.loc[wy, "annual_acft"] = round(data.loc[data["wy"] == wy, var].sum() * 86400 / 43560, 0)
                    evs.loc[wy, "count"] = len(data.loc[data["wy"]==wy, var])
                    max_idx = data.loc[data["wy"] == wy, var].idxmax()
                    evs.loc[wy, "max"] = max_idx
                    evs.loc[wy, f"max_{var}"] = round(data.loc[max_idx, var], 0)
    else:
        dur_data = data[var].rolling(dur,min_periods=int(np.ceil(dur*0.90))).mean()
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
                evs.loc[wy, "max"] = data.loc[evs.loc[wy, "start"]:evs.loc[wy, "end"],var].idxmax()
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
        if theil[0]<1:
            theil_slope = round(theil[0],1)
        else:
            theil_slope = round(theil[0],0)
        plt.plot(evs.index,evs.index*theil[0]+theil[1],"r--",label=f'Theil Slope = {theil_slope} \n (Kendall Tau p-value = {round(kendall.pvalue,3)})')

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
    if var in ["flow","Flow","discharge","Discharge","inflow","Inflow","IN","Q","QU","cfs","CFS"]:
        lab = "Flow (ft$^3$/s)"
    elif var in ["peak", "Peak", "peaks", "Peaks","peak discharge","Peak Discharge"]:
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