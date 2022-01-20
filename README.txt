Duration Analyses (v1)
@author: USBR (tclarkin 2021)

This script allows the user to conduct multiple daily flow data analyses.

The scripts have the following general workflow:
	1a_daily_data_prep -- can take user supplied daily flow data (.csv) or data from USGS, do simple deregulation (+/- another gage), and puts in a common format for all of the other scripts to use
	1b_peak_data_prep -- can take user supplied peak flow data (.csv) or data from USGS, and puts in a common format for all of the other scripts to use
	2a_flow_duration_analysis -- calculates flow duration curves (annual, monthly, all combinations, user-specified) and produces plots
	2b_flow_duration_multiplot -- produces a plot with multiple different annual curves (if multiple streams/locations are being analyzed)
	3_critical_duration_analysis -- allows user to conduct critical duration analysis by threshold or volume-window methods
	4a_volume duration_analysis -- finds annual maximum volume flows, plots each WY, plots traces of each WY
	4b_volume_duration_multiplot -- produces multiple initial data analysis plots (trends & shifts, autocorrelation, normality) and other useful plots (flow histogram, monthly distribution, plotted AMS)

All contributions will be licensed as Creative Commons Zero (CC0).