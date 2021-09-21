# -*- coding: utf-8 -*-
"""
Created on Mon Sep 20 17:11:30 2021

@author: WLeong
"""

import pandas as pd
import json
import os
import datetime


# get configurations from json file
def get_cfg(cfg_file_path):
    f = open(cfg_file_path).read()
    cfg = json.loads(f)
    return cfg


# load data from input file (based on config JSON file)
def get_data(cfg):
    input_file = cfg['InputFile']['FilePath']
    input_file_ext = os.path.splitext(input_file)[1][1:]
    input_file_skiprows = cfg['InputFile']['NoOfRowsToSkip']
    col_start = cfg['InputFile']['ColName_Start']
    col_end = cfg['InputFile']['ColName_End']
    col_des = cfg['InputFile']['ColName_ShortDescription']
    col_comment = cfg['InputFile']['ColName_Comment']
    # optional data field: check if it's null
    # check if input file is Excel spreadsheet or CSV file
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
                       col_comment: 'comment'
                       }, inplace=True)
    if cfg['InputFile']['ColName_Completion'] is not None:
        col_pct_completed = cfg['InputFile']['ColName_Completion']
        #df.rename(columns={col_pct_completed: 'completion'}, inplace=True)
    return df


# prepare issues data for chart
def preprocess_data(cfg, df):
    chart_legend_by = cfg['Chart']['ChartLegendBy']
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
    # add relative ref date (optional)
    ref1_date = cfg['InputFile']['ColName_Ref1_Date']
    if ref1_date is not None:
        df['rel_ref1_date'] = df[ref1_date].apply(lambda x: (x - df.start.min()).days)
    ref2_date = cfg['InputFile']['ColName_Ref2_Date']
    if ref2_date is not None:
        df['rel_ref2_date'] = df[ref2_date].apply(lambda x: (x - df.start.min()).days)
    # if completion % is available
    if cfg['InputFile']['ColName_Completion'] is not None:
        # calculate width of completed portion of the task
        df['w_comp']=round(df[cfg['InputFile']['ColName_Completion']]*df.duration/100,2)
    else:
        df['w_comp'] = 0
    # sort by Category
    if len(cfg['DataSelection']['AggregateBy']) > 0:
        chart_legend_by = cfg['DataSelection']['AggregateBy'][0]
    df=df.sort_values(by=[chart_legend_by,'start'], ascending=[False,True]).reset_index(drop=True)
    return df


# filter, aggregate data based on config
def filter_agg_data(cfg, df):
    filter1_colname = cfg['DataSelection']['Filter1']['ColName']
    filter1_type = cfg['DataSelection']['Filter1']['Type']
    filter1_values = cfg['DataSelection']['Filter1']['Values']
    filter2_colname = cfg['DataSelection']['Filter2']['ColName']
    filter2_type = cfg['DataSelection']['Filter2']['Type']
    filter2_values = cfg['DataSelection']['Filter2']['Values']
    filter3_colname = cfg['DataSelection']['Filter3']['ColName']
    filter3_type = cfg['DataSelection']['Filter3']['Type']
    filter3_values = cfg['DataSelection']['Filter3']['Values']
    aggby = cfg['DataSelection']['AggregateBy']
    
    # apply filters
    df_filtered = df.copy()
    # apply filter 1
    if filter1_colname is not None:
        if filter1_type.lower() in ['include','inc']:
            df_filtered = df[df[filter1_colname].isin(filter1_values)]
        elif filter1_type.lower() in ['exclude','exc']:
            df_filtered = df[~df[filter1_colname].isin(filter1_values)]
        else:
            print ('ERROR: Unknown filter1 type. Please enter "include" or "exclude".')
    # apply filter 2
    if filter2_colname is not None:
        if filter2_type.lower() in ['include','inc']:
            df_filtered = df_filtered[df_filtered[filter2_colname].isin(filter2_values)]
        elif filter2_type.lower() in ['exclude','exc']:
            df_filtered = df_filtered[~df_filtered[filter2_colname].isin(filter2_values)]
        else:
            print ('ERROR: Unknown filter2 type. Please enter "include" or "exclude".')
    # apply filter 3
    if filter3_colname is not None:
        if filter3_type.lower() in ['include','inc']:
            df_filtered = df_filtered[df_filtered[filter3_colname].isin(filter3_values)]
        elif filter3_type.lower() in ['exclude','exc']:
            df_filtered = df_filtered[~df_filtered[filter3_colname].isin(filter3_values)]
        else:
            print ('ERROR: Unknown filter3 type. Please enter "include" or "exclude".')
    df_filtered.reset_index(drop=True, inplace=True)
    
    # if there is a requirement to aggregate, then proceed
    if len(aggby) > 0:
        # make a copy of the data
        # aggregate
        df3 = df_filtered.groupby(aggby).agg({'start':min,'end':max,'duration':sum,'w_comp':sum})
        df3['completion'] = round(df3.w_comp / df3.duration * 100, 2)
        df3.drop(columns=['w_comp','duration'], inplace=True)
        # add back other data fields
        df3.reset_index(inplace=True)
        df3['task'] = df3[aggby[0]]
        df3['comment'] = None
        # if 'category1' not in df3.columns:
        #     df3['category1'] = aggby[0]
        # if 'category2' not in df3.columns:
        #     df3['category2'] = None
        # preprocess again
        df_aggd = preprocess_data(cfg, df3)
        return df_aggd
    else:
        return df_filtered