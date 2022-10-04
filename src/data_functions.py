# -*- coding: utf-8 -*-
"""
### DATA PREP FUNCTIONS ###
@author: tclarkin (USBR 2022)

This script contains the data preparation functions and pre-defined variables used in the duration analyses 1a and b

"""
import dataretrieval.nwis as nwis
import pandas as pd
import numpy as np
import datetime as dt

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
    out["doy"] = pd.DatetimeIndex(out.index).dayofyear
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
    out["doy"] = pd.DatetimeIndex(out.index).dayofyear
    out["year"] = pd.DatetimeIndex(out.index).year
    out["month"] = pd.DatetimeIndex(out.index).month
    out["wy"] = out["year"]
    if wy=="WY":
        out.loc[out["month"] >= 10, "wy"] = out.loc[out["month"] >= 10, "year"] + 1

    return(out)

def import_daily(site_source,wy_division,clean=False,zero=False):
    if ".csv" in site_source:
        # Load from .csv file
        site_daily = csv_daily_import(site_source, wy=wy_division)
        var = site_daily.columns[0]  # infer variable by column name
    else:
        # Load from usgs website
        if len(site_source) != 8:
            print("Must provide valid USGS site number (8-digit string) for at-site data")
        else:
            site_daily = nwis_import(site=site_source, dtype="dv", wy=wy_division)
            var = "flow"

    # Clean data, if selected
    if clean:
        # Remove negative values
        if zero != "average":
            site_daily.loc[site_daily[var] < zero, var] = zero
        else:
            site_rolling = site_daily.rolling(3, center=True).mean()
            site_daily.loc[site_daily[var] < 0, var] = site_rolling

    # Summarize data
    summary = pd.DataFrame()
    summary.loc["all","start"] = site_daily.index.min()
    summary.loc["all","end"] = site_daily.index.max()
    summary.loc["all","count"] = site_daily[var].count()
    summary.loc["all","max"] = site_daily[var].max()
    summary.loc["all","min"] = site_daily[var].min()
    summary.loc["all","mean"] = site_daily[var].mean()
    summary.loc["all","median"] = site_daily[var].median()
    for wy in site_daily["wy"].unique():
        wy_daily = site_daily.loc[site_daily["wy"] == wy]
        summary.loc[wy, "start"] = wy_daily.index.min()
        summary.loc[wy, "end"] = wy_daily.index.max()
        summary.loc[wy, "count"] = wy_daily[var].count()
        summary.loc[wy, "max"] = wy_daily[var].max()
        summary.loc[wy, "min"] = wy_daily[var].min()
        summary.loc[wy, "mean"] = wy_daily[var].mean()
        summary.loc[wy, "median"] = wy_daily[var].median()
    return site_daily,summary

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
        out["doy"] = pd.DatetimeIndex(out.index).dayofyear
        out["year"] = pd.DatetimeIndex(out.index).year
        out["month"] = pd.DatetimeIndex(out.index).month
        out["wy"] = out["year"]
        if wy == "WY":
            out.loc[out["month"] >= 10, "wy"] = out.loc[out["month"] >= 10, "year"] + 1

        out = out.reset_index(drop=False)
        out.index = out.wy
        out = out.drop(["year", "wy"], axis=1)

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
    out["date"] = pd.DatetimeIndex(out.index).date
    out["peak"] = data.peak_va

    # Add year, month and wy
    out["doy"] = pd.DatetimeIndex(out.index).dayofyear
    out["year"] = pd.DatetimeIndex(out.index).year
    out["month"] = pd.DatetimeIndex(out.index).month
    out["wy"] = out["year"]
    out.loc[out["month"] >= 10, "wy"] = out.loc[out["month"] >= 10, "year"] + 1

    out = out.reset_index(drop=True)
    out.index = out.wy

    out = out.drop(["year","wy"],axis=1)

    return(out)

def import_peaks(site_source):
    if ".csv" in site_source:
        # Load from .csv file
        site_peaks = csv_peak_import(site_source)
        var = site_peaks.columns[1]
    else:
        # Load from usgs website
        if len(site_source) != 8:
            print("Must provide valid USGS site number (8-digit string) for at-site data")
        else:
            site_peaks = nwis_peak_import(site=site_source)
            var = "peak"

    return site_peaks,var


def season_subset(data,season_idx,var):
    """
    Function to screen out data by season
    :param data: df, input data with at least var,month,doy
    :param season_idx: list, either months (cy) or [min,max] doy (cy)
    :return: df, seasonal data
    """
    data = data.copy()
    # If all values are < 12; assume to be months
    if max(season_idx) <= 12:
        data.loc[~data["month"].isin(season_idx), var] = np.nan
    # Else, if only two values are given; assume to be DOYs [S,F]
    elif len(season_idx) == 2:
        data.loc[data["doy"] < season_idx[0], var] = np.nan
        data.loc[data["doy"] > season_idx[1], var] = np.nan
    else:
        print("Format of season not recognized. Please provide a list of months (CY) or start and end day of year (CY)")
    return data


