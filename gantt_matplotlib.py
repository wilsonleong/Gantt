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
import datetime
import json
import os
import pytz


# get configurations from json file
def get_cfg(cfg_file_path):
    f = open(cfg_file_path).read()
    cfg = json.loads(f)
    return cfg


# load issues data
def get_data(cfg):
    input_file = cfg['InputFile']['FilePath']
    input_file_ext = os.path.splitext(input_file)[1][1:]
    input_file_skiprows = cfg['InputFile']['NoOfRowsToSkip']
    col_start = cfg['InputFile']['ColName_Start']
    col_end = cfg['InputFile']['ColName_End']
    col_cat1 = cfg['InputFile']['ColName_Category1']
    col_cat2 = cfg['InputFile']['ColName_Category2']
    col_des = cfg['InputFile']['ColName_ShortDescription']
    col_pct_completed = cfg['InputFile']['ColName_Completion']
    col_comment = cfg['InputFile']['ColName_Comment']
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
                       col_pct_completed: 'completion',
                       col_comment: 'comment'
                       }, inplace=True)
    df = df[['task','start','end','category1','category2','completion','comment']]
    return df


# prepare issues data for chart
def preprocess_data(cfg, df):
    # pre-processing: trim description
    df.task = df.task.str[:50]
    # pre-processing: if no end date, fill values with start date
    df.loc[df.end.isna(), 'end'] = df[df.end.isna()]['start']
    # fill na comments
    df.comment.fillna('', inplace=True)
    # zoom into chart start date
    chart_start_date = datetime.datetime.strptime(cfg['Chart']['ChartStartDate'],'%Y-%m-%d')
    for i in range(len(df)):
        if df.loc[i,'start'] < chart_start_date:
            df.loc[i,'start'] = chart_start_date
    # if both start & completion date are earlier than user filter, then remove row
    df = df[~(df.end < chart_start_date)]
    #Add Duration
    df['duration']=df.end-df.start
    df.duration=df.duration.apply(lambda x: x.days+1)
    #Add relative date
    df['rel_start']=df.start.apply(lambda x: (x - df.start.min()).days)
    # calculate width of completed portion of the task
    df['w_comp']=round(df.completion*df.duration/100,2)
    # sort by Category
    df=df.sort_values(by=['category1','start'], ascending=[False,True]).reset_index(drop=True)
    return df


# filter, aggregate data based on config
def filter_agg_data(cfg, df):
    filter_cat1 = cfg['DataSelection']['Cat1ToInclude']
    filter_cat2 = cfg['DataSelection']['Cat2ToInclude']
    aggby = cfg['DataSelection']['AggregateBy']
    
    # if there is a requirement to aggregate, then proceed
    if len(aggby) > 0:
        # make a copy of the data
        df2 = df.copy()
        # filter by cat1
        if len(filter_cat1) > 0:
            df2 = df[df.category1.isin(filter_cat1)]
        # filter by cat2
        if len(filter_cat2) > 0:
            df2 = df[df.category2.isin(filter_cat2)]
        # aggregate
        df3 = df2.groupby(aggby).agg({'start':min,'end':max,'duration':sum,'w_comp':sum})
        df3['completion'] = round(df3.w_comp / df3.duration * 100, 2)
        df3.drop(columns=['w_comp','duration'], inplace=True)
        # add back other data fields
        df3.reset_index(inplace=True)
        df3['task'] = df3[aggby]
        df3['comment'] = None
        if 'category1' not in df3.columns:
            df3['category1'] = aggby[0]
        if 'category2' not in df3.columns:
            df3['category2'] = None
        # preprocess again
        df4 = preprocess_data(cfg, df3)
        return df4
    else:
        return df


# plot gantt chart and save as PNG
def generate_gantt(cfg, df):
    time_now = datetime.datetime.now()
    # import data from CFG file
    chart_start_date = datetime.datetime.strptime(cfg['Chart']['ChartStartDate'],'%Y-%m-%d')
    chart_title = cfg['Chart']['ChartTitle'] + str(" - %s" % datetime.datetime.strftime(time_now, '%Y-%m-%d %H:%M:%S'))
    chart_legend_title = cfg['Chart']['LegendTitle']
    chart_groupby = cfg['Chart']['ChartGroupBy']
    xticks_size = cfg['Chart']['XAxisMajor_NoOfDays']

    #project level variables
    p_start = df.start.min()
    p_end = df.end.max()
    p_duration = (p_end-p_start).days+1
    
    #Create custom x-ticks and x-tick labels
    x_ticks=[i for i in range(p_duration+1)]
    x_labels=[(p_start+datetime.timedelta(days=i)).strftime('%d-%b-%y') for i in x_ticks]
    
    # assign colours
    colours = list(mcolors.TABLEAU_COLORS.keys())
    categories = list(df.category1.unique())
    c_dict = {}
    for i in range(len(categories)):
        c_dict[categories[i]] = colours[i]
    
    yticks=[i for i in range(len(df.task))]
    
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
        if df.comment[i]=='':
            comment_str = f'{df.completion[i]}%'
        else:
            comment_str = f'{df.completion[i]}%' + ' - %s' % df.comment[i]
        plt.text(x=df.rel_start[i]+df.w_comp[i],
                 y=yticks[i],
                 s= comment_str)
    
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
    
    # rotate date
    plt.xticks(rotation=90, ha='right')
    
    fig.savefig('output.png', dpi=150, bbox_inches='tight')
    plt.show()



# main process
def main():
    # get the config from json file
    cfg = get_cfg(r'D:\Users\wleong\Documents\_personal\gantt\config.json')
    
    # load issues data & pre-process
    df = get_data(cfg)
    df = preprocess_data(cfg, df)
    
    # filter, aggregate data
    df2 = filter_agg_data(cfg, df)
    
    # plot gantt chart & save as PNG
    generate_gantt(cfg, df2)


main()