# -*- coding: utf-8 -*-
"""
### DATA PREP FUNCTIONS ###
@author: tclarkin (USBR 2022)

This script contains the data preparation functions and pre-defined variables used in the duration analyses 1a and b

"""
import dataretrieval.nwis as nwis
import dataretrieval as dr
import pandas as pd
import numpy as np
import datetime as dt
from requests import get as r_get
from io import StringIO
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
        except [ValueError,dr.utils.NoSitesError] as error:
            data["flow"] = np.nan
    else:
        if (start==None) & (end==None):
            try:
                data = nwis.get_record(sites=site, start="1800-01-01",service=dtype, parameterCd='00060')
            except [ValueError, dr.utils.NoSitesError] as error:
                data["flow"] = np.nan
        else:
            if end==None:
                try:
                    data = nwis.get_record(sites=site, start=start, end="3000-01-01", service=dtype, parameterCd='00060')
                except [ValueError, dr.utils.NoSitesError] as error:
                    data["flow"] = np.nan
            if start==None:
                try:
                    data = nwis.get_record(sites=site, start="1800-01-01", end=end, service=dtype, parameterCd='00060')
                except [ValueError, dr.utils.NoSitesError] as error:
                    data["flow"] = np.nan
    try:
        data.index = pd.to_datetime(data.index,utc=True)
    except ValueError:
        print("Unable to convert to datetime")

    data = data.tz_localize(None)
    end = data.index.max()
    start = data.index.min()

    if dtype == "dv":
        date_index = pd.date_range(start, end, freq="D")
    elif dtype == "iv":
        if start==end:
            end = dt.datetime.strftime((dt.datetime.strptime(start,"%Y-%m-%d") + dt.timedelta(hours=24)),"%Y-%m-%d")
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


# Define functions
def snotel_import(site_triplet,vars=["WTEQ", "SNWD", "PREC", "TAVG"],wy="WY",verbose=False):
    """Download NRCS SNOTEL data

    Parameters
    ---------
        site_triplet: three part SNOTEL triplet (e.g., 713_CO_SNTL)
            https://wcc.sc.egov.usda.gov/nwcc/yearcount?network=sntl&counttype=statelist&state=
        vars: array of variables for import (tested with WTEQ, SNWD, PREC, TAVG..other options may be available)
        out_dir: str to directory to save .csv...if None, will return df
        verbose: boolean
            True : enable print during function run

    Returns
    -------
        dataframe

    """
    # Create dictionary of variables
    snotel_dict = dict()
    ext = "DAILY"

    # Cycle through variables
    for var in vars:
        if verbose == True:
            print("Importing {} data".format(var))
        site_url = "https://www.nrcs.usda.gov/Internet/WCIS/sitedata/" + ext + "/" + var + "/" + site_triplet + ".json"
        if verbose == True:
            print(site_url)
        failed = True
        tries = 0
        while failed:
            try:
                csv_str = r_get(site_url, timeout=1,verify=False).text
                failed = False
            except ConnectionError:
                raise Exception("Timeout; Data unavailable?")
                tries += 1
                print(tries)
                if tries > 10:
                    return

            if "not found on this server" in csv_str:
                print("Site URL incorrect.")
                return

        csv_io = StringIO(csv_str)
        f = pd.read_json(csv_io, orient="index")

        # Create index of dates for available data for current site
        json_index = pd.date_range(f.loc["beginDate"].item(), f.loc["endDate"].item(), freq="D", tz='UTC')
        # Create dataframe of available data (includes Feb 29)
        json_data = pd.DataFrame(f.loc["values"].item())
        # Cycle through and remove data assigned to February 29th in non-leap years
        years = json_index.year.unique()
        for year in years:
            if (year % 4 == 0) & ((year % 100 != 0) | (year % 400 == 0)):
                continue
            else:
                feb29 = dt.datetime(year=year, month=3, day=1, tzinfo=dt.timezone.utc)
                try:
                    feb29idx = json_index.get_loc(feb29)
                    if feb29idx == 0:
                        continue
                    else:
                        json_data = json_data.drop(feb29idx)
                        if verbose == True:
                            print("February 29th data for {} removed.".format(year))
                except KeyError:
                    continue

        # Concatenate the cleaned data to the date index
        snotel_in = pd.DataFrame(index=json_index)
        snotel_in[var] = json_data.values

        # For precip, calculate incremental precip and remove negative values
        if var == "PREC":
            if verbose == True:
                print("Calculating incremental Precip.")
            snotel_in["PREC"] = snotel_in[var] - snotel_in[var].shift(1)
            snotel_in.loc[snotel_in["PREC"] < 0, "PREC"] = 0

        # Add to dict
        snotel_dict[var] = snotel_in

    if verbose == True:
        print("Checking dates")
    begin = end = pd.to_datetime(dt.datetime.now()).tz_localize("UTC")
    for key in snotel_dict.keys():
        if snotel_dict[key].index.min() < begin:
            begin = snotel_dict[key].index.min()
        if snotel_dict[key].index.max() > end:
            end = snotel_dict[key].index.max()

    dates = pd.date_range(begin,end,freq="D",tz='UTC')
    out = pd.DataFrame(index=dates)

    if verbose == True:
        print("Preparing output")
    for key in snotel_dict.keys():
        # Merge to output dataframe
        snotel_in = out.merge(snotel_dict[key][key], left_index=True, right_index=True, how="left")
        out[key] = snotel_in[key]
        if verbose == True:
            print("Added to dataframe")

    # Add year, month and wy
    out["doy"] = pd.DatetimeIndex(out.index).dayofyear
    out["year"] = pd.DatetimeIndex(out.index).year
    out["month"] = pd.DatetimeIndex(out.index).month
    out["wy"] = out["year"]
    if wy=="WY":
        out.loc[out["month"] >= 10, "wy"] = out.loc[out["month"] >= 10, "year"] + 1

    return out

def import_hydromet(site,var,region,wy="WY",verbose=False):
    if region=="CPN" or region=="cpn":
        today = dt.datetime.today()

        # Cycle through variables
        if verbose == True:
            print(f"Importing {var} data")
        site_url = f"https://www.usbr.gov/pn-bin/daily.pl?station={site}&format=html&year={1900}&month={10}&day={1}&year={today.year}&month={today.month}&day={today.day}&pcode={var}"
        if verbose == True:
            print(site_url)
        failed = True
        tries = 0
        while failed:
            try:
                csv_str = r_get(site_url, timeout=10, verify=False).text
                failed = False
            except ConnectionError:
                raise Exception("Timeout; Data unavailable?")
                tries += 1
                print(tries)
                if tries > 10:
                    return
            if "not found on this server" in csv_str:
                print("Site URL incorrect.")
                return
        csv_io = StringIO(csv_str)
        f = pd.read_html(csv_io,flavor="lxml",parse_dates=True,index_col=0)

        # Fix if list
        if isinstance(f,list):
            hydro_in = f[0]
        else:
            hydro_in = f

        # Fix variable name
        var = hydro_in.columns[0].split("_")[1]
        hydro_in.columns = [var]

        # Check for start and end dates
        hydro_in_true = hydro_in[hydro_in[var].notna()==True].index
        begin = hydro_in_true.min()
        end = hydro_in_true.max()
        hydro_in = hydro_in.loc[begin:end]

        dates = pd.date_range(begin, end, freq="D")
        out = pd.DataFrame(index=dates)

        out = out.merge(hydro_in[var], left_index=True, right_index=True, how="left")

        # Add year, month and wy
        out["doy"] = pd.DatetimeIndex(out.index).dayofyear
        out["year"] = pd.DatetimeIndex(out.index).year
        out["month"] = pd.DatetimeIndex(out.index).month
        out["wy"] = out["year"]
        if wy == "WY":
            out.loc[out["month"] >= 10, "wy"] = out.loc[out["month"] >= 10, "year"] + 1

        return out

def import_daily(site_source,wy_division,clean=False,zero=False):
    if isinstance(site_source,list):
        # Load hydromet data
        site = site_source[0]
        var = site_source[1]
        region = site_source[2]
        site_daily = import_hydromet(site,var,region,wy_division)
        var = site_daily.columns[0]
    elif ".csv" in site_source:
        # Load from .csv file
        site_daily = csv_daily_import(site_source, wy=wy_division)
        var = site_daily.columns[0]  # infer variable by column name
    elif "SNTL" in site_source or "sntl" in site_source:
        var = site_source.split("+")[1]
        site_source = site_source.split("+")[0]
        site_daily = snotel_import(site_source,[var])
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


    return site_daily

def summarize_daily(site_daily,var=None):
    if var is None:
        var = site_daily.columns[0]
    # Summarize data
    summary = pd.DataFrame()
    summary.loc["all","start"] = site_daily.index.min()
    summary.loc["all","end"] = site_daily.index.max()
    summary.loc["all","count"] = site_daily[var].count()
    summary.loc["all","max"] = site_daily[var].max()
    summary.loc["all","min"] = site_daily[var].min()
    summary.loc["all","mean"] = site_daily[var].mean()
    summary.loc["all","median"] = site_daily[var].median()
    summary.loc["all", "sd"] = site_daily[var].std()
    for wy in site_daily["wy"].unique():
        wy_daily = site_daily.loc[site_daily["wy"] == wy]
        summary.loc[wy, "start"] = wy_daily.index.min()
        summary.loc[wy, "end"] = wy_daily.index.max()
        summary.loc[wy, "count"] = wy_daily[var].count()
        summary.loc[wy, "max"] = wy_daily[var].max()
        summary.loc[wy, "min"] = wy_daily[var].min()
        summary.loc[wy, "mean"] = wy_daily[var].mean()
        summary.loc[wy, "median"] = wy_daily[var].median()
        summary.loc[wy, "sd"] = wy_daily[var].std()

    return summary

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

    try:
        data = nwis.get_record(sites=site, service=dtype, parameterCd=parameter)
    except dr.utils.NoSitesError:
        data = pd.DataFrame()
        data["peak_va"] = np.nan

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


