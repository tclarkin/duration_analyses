# -*- coding: utf-8 -*-
"""
Created on May 25 2021
Critical Duration Script  (v4)
@author: tclarkin (USBR 2021)

This script analyzes user supplied continuous daily inflows (Ifile) using a
user supplied threshold (event_thresh). The threshold is used to define a 
partial duration series (PDS) and calculate durations (time above the 
threshold). Critical duration is then estimated as the peak weighted and 
arithmetic average of the durations from the PDS. The user also has the option 
to specify duration or peak limits (min_dur and min_peak, respectively), if it 
is desired to screen out events below the specified limits:

- If no limits are set, the peak weighted and arithmetic averages of duration 
will be calculated on the full population of events
- If a duration and/or peak limit is set, the peak weighted and arithmetic 
averages of duration will be calculated on the screened population

The user can specify if they want individual events plotted (plot_event). If 
selected, a duration plot will be created for each screened event. If not
selected, only the very first event will be plotted, but not saved.

The user can specify if they want to check the annual pattern (check_annual_pattern).
If selected, all events (regardless of user specified limits) will be plotted
by month.

The user must:
    - Identify the current directory
    - Provide the dam name (dam)
    - Define the following: event_thresh (num), plot_event (bool), 
    check_annual_pattern (bool), min_dur (int) and min_peak (num)

"""
import os
import pandas as pd
import matplotlib.pyplot as plt
from functions import countdur,analyze_critdur,analyze_monthlydur,analyze_monthlypeak,durationplot
    
### Begin User Input ### 
# Set Working Directory
os.chdir("C://Users//tclarkin//Documents//Projects//Roosevelt_Dam_IE//duration_analyses//")

# Site information and user selections
site = "TRD" # site or dam name
event_thresh = 11657    # threshold flow for defining flood events
plot_events = True     # !!! Warning...better to wait until you run the first piece, because that will tell you how many plots this will produce (n = X)
check_annual_pattern = True
min_dur = 0        # minumum duration acceptable for analysis
min_peak = 30000   # minumum duration acceptable for analysis
plot_max = 0       # maximum duration to show in peak vs duration plot (will use max if 0)

### Begin Script ###
# Load inflows
data = pd.read_csv(f"{site}_site_data.csv",parse_dates=True,index_col=0)

# Check for output directory
if not os.path.isdir("critical"):
    os.mkdir("critical")

# Determine flows in excess of event threshold
print('Analyzing critical duration for events above {} ft^3/s.'.format(event_thresh))
evs = countdur(data,event_thresh)
analyze_critdur(evs,min_dur,min_peak,plot_max)
plt.savefig(f'critical/{site}_{str(event_thresh)}_p{str(min_peak)}_d{str(min_dur)}_peakvsdur.jpg',bbox_inches='tight',dpi=300)
evs.to_csv(f'critical/{site}_{str(event_thresh)}_p{str(min_peak)}_d{str(min_dur)}_peakvsdur.csv')

if plot_events:
    print("Plotting events")
    etot = len(evs.loc[evs["peak"]>min_peak].index)
    n = 0
    for e in evs.loc[evs["peak"]>min_peak].index:
        n += 1
        print('Plotting event {} of {}'.format(n,etot))
        durationplot(data,evs,e,event_thresh)

        edate = evs.loc[e,"start_idx"].strftime("%Y-%m-%d")
        plt.savefig(f"critical/{site}_{edate}.jpg",bbox_inches='tight',dpi=300)
else:
    durationplot(data,evs,0,event_thresh)
    
if check_annual_pattern:
    print("Plotting annual pattern")
    monthdur = analyze_monthlydur(evs)
    plt.savefig(f"critical/{site}_{str(event_thresh)}_dur_seasonality.jpg",bbox_inches="tight",dpi=300)
    monthdur.to_csv(f'critical/{site}_{str(event_thresh)}_p{str(min_peak)}_d{str(min_dur)}_dur_monthlystats.csv')

    monthpeak = analyze_monthlypeak(evs)
    plt.savefig(f"critical/{site}_{str(event_thresh)}_peak_seasonality.jpg",bbox_inches="tight",dpi=300)
    monthpeak.to_csv(f'critical/{site}_{str(event_thresh)}_p{str(min_peak)}_d{str(min_dur)}_peak_monthlystats.csv')
