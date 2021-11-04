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
import os
import pandas as pd
import matplotlib.pyplot as plt
from functions import countdur,analyze_critdur,plot_standard_duration,plot_volwindow_duration
    
### Begin User Input ### 
# Set Working Directory
#os.chdir("C://Users//tclarkin//Documents//Projects//Anderson_Ranch_Dam//duration_analyses//")

# Site information and user selections
site = "ARD" # site or dam name
event_thresh = 2000    # threshold flow for defining flood events
min_dur = 0        # minumum duration acceptable for analysis
min_peak = 10000    # minumum duration acceptable for analysis
plot_max = 0       # maximum duration to show in peak vs duration plot (will use max if 0)

plot_events = True     # !!! Warning...better to wait until you run the first piece, because that will tell you how many plots this will produce (n = X)
buffer = 10
tangent = True

### Begin Script ###
# Check for output directory
if not os.path.isdir("critical"):
    os.mkdir("critical")

# Load data
data = pd.read_csv(f"data/{site}_site_daily.csv",parse_dates=True,index_col=0)

# Determine periods in excess of event threshold
print(f'Analyzing critical duration for events above {event_thresh} ft^3/s.')
evs = countdur(data,event_thresh)
analyze_critdur(evs,min_dur,min_peak,plot_max)
plt.savefig(f'critical/{site}_{str(event_thresh)}_p{str(min_peak)}_d{str(min_dur)}_peakvsdur.jpg',bbox_inches='tight',dpi=600)
evs.to_csv(f'critical/{site}_{str(event_thresh)}_p{str(min_peak)}_d{str(min_dur)}_peakvsdur.csv')

# Plot events
if plot_events:
    print("Plotting events")
    etot = len(evs.loc[evs["peak"]>min_peak].index)
    n = 0
    for e in evs.loc[evs["peak"]>min_peak].index:
        n += 1
        print(f'Plotting event {n} of {etot}')
        plot_standard_duration(data,evs,e,event_thresh,buffer,tangent)

        edate = evs.loc[e,"start_idx"].strftime("%Y-%m-%d")
        plt.savefig(f"critical/{site}_{edate}.jpg",bbox_inches='tight',dpi=600)
else:
    durationplot(data,evs,0,event_thresh)

