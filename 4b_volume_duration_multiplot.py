# -*- coding: utf-8 -*-
"""
Created on May 25 2021
Plot Volume Duration Script  (v1)
@author: tclarkin (USBR 2021)

This script aids in volume frequency analysis by plotting the data and, optionally, creating various timeseries and
thresholds for use in analysis.

This script can be run for all sites simultaneously
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from functions import plot_trendsshifts,plot_normality,plot_voldurpp,plot_voldurpdf,plot_voldurmonth
from statsmodels.graphics import tsaplots


### Begin User Input ###
os.chdir("C://Users//tclarkin//Documents//Projects//Roosevelt_Dam_IE//duration_analyses//")

# Site information and user selections
sites = ["TRD"] # list, site or dam names
durations = ["peak",1,4,10] # Duration in days
wy_division = "WY" # "WY" or "CY"
idaplot = True      # Will create initial data analysis plots (NOT DEVELOPED YET!)
ppplot = True       # Will create a plot with all durations plotted with plotting positions
pdfplot = True      # Plot probability density function of data
monthplot = True    # Plot monthly distribution of annual peaks
mixed = True        # Attempt to split mixed population with gaussian mixture
alpha = 0           # alpha for plotting positions

### Begin Script ###

# Check for output directory
if not os.path.isdir("volume"):
    print("No volume directory. Please run 4a_volume_duration_analysis.py before using this script")
if not os.path.isdir("plot"):
    os.mkdir("plot")

# Loop through sites
for site in sites:
    print(f"Analyzing {site}")
    site_dur = list()
    site_sum = pd.DataFrame()

    for dur in durations:
        df_dur = pd.read_csv(f"volume/{site}_{dur}.csv",index_col=0)
        df_dur["date"] = pd.to_datetime(df_dur["date"])
        df_dur = df_dur.dropna()
        site_dur.append(df_dur)

        site_sum.loc[dur,"N"] = len(df_dur)
        site_sum.loc[dur, "mean"] = df_dur.avg_flow.mean()
        site_sum.loc[dur, "median"] = df_dur.avg_flow.median()
        site_sum.loc[dur, "sd"] = df_dur.avg_flow.std()
        site_sum.loc[dur, "skew"] = df_dur.avg_flow.skew()
        site_sum.loc[dur, "log_mean"] = np.log10(df_dur.avg_flow).mean()
        site_sum.loc[dur, "log_median"] = np.log10(df_dur.avg_flow).median()
        site_sum.loc[dur, "log_sd"] = np.log10(df_dur.avg_flow).std()
        site_sum.loc[dur, "log_skew"] = np.log10(df_dur.avg_flow).skew()

    site_sum.to_csv(f"volume/{site}_stats_summary.csv")

    # Plot data
    if idaplot:
        print("Conducting initial data analysis...")
        # Check for output directory
        if not os.path.isdir("ida"):
            os.mkdir("ida")
        for d in range(0,len(durations)):
            evs = site_dur[d]
            dur = durations[d]
            print(f'{dur}...')

            # Check for trends and shifts
            plot_trendsshifts(evs,dur,"avg_flow")
            plt.savefig(f"ida/{site}_{dur}_trends&shifts_plot.jpg", bbox_inches="tight", dpi=300)

            # Check for autocorrelation
            fig = tsaplots.plot_acf(evs["avg_flow"], lags=20)
            fig.set_size_inches(6.25, 4)
            plt.ylabel("Autocorrelation")
            plt.xlabel("Lag K, in years")
            plt.savefig(f"ida/{site}_{dur}_acf_plot.jpg", bbox_inches="tight", dpi=300)

            # Check for normality
            plot_normality(evs,dur,"avg_flow")
            plt.savefig(f"ida/{site}_{dur}_normality_plot.jpg", bbox_inches="tight", dpi=300)

    if ppplot:
        print("Plotting with plotting positions")
        plot_voldurpp(site_dur,durations,"avg_flow",alpha)
        plt.savefig(f"plot/{site}_pp_plot.jpg", bbox_inches="tight", dpi=300)

    if pdfplot:
        print("Plotting with probability density function")
        plot_voldurpdf(site_dur,durations,"avg_flow")
        plt.savefig(f"plot/{site}_pdf_plot.jpg", bbox_inches="tight", dpi=300)

    if monthplot:
        print("Plotting with monthly distributions")
        plot_voldurmonth(site_dur,durations,"avg_flow","count",wy_division)
        plt.savefig(f"plot/{site}_month_count_plot.jpg", bbox_inches="tight", dpi=300)

        plot_voldurmonth(site_dur,durations,"avg_flow","mean",wy_division)
        plt.savefig(f"plot/{site}_month_mean_plot.jpg", bbox_inches="tight", dpi=300)

        plot_voldurmonth(site_dur,durations,"avg_flow","max",wy_division)
        plt.savefig(f"plot/{site}_month_max_plot.jpg", bbox_inches="tight", dpi=300)

    if mixed:
        if not os.path.isdir("mixed"):
            os.mkdir("mixed")

        from sklearn.mixture import GaussianMixture

        def GMM_sklearn(x, weights=None, means=None, covariances=None):
            model = GaussianMixture(n_components=2,
                                    covariance_type='full',
                                    tol=0.01,
                                    max_iter=1000,
                                    weights_init=weights,
                                    means_init=means,
                                    precisions_init=covariances)
            model.fit(x)
            print("\nscikit learn:\n\tphi: %s\n\tmu_0: %s\n\tmu_1: %s\n\tsigma_0: %s\n\tsigma_1: %s"
                  % (model.weights_[1], model.means_[0, :], model.means_[1, :], model.covariances_[0, :],
                     model.covariances_[1, :]))
            return model.predict(x), model.predict_proba(x)[:, 1]


        for dur, dat in zip(durations, site_dur):
            print(dur)
            x = np.reshape(dat.avg_flow.values, (len(dat), 1))
            sklearn_forecasts, posterior_sklearn = GMM_sklearn(x)

            dat["forecast"] = sklearn_forecasts
            dat.to_csv(f"mixed/{site}_{dur}_forecast.csv")