# -*- coding: utf-8 -*-
"""
### CRITICAL DURATION FUNCTIONS ###
@author: tclarkin (USBR 2021)

This script contains the critical duration functions and pre-defined variables used in the duration analyses

"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import datetime as dt

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
    volumes.to_csv(f"critical/vw/{edate}_volumes.csv")

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

cfs_af = 24*60*60/43560

def route(hydro,start,rating):
    output = pd.DataFrame()
    start_af = interp(start,rating.FB,rating.AF)

    for i in hydro.index:
        inflow = output.loc[i,"q"] = hydro[i]

        # First timestep
        if i==0:
            output.loc[i,"fb"] = start
            output.loc[i,"af"] = start_af
            output.loc[i,"qd"] = interp(start,rating.FB,rating.QD)
        # Any other timestep
        else:
            output.loc[i, "af"] = output.loc[i-1, "af"]+(inflow-output.loc[i-1,"qd"])*cfs_af
            output.loc[i,"fb"] = interp(output.loc[i, "af"],rating.AF,rating.FB,2)
            output.loc[i,"qd"] = interp(output.loc[i,"fb"],rating.FB,rating.QD)

        # Check if lower than start, correct
        if output.loc[i, "af"]+(inflow-output.loc[i,"qd"])*cfs_af < start_af:
            output.loc[i, "qd"] = output.loc[i, "af"]/cfs_af+inflow-start_af/cfs_af

    return output


def analyze_cvhs_duration(data,evs,min_peak,hydro_dur,by,rating_file,start,plot=False):
    if min_peak == 0:
        print("Warning! Highly recommended a minumum peak be used for CVHS method!")

    # First, develop proxy curves
    var = data.columns[0]
    durations = range(1,hydro_dur+1,by)
    vol_table = pd.DataFrame()

    for dur in durations:
        # identify duration volumes
        df_dur = analyze_voldur(data,dur)
        # identify pp
        df_dur_pp = calc_pp(df_dur["avg_flow"])
        # select largest event, record pp
        vol_table.loc[dur,"pp"] = df_dur_pp.loc[0,"pp"]
        vol_table.loc[dur,"flow"] = df_dur_pp.loc[0,"avg_flow"]
    vol_table.to_csv("critical/cvhs/vol_table.csv")

    # Second, identify hydrographs
    evs_sel = evs.loc[evs["peak"] > min_peak]
    hydros = pd.DataFrame()
    for e in evs_sel.index:
        if evs_sel.loc[e,"duration"] != hydro_dur:
            shift = int(hydro_dur - evs_sel.loc[e,"duration"])
        elif evs_sel.loc[e,"duration"] == hydro_dur:
            shift = 0
        hydros.loc[:,evs_sel.loc[e,"start_idx"]] = data.loc[evs_sel.loc[e,"start_idx"]-dt.timedelta(days=np.floor(shift/3)):evs_sel.loc[e,"end_idx"]+dt.timedelta(days=np.ceil(2*shift/3)),var].reset_index(drop=True)
    hydros.to_csv("critical/cvhs/hydros.csv")

    # Third, define rating curve and check start
    rating = pd.read_csv(rating_file)
    if start < rating.FB.min() or start > rating.FB.max():
        print("Start outside of range of FB in rating file; please correct!")
        return

    # Fourth, begin analysis
    output = vol_table.copy()
    route_out = np.zeros((len(hydros.columns),hydro_dur,hydro_dur,4))
    for h,hydro in enumerate(hydros.columns):
        if plot:
            colors = ['#a6cee3','#1f78b4','#b2df8a','#33a02c','#fb9a99','#e31a1c','#fdbf6f','#ff7f00','#cab2d6','#6a3d9a','#ffff99','#b15928']
            while len(durations)>len(colors):
                colors=colors*2

            fig, ax = plt.subplots(figsize=(8, 3.5))
            plt.title = f"{hydro}"
            ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
            plt.ylabel('Flow (ft$^3$s)')
            plt.xlabel('Day')

        for d,dur in enumerate(durations):

            # create volume scaled hydrograph
            hydro_in = hydros.loc[:,hydro]
            hydro_vol = hydro_in.rolling(dur).mean()
            hydro_vol_max = hydro_vol.idxmax()
            hydro_scale = hydro_in.copy()

            vol = vol_table.loc[dur,"flow"]
            vr = vol/hydro_vol[hydro_vol_max]

            if dur>1:
                hydro_scale.loc[hydro_vol_max-dur+1:hydro_vol_max+1] = \
                    hydro_scale.loc[hydro_vol_max-dur+1:hydro_vol_max+1]*vr
            else:
                hydro_scale.loc[hydro_vol_max] = hydro_scale.loc[hydro_vol_max]*vr
            # route hydrograph
            routed = route(hydro_scale,start,rating)
            routed.to_csv(f"critical/cvhs/{hydro.year}_{dur}.csv")

            route_out[h,d,:,:] = np.array(routed)
            output.loc[dur,hydro.year] = route_out[h,d,:,1].max()

            if plot:
                if d==0:
                    inf_lab = "Inflow"
                    out_lab = "Outflow"
                else:
                    inf_lab = "_nolegend_"
                    out_lab = "_nolegend_"
                plt.plot(routed.q,color=colors[d],linestyle="solid",label=inf_lab)
                #plt.plot(routed.qd,color=colors[d],linestyle="dotted",label=out_lab)
        plt.plot(hydro_in,color="black",linestyle="dashed",linewidth=0.5,label='Raw Hydro')
        plt.legend()
        plt.savefig(f"critical/cvhs/{hydro.year}.jpg", dpi=300, bbox_inches="tight")
        plt.close()

    output.loc[:,"mean"] = output.iloc[:,2:].mean(axis=1)
    return(output)
