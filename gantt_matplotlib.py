# -*- coding: utf-8 -*-
"""
Created on Mon Sep  6 14:34:37 2021

@author: WLeong

Source: https://medium.com/geekculture/create-an-advanced-gantt-chart-in-python-f2608a1fd6cc

"""

# Import Libraries
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
#from matplotlib import dates as mdates
import datetime
import json
import os

f = open(r'D:\Users\wleong\Documents\_personal\gantt\config.json').read()
cfg = json.loads(f)

# import data from CFG file
chart_start_date = datetime.datetime.strptime(cfg['Chart']['ChartStartDate'],'%Y-%m-%d')
chart_title = cfg['Chart']['ChartTitle']
chart_legend_title = cfg['Chart']['LegendTitle']
chart_groupby = cfg['Chart']['ChartGroupBy']
xticks_size = cfg['Chart']['XAxisMajor_NoOfDays']

input_file = cfg['InputFile']['FilePath']
input_file_ext = os.path.splitext(input_file)[1][1:]
input_file_skiprows = cfg['InputFile']['NoOfRowsToSkip']
col_start = cfg['InputFile']['ColName_Start']
col_end = cfg['InputFile']['ColName_End']
col_cat1 = cfg['InputFile']['ColName_Category1']
col_cat2 = cfg['InputFile']['ColName_Category2']
col_des = cfg['InputFile']['ColName_ShortDescription']
col_pct_completed = cfg['InputFile']['ColName_Completion']
if input_file_ext=='xlsx' or input_file_ext=='xls':
    df = pd.read_excel(input_file, skiprows=input_file_skiprows)
elif input_file_ext=='csv':
    df = pd.read_csv(input_file)
    #Convert dates to datetime format (TO BE FIXED)
    #df.start=pd.to_datetime(df.start, format='%d/%m/%Y')
    #df.end=pd.to_datetime(df.end, format='%d/%m/%Y')
    
# columns renaming
df.rename(columns={col_start: 'start',
                   col_end: 'end',
                   col_des: 'task',
                   col_cat1: 'category1',
                   col_cat2: 'category2',
                   col_pct_completed: 'completion'}, inplace=True)
df = df[['task','start','end','category1','category2','completion']]
# pre-processing: trim description
df.task = df.task.str[:50]
# pre-processing: if no end date, fill values with start date
df.loc[df.end.isna(), 'end'] = df[df.end.isna()]['start']


# zoom into chart start date
for i in range(len(df)):
    if df.loc[i,'start'] < chart_start_date:
        df.loc[i,'start'] = chart_start_date
# if both start & completion date are earlier than user filter, then remove row
df = df[~(df.end < chart_start_date)]


#Add Duration
df['duration']=df.end-df.start
df.duration=df.duration.apply(lambda x: x.days+1)
#sort in ascending order of start date
df=df.sort_values(by=['category1','start'], ascending=True)

#project level variables
p_start=df.start.min()
p_end=df.end.max()
p_duration=(p_end-p_start).days+1
#Add relative date
df['rel_start']=df.start.apply(lambda x: (x - p_start).days)
#Create custom x-ticks and x-tick labels
x_ticks=[i for i in range(p_duration+1)]
x_labels=[(p_start+datetime.timedelta(days=i)).strftime('%d-%b-%y') for i in x_ticks]

# calculate width of completed portion of the task
df['w_comp']=round(df.completion*df.duration/100,2)

# assign colours
colours = list(mcolors.TABLEAU_COLORS.keys())
categories = list(df.category1.unique())
c_dict = {}
for i in range(len(categories)):
    c_dict[categories[i]] = colours[i]

# sort by Category
df=df.sort_values(by='category1', ascending=False).reset_index(drop=True)

# #Only HR Tasks
# df=df[df.Department=='HR'].reset_index()
# #Only Incomplete tasks
#df=df[df.Completion<100].reset_index()

yticks=[i for i in range(len(df.task))]

#fig = plt.figure(figsize=(12,7))
fig, ax = plt.subplots(1,1, figsize=(12,10))
plt.title(chart_title, size=14)
for i in range(df.shape[0]):
    color=c_dict[df[chart_groupby][i]]
    plt.barh(y=yticks[i], left=df.rel_start[i], 
             width=df.duration[i], alpha=0.4, 
             color=color)
    plt.barh(y=yticks[i], left=df.rel_start[i], 
             width=df.w_comp[i], alpha=1, color=color,
            label=df[chart_groupby][i])
    plt.text(x=df.rel_start[i]+df.w_comp[i],
             y=yticks[i],
             s=f'{df.completion[i]}%')

plt.gca().invert_yaxis()
plt.xticks(ticks=x_ticks[::xticks_size], labels=x_labels[::xticks_size])
plt.yticks(ticks=yticks, labels=df.task)
plt.grid(axis='x', alpha=0.1)

# add reference line for today
xticks_today_pos = [(p_start+datetime.timedelta(days=i)).strftime('%d-%b-%y') for i in x_ticks].index(datetime.datetime.today().strftime('%d-%b-%y'))
plt.axvline(x=xticks_today_pos, linestyle='--')

#fix legends
handles, labels = plt.gca().get_legend_handles_labels()
handle_list, label_list = [], []
for handle, label in zip(handles, labels):
    if label not in label_list:
        handle_list.append(handle)
        label_list.append(label)
plt.legend(handle_list, label_list, fontsize='medium', 
           title=chart_legend_title, title_fontsize='large')

#fig.autofmt_xdate() #does not do anything!
#ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%Y'))

plt.xticks(rotation=90, ha='right')
#plt.update_xaxes(dtick='M1', tickformet='%b-%Y')

fig.savefig('output.png', dpi=150, bbox_inches='tight')
plt.show()


