# -*- coding: utf-8 -*-
"""
Created on May 25 2021
Critical Duration Script  (v4)
@author: tclarkin (USBR 2021)

This script analyzes user supplied continuous daily records using a user supplied threshold (event_thresh). The
threshold is used to define a partial duration series (PDS) and calculate durations (time above the threshold).
Critical duration is then estimated as the peak weighted, arithmetic, and geometric average of the durations from the
PDS. The user also has the option to specify duration or peak limits (min_dur and min_peak, respectively), if it is
desired to screen out events below the specified limits:

- If no limits are set, the peak weighted and arithmetic averages of duration will be calculated on the full PDS
- If a duration and/or peak limit is set, the averages will be calculated on the screened population

The user can specify if they want individual events plotted (plot_event). If selected, a duration plot will be created
for each screened event. If not selected, only the very first event will be plotted, but not saved.

The user can specify if they want to check the annual pattern (check_annual_pattern). If selected, all events
(regardless of user specified limits) will be plotted by month.

This script should be run individually for each site being analyzed--should be iterative.

"""
import pandas as pd
import matplotlib.pyplot as plt
from src.functions import check_dir
from src.data_functions import csv_daily_import
from src.crit_functions import identify_thresh_events,init_duration_plot,plot_and_calc_durations,plot_thresh_duration,analyze_cvhs_duration,analyze_volwindow_duration

### Begin User Input ###
# Set Working Directory
#os.chdir("")

# Site information and user selections
site = "06468170" # site (cannot handle seasonal)
season = "spring" # False or season name
event_thresh = 4500 # threshold flow for defining flood events
min_dur = None      # minimum duration acceptable for analysis (or None)
min_peak = 30000   # minimum duration acceptable for analysis (or None)
plot_max = 0        # maximum duration to show in peak vs duration plot (will use max if 0)
mean_type = "arithmetic" # "arithmetic", "geometric", "peak-weight"

# Standard Duration
analyze_standard = True
standard_plots = False     # !!! Warning...better to wait until you run the first piece, because that will tell you how many plots this will produce (n = X)
buffer = 5                 # int, number of days before and after duration to plot
tangent = False              # boolean, including cumulative flows and tangent line

# Volume-Window Duration
analyze_volwindow = False    # Analyze using volume-window method
volwindow_plots = True     # !!! Warning...better to wait until you run the first piece, because that will tell you how many plots this will produce (n = X)
res_file = "daily_res.csv"  # .csv filename or None. If file, QD (discharge) and AF (storage) are expected.

# CVHS Duration
analyze_cvhs = False
cvhs_plots = True            # include plots...
hydro_dur = 30               # max duration to analyze
by = 1
rating_file = "rating.csv"   # .csv file. If file, FB (elevation), QD (discharge), AF (storage) expected
start = 220.5                # must be in rating_file

### Begin Script ###
# Check for output directory
outdir = check_dir(site,"critical")
threshdir = check_dir(outdir,"thresh")

# Load data

if season == "all" or season == False:
    s = ""
else:
    s = f"_{season}"

data = pd.read_csv(f"{site}/data/{site}{s}_site_daily.csv",parse_dates=True,index_col=0)

# Determine periods in excess of event threshold
print(f'Analyzing critical duration for events above {event_thresh} ft^3/s.')
evs = identify_thresh_events(data,event_thresh)

if analyze_standard:
    print("Using standard method...")
    # Check thresholds
    if min_peak is None:
        min_peak = 0
    if min_dur is None:
        min_dur = 0

    # Intialize figure
    init_duration_plot(evs,plot_max)

    # Plot all data
    if (min_dur==0) and (min_peak==0):
        plot_and_calc_durations(evs,0,0,mean_type)
    else:
        plot_and_calc_durations(evs, 0, 0)
    # Plot screened data
    if (min_dur>0) or (min_peak>0):
        plot_and_calc_durations(evs,min_dur,min_peak,mean_type,"Screened Events")

    # Add title and legend, and save
    plt.title(f"Flow vs Duration")
    ax = plt.gca()
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.9, box.height])
    plt.legend(bbox_to_anchor=(1, 0.5), loc='center left', prop={'size': 10})
    plt.savefig(f'{threshdir}/{site}_{str(event_thresh)}_p{str(min_peak)}_d{str(min_dur)}_peakvsdur.jpg',bbox_inches='tight',dpi=300)
    evs.to_csv(f'{threshdir}/{site}_{str(event_thresh)}_p{str(min_peak)}_d{str(min_dur)}_peakvsdur.csv')

    # Selected events
    evs_sel = evs.copy(deep=True)
    evs_sel = evs_sel.loc[evs["peak"] > min_peak]
    etot = len(evs_sel.index)
    evs_sel.to_csv(f'{threshdir}/{site}_{str(event_thresh)}_p{str(min_peak)}_d{str(min_dur)}_peakvsdur_selected.csv')

# Create standard event plots
if standard_plots:
    print("Plotting events")
    for n,e in zip(range(1,len(evs_sel)+1),evs_sel.index):
        print(f'Plotting event {n} of {etot}')
        plot_thresh_duration(data,evs_sel,e,event_thresh,buffer,tangent)

        edate = evs_sel.loc[e,"start_idx"].strftime("%Y-%m-%d")
        plt.savefig(f"{threshdir}/{site}_thresh_{edate}.jpg",bbox_inches='tight',dpi=300)

# Analyse by volume-window method
if analyze_volwindow:
    print("Beginning Volume Window Duration Analysis")
    vwdir = check_dir(outdir,"vw")

    if res_file is None:
        print("No reservoir information file (res_file) provided. Volume-Window Plots not created.")
    else:
        # Import reservoir data
        resdat = csv_daily_import(res_file,"WY",False)
        # Create volume-window plots
        print("Analyzing events with Volume-Window Method")
        for n,e in zip(range(1,len(evs_sel)+1),evs_sel.index):
            if evs_sel.loc[e,"start_idx"]<resdat.index.min():
                print(f'Skipping event {n} of {etot}')
                evs_sel = evs_sel.drop(e)
                continue
            else:
                print(f'Analyzing event {n} of {etot}')
                crit = analyze_volwindow_duration(data,evs_sel,e,resdat,buffer,volwindow_plots)
                evs_sel.loc[e,"duration"] = crit
                if volwindow_plots:
                    edate = evs_sel.loc[e, "start_idx"].strftime("%Y-%m-%d")
                    plt.savefig(f"{vwdir}/{site}_volwindow_{edate}.jpg",bbox_inches='tight',dpi=300)

        # Save data
        evs_sel.to_csv(f'{vwdir}/{site}_{str(event_thresh)}_p{str(min_peak)}_d{str(min_dur)}_peakvsdur_volwindow.csv')

        # Summarize duration information
        # Intialize figure
        init_duration_plot(evs, plot_max)
        # Replot all data
        plot_and_calc_durations(evs, 0, 0)
        # Plot screened data
        if (min_dur > 0) or (min_peak > 0):
            plot_and_calc_durations(evs,min_dur,min_peak,mean_type,"Screened Events")

        # Plot volume-window durations
        plot_and_calc_durations(evs_sel,0,0,mean_type,"Volume-Window Events","black","black")

        # Add title and legend and save
        plt.title(f"Flow vs Duration")
        ax = plt.gca()
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.9, box.height])
        plt.legend(bbox_to_anchor=(1, 0.5), loc='center left', prop={'size': 10})

        plt.savefig(f'{vwdir}/{site}_{str(event_thresh)}_p{str(min_peak)}_d{str(min_dur)}_peakvsdur_volwindow.jpg',
                bbox_inches='tight', dpi=300)

# Analyze CVHS Critical Duration
if analyze_cvhs:
    print("Beginning CVHS Duration Analysis")
    cvhsdir = check_dir(outdir,"cvhs")

    # Analyze
    cvhs = analyze_cvhs_duration(data,evs,min_peak,hydro_dur,by,rating_file,start,cvhs_plots)
    cvhs.to_csv(f"{cvhsdir}/{site}_{str(event_thresh)}_p{str(min_peak)}_d{str(min_dur)}_cvhs.csv")

    # Plot results
    fig, ax = plt.subplots(figsize=(8, 3.5))
    plt.title = f"CVHS Duration"
    plt.xlabel("Duration")
    plt.ylabel("Max Stage")
    for h in cvhs.iloc[:,2:].columns:
        if h=="mean":

            plt.plot(cvhs[h],label=h,color="black",linestyle="dashed")
            plt.plot([cvhs[h].idxmax()]*2,[cvhs[h].min(),cvhs[h].max()],color="black",linestyle="dashed",label=f"Mean Crit. Duration ({cvhs[h].idxmax()}-days)")
        else:
            plt.plot(cvhs[h],label=h)

    plt.legend()
    plt.savefig(f"{cvhsdir}/{site}_{str(event_thresh)}_p{str(min_peak)}_d{str(min_dur)}_cvhs.jpg")

print("Script 3 Complete")