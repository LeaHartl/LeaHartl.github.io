#! /usr/bin/env python3


# load standard modules
import argparse
import json
import urllib
import requests
import os.path
import jinja2
from scipy import stats
import numpy as np
import pandas as pd
import datetime
from datetime import date, timedelta
from pandas import Series, DataFrame, Panel
import matplotlib.pyplot as plt
from matplotlib.offsetbox import AnchoredText

from bokeh.io import show
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, RangeTool, Range1d, LinearAxis
from bokeh.plotting import figure
from bokeh.resources import CDN
from bokeh.embed import file_html



pd.options.mode.chained_assignment = None  # default='warn'  #this turns of copy index warnings - careful!



#--------------------------------------------------------
#some helpers


#colours for plots
# def colours(anom_df):
#     anom_df['colors'] = 'r'
#     anom_df.loc[anom_df.values[:, 1]<=0,'colors'] = 'b'
#     return (anom_df)

# #convert to float and remove data for 2018 (incomplete year)
# def setups(param_df):
#     param_df[['value', 'anomaly']] = param_df[['value', 'anomaly']].astype(float)
#     param_df = param_df[(param_df.index.year != 2019)] #drop 2019 because incomplete    
#     return (param_df)

def read_files(url):
    # with open(filename) as data_file:
        # data = json.load(data_file)
    df=pd.read_csv(url, skiprows=6)
    df = df.drop([0, 1])
    print(df.columns)
    # df = df.drop(['road_temp_set_1','road_temp_set_2', 'wind_chill_set_1d',  'Station_ID', 'weather_cond_code_set_1',  'road_subsurface_tmp_set_1', 'wind_cardinal_direction_set_1d','heat_index_set_1d', 'wet_bulb_temperature_set_1d', 'heat_index_set_1d', 'altimeter_set_1d'     ], axis= 1)
    df.Date_Time = pd.to_datetime(df.Date_Time)
    df[['pressure_set_1', 'air_temp_set_1',
       'relative_humidity_set_1', 'wind_speed_set_1', 'wind_direction_set_1',
       'wind_gust_set_1', 'precip_accum_set_1', 'precip_accum_24_hour_set_1',
       'dew_point_temperature_set_1d', 'altimeter_set_1d']] = df[['pressure_set_1', 'air_temp_set_1',
       'relative_humidity_set_1', 'wind_speed_set_1', 'wind_direction_set_1',
       'wind_gust_set_1', 'precip_accum_set_1', 'precip_accum_24_hour_set_1',
       'dew_point_temperature_set_1d', 'altimeter_set_1d']].astype(float)
    # df.set_index('Date_Time', inplace=True)

    print (df.head(10))
    print (df.columns)

    return df

            # replace missing values with nan and trace values with 0.0
    # dat_df['value'].replace(-99, np.nan, inplace = True)
    # dat_df['anomaly'].replace(-99, 0.0, inplace=True)
    # dat_df.index = pd.to_datetime(dat_df.index, format = '%Y%m')


#--------------------------------------------------------
#MAIN script


now = datetime.datetime.now()

def fixdatestrings(dt):
    if dt < 10:
        dtS = '0' + str(dt)
    else:
        dtS = str(dt)
    return (dtS)


end = str(now.year) + fixdatestrings(now.month) + fixdatestrings(now.day) + fixdatestrings(now.hour)
startdate = date.today() - timedelta(30)
start = str(startdate.year) + fixdatestrings(startdate.month) + fixdatestrings(startdate.day)
print(start)
print (end)
# 201904240000

var = 'vars=pressure,air_temp,dew_point_temperature,relative_humidity,wind_speed,wind_direction,wind_gust,precip_accum,precip_accum_24_hour'

filename ='https://api.mesowest.net/v2/stations/timeseries?&stid=TRDA2&start='+start+'0000&end='+end+'00&token=demotoken&r&obtimezone=local&'+var+'&output=csv'
dat_df = read_files(filename) #load json and turn into dataframe.

dates = np.array(dat_df.Date_Time , dtype=np.datetime64)
dat_df['dates'] = np.array(dat_df.Date_Time , dtype=np.datetime64)
source = ColumnDataSource(data=dat_df)
# source = ColumnDataSource(data=dict(date=dates, temp=dat_df.air_temp_set_1, dew = dat_df.dew_point_temperature_set_1d))
print(dat_df.head())
p = figure(plot_height=300, plot_width=800,
            title="Richardson @ Trims DOT (TRDA2)",
           x_axis_type="datetime", x_axis_location="above",
           background_fill_color="#efefef", x_range=(dates[-200], dates[-1]))
# tools="xpan", toolbar_location=None
p.line('dates', 'air_temp_set_1', source=source, legend = 'Air Temp', line_color="tomato")
p.line('dates', 'dew_point_temperature_set_1d', source=source, legend = 'Dew Point', line_color="indigo" )
p.y_range = Range1d(
    dat_df.dew_point_temperature_set_1d.min() , dat_df.air_temp_set_1.max() +2)

p.yaxis.axis_label = 'Celsius'
p.legend.location = "bottom_left"
p.legend.click_policy="hide"

p.extra_y_ranges = {"hum": Range1d(start=0, end=100)}
p.add_layout(LinearAxis(y_range_name="hum", axis_label='%'), 'right')
p.line('dates', 'relative_humidity_set_1', source=source, legend = 'Rel Hum', line_color="green" , y_range_name="hum")

p1 = figure(plot_height=300, plot_width=800,
            x_range=p.x_range,
            # title="Richardson @ Trims DOT (TRDA2)",
           x_axis_type="datetime", x_axis_location="above",
           background_fill_color="#efefef")
# tools="xpan", toolbar_location=None
p1.line('dates', 'wind_speed_set_1', source=source, legend = 'Wind speed', line_color="tomato")
p1.line('dates', 'wind_gust_set_1', source=source, legend = 'Gusts', line_color="indigo" )
p1.y_range = Range1d(start=0, end= dat_df.wind_gust_set_1.max() +2)

p1.yaxis.axis_label = 'm/s'

p1.legend.location = "bottom_left"
p1.legend.click_policy="hide"

p1.extra_y_ranges = {"dir": Range1d(start=0, end=360)}
p1.add_layout(LinearAxis(y_range_name="dir"), 'right')
p1.circle('dates', 'wind_direction_set_1', source=source, legend = 'Wind Dir', line_color="black" , y_range_name="dir")



select = figure(title="Drag the middle and edges of the selection box to change the range above",
                plot_height=130, plot_width=800, y_range=p.y_range,
                x_axis_type="datetime", y_axis_type=None,
                tools="", toolbar_location=None, background_fill_color="#efefef")

range_tool = RangeTool(x_range=p.x_range)
range_tool.overlay.fill_color = "navy"
range_tool.overlay.fill_alpha = 0.2

select.line('dates', 'air_temp_set_1', source=source)
select.ygrid.grid_line_color = None
select.add_tools(range_tool)
select.toolbar.active_multi = range_tool
show(column(p, p1, select))
# show(p)


html = file_html(p, CDN, "my plot")





# #convert to float and remove data for 2018 (incomplete year)
# temp_df = setups(temp_df)
# # print(temp_df)

# #annual and monthly means
# temp_df_an = temp_df.resample("A").mean()
# temp_df_mn = temp_df.resample("M").mean()
# # print(temp_df_mn.tail(10))
# temp_df_an['rolling_anom'] = temp_df_an['anomaly'].rolling(window=5, center=True).mean()
# temp_df_an['normal'] = temp_df_an['value'] - temp_df_an['anomaly']
# # temp_df_an[div]['value_percent'] = 100 * temp_df_an[div]['value'] / temp_df_an[div]['normal']

# #make dfs of seasonal means and add colour clomuns for plots
# # temp_winter_df, temp_spring_df[div], temp_summer_df[div], temp_fall_df[div] = seasons(temp_df[div]) 
# # temp_winter_df = colours(temp_winter_df[div]) 
# # temp_spring_df = colours(temp_spring_df[div]) 
# # temp_summer_df = colours(temp_summer_df[div]) 
# # temp_fall_df = colours(temp_fall_df[div]) 
# ghelp.normals(temp_df_mn, output_dir)
# ghelp.plotStatewide(temp_df_an, 'Mean annual air temperature', 'Annual', param, 'AK', output_dir, baseStart, baseEnd)


