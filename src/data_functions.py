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
def csv_daily_import(filename,single=True):
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

    return(out)

def nwis_import(site, dtype, start=None, end=None):
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

    return(out)

def import_snotel(site,stype,vars=["WTEQ","SNWD","PREC","TAVG"],verbose=False,inc=False):
    """Download NRCS SNOTEL data

    Parameters
    ---------
        site_no: site number
        snotel_sites: df of all sites with other information on sites (https://wcc.sc.egov.usda.gov/nwcc/yearcount?network=sntl&state=&counttype=statelist)
        start_date: datetime
        end_date: datetime
        vars: array of variables for import (tested with WTEQ, SNWD, PREC, TAVG..other options may be available)
        verbose: boolean
            True : enable print during function run

    Returns
    -------
        dataframe

    """
    print(site)
    # Get snotel file
    snotel_sites = pd.read_csv("src/snotel_sites.csv")

    # Get site name, add %20 for spaces
    if stype=="name":
        name = site.replace(" ","%20")
    else:
        name = snotel_sites.loc[snotel_sites[stype]==site,"name"].item().replace(" ", "%20")
    print(name)
    state = snotel_sites.loc[snotel_sites[stype]==site,"state"].item()
    print(state)
    print(vars)

    # Create dictionary of variables
    snotel_dict = dict()
    ext = "DAILY"

    # Cycle through variables
    for var in vars:
        if verbose == True:
            print("Importing {} data".format(var))
        site_url = f"https://nwcc-apps.sc.egov.usda.gov/awdb/site-plots/POR/{var}/{state}/{name}.csv"
        print(site_url)
        if verbose == True:
            print(site_url)
        failed = True
        tries = 0
        csv_str = ""
        while failed:
            try:
                csv_str = r_get(site_url, timeout=5,verify=True).text
                failed = False
            except (ConnectionError, TimeoutError,ReadTimeout,ReadTimeoutError) as error:
                print(f"{error}")
                tries += 1
                if tries <= 10:
                    print(f"After {tries} tries, retrying...")
                else:
                    continue

            if "not found on this server" in csv_str:
                print("Site URL incorrect.")
                continue

        csv_io = StringIO(csv_str)
        f = pd.read_csv(csv_io,index_col=0)

        # Create index of dates for available data for current site
        df_index = pd.date_range(dt.datetime.strptime(f"{f.index[0]}-{int(f.columns[0])-1}","%m-%d-%Y"),
                                   dt.datetime.today(),
                                   freq="D",
                                   tz='UTC')
        # Create dataframe of available data (includes Feb 29)
        snotel_in = pd.DataFrame(index=df_index)

        # Concatenate the cleaned data to the date index
        for year in f.columns:
            try:
                int(year)
            except ValueError:
                continue
            # Remove missing columns...
            year_data = f.loc[:,year].dropna()

            # Fix index (will no longer include Feb 29 when missing)
            year_index = list()
            for i in year_data.index:
                if int(i[:2])>=10:
                    year_index.append(dt.datetime.strptime(f"{i}-{int(year)-1}","%m-%d-%Y"))
                else:
                    year_index.append(dt.datetime.strptime(f"{i}-{int(year)}", "%m-%d-%Y"))

            year_data.index = pd.DatetimeIndex(year_index,tz="utc")

            # Set appropriate rows in snotel_in
            snotel_in.loc[year_data.index,var] = year_data


        # For precip, calculate incremental precip and remove negative values
        if var == "PREC" and inc==True:
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
    data = pd.DataFrame(index=dates)

    if verbose == True:
        print("Preparing output")
    for key in snotel_dict.keys():
        # Merge to output dataframe
        snotel_in = data.merge(snotel_dict[key][key], left_index=True, right_index=True, how="left")
        data[key] = snotel_in[key]
        if verbose == True:
            print("Added to dataframe")

    return (data)

def import_hydromet(site,var,region,verbose=False):
    # Set today's date
    today = dt.datetime.today()

    # Build site url depending on region
    if region in ["cpn","CPN","pn","PN"]:
        reg = "CPN"
        site_url = f"https://www.usbr.gov/pn-bin/daily.pl?station={site}&format=html&year={1900}&month={10}&day={1}&year={today.year}&month={today.month}&day={today.day}&pcode={var}"

    elif region in ["GP","gp","MBART","mbart","MB","mb"]:
        reg = "MBART"
        site_url = f"https://www.usbr.gov/gp-bin/webarccsv.pl?parameter={site}%20{var}&syer={1900}&smnth={10}&sdy={1}&eyer={today.year}&emnth={today.month}&edy={today.day}&format=2"

    elif region in ["UC","uc","UCB","ucb"]:
        reg = "UCB"
        ucb_dict = {"af":"17","storage":"17","in":"29","qu":"29","qd":"42","fb":"49","elev":"49","stage":"49"}
        if var in ucb_dict.keys():
            var = ucb_dict[var]
        site_url = f"https://www.usbr.gov/uc/water/hydrodata/reservoir_data/{site}/csv/{var}.csv"

    else:
        return None

    # Import data
    if verbose == True:
        print(f"Importing {var} data")
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

    # Fix html info and read csv (GP only)
    if reg=="MBART":
        csv_str = csv_str.split("BEGIN DATA")[1].replace("NO RECORD","NaN")
        csv_str = csv_str.split("END DATA")[0].replace("MISSING","NaN").replace(" ","")
        csv_io = StringIO(csv_str)
        f = pd.read_csv(csv_io,parse_dates=True,index_col=0)
    # Read html (CPN only)
    elif reg=="CPN":
        # Convert to dataframe
        csv_io = StringIO(csv_str)
        f = pd.read_html(csv_io,flavor="lxml",parse_dates=True,index_col=0)
    elif reg=="UCB":
        # Convert to dataframe
        csv_io = StringIO(csv_str)
        f = pd.read_csv(csv_io,parse_dates=True,index_col=0)

    # Fix if list
    if isinstance(f,list):
        hydro_in = f[0]
    else:
        hydro_in = f

    # Fix variable name
    var = var
    hydro_in.columns = [var]
    # Check for start and end dates
    hydro_in_true = hydro_in[hydro_in[var].notna()==True].index
    begin = hydro_in_true.min()
    end = hydro_in_true.max()
    hydro_in = hydro_in.loc[begin:end]

    dates = pd.date_range(begin, end, freq="D")
    out = pd.DataFrame(index=dates)

    out = out.merge(hydro_in[var], left_index=True, right_index=True, how="left")

    return out

def import_daily(site_source,wy_division,decimal,zero=False):
    if isinstance(site_source,list):
        if site_source[2] in ["sntl","SNTL"]:
            site = site_source[0]
            if site.isnumeric():
                stype = "site_no"
                site = int(site)
            else:
                stype = "name"
            var = site_source[1]
            if var not in ["WTEQ","SNWD","PREC","TAVG"]:
                print("Invalid variable listed. Using WTEQ")
                var = "WTEQ"
            site_daily = import_snotel(site,stype,[var])
        else:
            # Load hydromet data
            site = site_source[0]
            var = site_source[1]
            region = site_source[2]
            site_daily = import_hydromet(site,var,region)
            var = site_daily.columns[0]
    elif ".csv" in site_source:
        # Load from .csv file
        site_daily = csv_daily_import(site_source)
        var = site_daily.columns[0]  # infer variable by column name
    else:
        # Load from usgs website
        if len(site_source) != 8:
            print("Must provide valid USGS site number (8-digit string) for at-site data")
        else:
            site_daily = nwis_import(site=site_source, dtype="dv")
            var = "flow"

    # Clean data, if selected
    if type(zero) is bool and zero==False:
        print("no edits...")
    else:
        # Remove negative values
        if isinstance(zero,int) or isinstance(zero,float):
            idx = site_daily[site_daily[var] < zero].index
            site_daily.loc[idx, var] = zero
            site_daily.loc[idx,"clean"] = f"User Input: {zero}"
        else:
            # Clean using 3-day average
            idx3 = site_daily[site_daily[var] < 0].index
            if idx3.__len__()>0:
                site_rolling3 = site_daily.rolling(3, center=True).mean()
                site_daily.loc[idx3, var] = site_rolling3
                site_daily.loc[idx3, "clean"] = "Average: 3-day"

                # If needed, clean using 5-day average
                idx5 = site_daily[site_daily[var] < 0].index
                if idx5.__len__()>0:
                    site_rolling5 = site_daily.rolling(3, center=True).mean()
                    site_daily.loc[idx5, var] = site_rolling5
                    site_daily.loc[idx5, "clean"] = "Average: 5-day"

                    # If needed, set remaining values to zero
                    idxlast = site_daily[site_daily[var] < 0].index
                    if idxlast.__len__()>0:
                        site_daily.loc[idxlast, var] = 0
                        site_daily.loc[idxlast, "clean"] = "Average: set to zero"

    site_daily[var] = site_daily[var].round(decimal)

    # Add year, month and wy
    site_daily["doy"] = pd.DatetimeIndex(site_daily.index).dayofyear
    site_daily["year"] = pd.DatetimeIndex(site_daily.index).year
    site_daily["month"] = pd.DatetimeIndex(site_daily.index).month
    site_daily["wy"] = site_daily["year"]
    if wy_division == "WY":
        site_daily.loc[site_daily["month"] >= 10, "wy"] = site_daily.loc[site_daily["month"] >= 10, "year"] + 1

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


