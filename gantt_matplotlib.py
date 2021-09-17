# -*- coding: utf-8 -*-
"""
Created on Mon Sep  6 14:34:37 2021

@author: WLeong

Reference: https://medium.com/geekculture/create-an-advanced-gantt-chart-in-python-f2608a1fd6cc

"""

# Import Libraries
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import datetime
import json
import os
#import pytz


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
        df.rename(columns={col_pct_completed: 'completion'}, inplace=True)
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
        df['w_comp']=round(df.completion*df.duration/100,2)
    else:
        df['w_comp'] = 0
    # sort by Category
    if len(cfg['DataSelection']['AggregateBy']) > 0:
        chart_legend_by = cfg['DataSelection']['AggregateBy'][0]
    df=df.sort_values(by=[chart_legend_by,'start'], ascending=[False,True]).reset_index(drop=True)
    return df


# filter, aggregate data based on config
def filter_agg_data(cfg, df):
    filter1_colname = cfg['DataSelection']['Filter1_ColName']
    filter1_type = cfg['DataSelection']['Filter1_Type']
    filter1_values = cfg['DataSelection']['Filter1_Values']
    filter2_colname = cfg['DataSelection']['Filter2_ColName']
    filter2_type = cfg['DataSelection']['Filter2_Type']
    filter2_values = cfg['DataSelection']['Filter2_Values']
    filter3_colname = cfg['DataSelection']['Filter3_ColName']
    filter3_type = cfg['DataSelection']['Filter3_Type']
    filter3_values = cfg['DataSelection']['Filter3_Values']
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


# plot gantt chart and save as PNG
def generate_gantt(cfg, df2):
    time_now = datetime.datetime.now()
    # import data from CFG file
    chart_start_date = datetime.datetime.strptime(cfg['Chart']['ChartStartDate'],'%Y-%m-%d')
    chart_title = cfg['Chart']['ChartTitle'] + str(" - %s" % datetime.datetime.strftime(time_now, '%Y-%m-%d %H:%M:%S'))
    xticks_size = cfg['Chart']['XAxisMajor_NoOfDays']
    
    # if data was aggregated, legend will need to be forced
    if len(cfg['DataSelection']['AggregateBy']) > 0:
        aggby = cfg['DataSelection']['AggregateBy'][0]
        chart_legend_title = aggby
        chart_legend_by = aggby
    else:
        chart_legend_title = cfg['Chart']['LegendTitle']
        chart_legend_by = cfg['Chart']['ChartLegendBy']

    #project level variables
    p_start = df2.start.min()
    p_end = df2.end.max()
    p_duration = (p_end-p_start).days+1
    
    #Create custom x-ticks and x-tick labels
    x_ticks=[i for i in range(p_duration+1)]
    x_labels=[(p_start+datetime.timedelta(days=i)).strftime('%d-%b-%y') for i in x_ticks]
    
    # assign colours
    categories = list(df2[chart_legend_by].unique())
    if len(categories)>len(mcolors.TABLEAU_COLORS):
        colours = list(mcolors.CSS4_COLORS.keys())      # 1xx different colours
    else:
        colours = list(mcolors.TABLEAU_COLORS.keys())   # 10 different colours
    c_dict = {}
    for i in range(len(categories)):
        c_dict[categories[i]] = colours[i]
    
    yticks=[i for i in range(len(df2.task))]

    fig, ax = plt.subplots(1,1, figsize=(12,10))
    plt.title(chart_title, size=14)
    
    # plot each issue row by row
    for i in range(len(df2)):
        color = c_dict[df2[chart_legend_by][i]]

        # if completion % is available, add value label
        if cfg['InputFile']['ColName_Completion'] is not None:
            alpha_completed = 0.4
            if df2.comment[i]=='':
                comment_str = f'{df2.completion[i]}%'
            else:
                comment_str = f'{df2.completion[i]}%' + ' - %s' % df2.comment[i]
            plt.text(x=df2.rel_start[i]+df2.w_comp[i],
                     y=yticks[i],
                     s= comment_str)
        else:
            alpha_completed = 0.75

        # plot completed bar
        plt.barh(y=yticks[i], left=df2.rel_start[i], 
                 width=df2.duration[i], alpha=alpha_completed, 
                 color=color)
        # plot entire timeline bar
        plt.barh(y=yticks[i], left=df2.rel_start[i], 
                 width=df2.w_comp[i], alpha=0.75, color=color,
                label=df2[chart_legend_by][i])


        # plot reference date 1 (optional data field)
        ref1_date = cfg['InputFile']['ColName_Ref1_Date']
        ref1_marker_style = cfg['Chart']['Ref1_MarkerStyle']
        ref1_marker_colour = cfg['Chart']['Ref1_MarkerColour']
        ref1_marker_edgewidth = cfg['Chart']['Ref1_MarkerEdgeWidth']
        ref1_marker_size = cfg['Chart']['Ref1_MarkerSize']
        if ref1_date is not None:
            if not pd.isnull(df2[ref1_date][i]):
                ax.plot(df2.rel_ref1_date[i],                 # this x-axis needs to be relative to the chart start date
                        yticks[i],
                        marker=ref1_marker_style,         # https://matplotlib.org/stable/api/markers_api.html
                        color=ref1_marker_colour,
                        markeredgewidth=ref1_marker_edgewidth,
                        markersize=ref1_marker_size,
                        lw=0)

        # plot reference date 2 (optional data field)
        ref2_date = cfg['InputFile']['ColName_Ref2_Date']
        ref2_marker_style = cfg['Chart']['Ref2_MarkerStyle']
        ref2_marker_colour = cfg['Chart']['Ref2_MarkerColour']
        ref2_marker_edgewidth = cfg['Chart']['Ref2_MarkerEdgeWidth']
        ref2_marker_size = cfg['Chart']['Ref2_MarkerSize']
        if ref2_date is not None:
            if not pd.isnull(df2[ref2_date][i]):
                ax.plot(df2.rel_ref2_date[i],                 # this x-axis needs to be relative to the chart start date
                        yticks[i],
                        marker=ref2_marker_style,         # https://matplotlib.org/stable/api/markers_api.html
                        color=ref2_marker_colour,
                        markeredgewidth=ref2_marker_edgewidth,
                        markersize=ref2_marker_size,
                        lw=0)
    
    plt.gca().invert_yaxis()
    plt.xticks(ticks=x_ticks[::xticks_size], labels=x_labels[::xticks_size])
    plt.yticks(ticks=yticks, labels=df2.task)
    plt.grid(axis='x', alpha=0.1)
    
    # add reference line for today
    xticks_today_pos = [(p_start+datetime.timedelta(days=i)).strftime('%d-%b-%y') for i in x_ticks].index(datetime.datetime.today().strftime('%d-%b-%y'))
    plt.axvline(x=xticks_today_pos, linestyle='--', color='red', lw=0.5, alpha=0.75)
    
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
    #cfg = get_cfg(r'D:\Users\wleong\Documents\_personal\gantt\config_DMS.json')
    #cfg = get_cfg(r'D:\Users\wleong\Documents\_personal\gantt\config_sample.json')
    cfg = get_cfg(r'D:\Wilson\Documents\Python Scripts\tools\gantt\config_sample.json')
    
    # load issues data & pre-process
    df = get_data(cfg)
    df = preprocess_data(cfg, df)
    
    # filter, aggregate data
    df2 = filter_agg_data(cfg, df)
    #df2.to_excel('agg_output.xlsx', index=False)
    
    # plot gantt chart & save as PNG
    generate_gantt(cfg, df2)


main()