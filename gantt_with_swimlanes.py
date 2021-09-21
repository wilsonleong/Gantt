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


    # generate the plot & axes
    groups = list(df2[chart_legend_by].unique())
    groups.sort()
    
    fig = plt.figure(figsize=(12,10))
    gs = fig.add_gridspec(len(groups), hspace=0.5)
    axs = gs.subplots(sharex=True)
    fig.suptitle(chart_title, size=12)
    
    # plot each App in a separate ax
    for g in range(len(groups)):
        dfGroup = df2[df2[chart_legend_by]==groups[g]].copy()
        dfGroup = dfGroup.sort_values(['start'], ascending=False)
        dfGroup.reset_index(inplace=True, drop=True)
        
        axs[g].set_title(groups[g], size=10, loc='left')
        
        yticks=[y for y in range(len(dfGroup.task))]
    
        # plot each issue row by row
        for r in range(len(dfGroup)):
            color = c_dict[groups[g]]
    
            # if completion % is available, add value label
            if cfg['InputFile']['ColName_Completion'] is not None:
                alpha_completed = 0.4
                if dfGroup.comment[r]=='':
                    comment_str = f"{dfGroup[cfg['InputFile']['ColName_Completion']][r]}%"
                else:
                    comment_str = f"{dfGroup[cfg['InputFile']['ColName_Completion']][r]}%" + ' - %s' % dfGroup.comment[r]
                # only plot if task name is displayed on y-axis instead of on the timeline bar
                if cfg['Chart']['YAxisDisplayText']:
                    axs[g].text(x=dfGroup.rel_start[r]+dfGroup.w_comp[r],
                             y=yticks[r],
                             s=comment_str,
                             verticalalignment='center',
                             color='gray')
            else:
                alpha_completed = 0.75
    
            # plot completed bar
            axs[g].barh(y=yticks[r], left=dfGroup.rel_start[r], 
                     width=dfGroup.duration[r], alpha=alpha_completed, 
                     color=color)
            # plot entire timeline bar
            axs[g].barh(y=yticks[r], left=dfGroup.rel_start[r], 
                     width=dfGroup.w_comp[r], alpha=0.75, color=color,
                    label=dfGroup[chart_legend_by][r])
            
            # add theme display text
            if not cfg['Chart']['YAxisDisplayText']:
                axs[g].text(x=dfGroup.rel_start[r],
                         y=yticks[r],
                         s=dfGroup.task[r],
                         color='dimgrey',
                         verticalalignment='center',
                         size=7
                         )
    
            # plot row reference date 1 (optional data field)
            ref1_date = cfg['InputFile']['ColName_Ref1_Date']
            ref1_marker_style = cfg['Chart']['RowRef1']['MarkerStyle']
            ref1_marker_colour = cfg['Chart']['RowRef1']['MarkerColour']
            ref1_marker_edgewidth = cfg['Chart']['RowRef1']['MarkerEdgeWidth']
            ref1_marker_size = cfg['Chart']['RowRef1']['MarkerSize']
            if ref1_date is not None:
                if not pd.isnull(dfGroup[ref1_date][r]):
                    axs[g].plot(dfGroup.rel_ref1_date[r],                 # this x-axis needs to be relative to the chart start date
                            yticks[r],
                            marker=ref1_marker_style,         # https://matplotlib.org/stable/api/markers_api.html
                            color=ref1_marker_colour,
                            markeredgewidth=ref1_marker_edgewidth,
                            markersize=ref1_marker_size,
                            lw=0)
    
            # plot row reference date 2 (optional data field)
            ref2_date = cfg['InputFile']['ColName_Ref2_Date']
            ref2_marker_style = cfg['Chart']['RowRef2']['MarkerStyle']
            ref2_marker_colour = cfg['Chart']['RowRef2']['MarkerColour']
            ref2_marker_edgewidth = cfg['Chart']['RowRef2']['MarkerEdgeWidth']
            ref2_marker_size = cfg['Chart']['RowRef2']['MarkerSize']
            if ref2_date is not None:
                if not pd.isnull(dfGroup[ref2_date][r]):
                    axs[g].plot(dfGroup.rel_ref2_date[r],                 # this x-axis needs to be relative to the chart start date
                            yticks[r],
                            marker=ref2_marker_style,         # https://matplotlib.org/stable/api/markers_api.html
                            color=ref2_marker_colour,
                            markeredgewidth=ref2_marker_edgewidth,
                            markersize=ref2_marker_size,
                            lw=0)
                    
            # add x and y axes labels and grid
            plt.xticks(ticks=x_ticks[::xticks_size], labels=x_labels[::xticks_size])
            axs[g].set_yticks(ticks=dfGroup.index)
            axs[g].set_yticklabels(dfGroup.task)
            #axs[g].grid(axis='x', alpha=1)     # this doesn't work for some reason

    
            # add reference line for today
            xticks_today_pos = [(p_start+datetime.timedelta(days=i)).strftime('%d-%b-%y') for i in x_ticks].index(datetime.datetime.today().strftime('%d-%b-%y'))
            axs[g].axvline(x=xticks_today_pos, linestyle='--', color='red', lw=0.5, alpha=0.75)
            
            # add chart reference line 1
            if cfg['Chart']['ChartRef1']['IsActive']:
                row_ref1_date_str = cfg['Chart']['ChartRef1']['Date']
                row_ref1_date = datetime.datetime.strptime(row_ref1_date_str, '%Y-%m-%d')
                xticks_ref1_pos = [(p_start+datetime.timedelta(days=i)).strftime('%d-%b-%y') for i in x_ticks].index(row_ref1_date.strftime('%d-%b-%y'))
                axs[g].axvline(x=xticks_ref1_pos,
                            linestyle=cfg['Chart']['ChartRef1']['MarkerStyle'],
                            color=cfg['Chart']['ChartRef1']['Colour'],
                            lw=cfg['Chart']['ChartRef1']['LineWidth'],
                            alpha=cfg['Chart']['ChartRef1']['Alpha']
                            )
                # annotate only once at the bottom
                if g==len(groups)-1:
                    axs[g].text(x=xticks_ref1_pos,
                             #y=len(df2)+1.3,
                             y=-1.3,
                             s=cfg['Chart']['ChartRef1']['Comment'],
                             color=cfg['Chart']['ChartRef1']['Colour'],
                             ha='center',
                             va='bottom',
                             size=7
                             )

            # add chart reference line 2
            if cfg['Chart']['ChartRef2']['IsActive']:
                row_ref2_date_str = cfg['Chart']['ChartRef2']['Date']
                row_ref2_date = datetime.datetime.strptime(row_ref2_date_str, '%Y-%m-%d')
                xticks_ref2_pos = [(p_start+datetime.timedelta(days=i)).strftime('%d-%b-%y') for i in x_ticks].index(row_ref2_date.strftime('%d-%b-%y'))
                axs[g].axvline(x=xticks_ref2_pos,
                            linestyle=cfg['Chart']['ChartRef2']['MarkerStyle'],
                            color=cfg['Chart']['ChartRef2']['Colour'],
                            lw=cfg['Chart']['ChartRef2']['LineWidth'],
                            alpha=cfg['Chart']['ChartRef2']['Alpha']
                            )
                # annotate only once
                if g==len(groups)-1:
                    axs[g].text(x=xticks_ref2_pos,
                             #y=len(df2)+1.3,
                             y=-1.3,
                             s=cfg['Chart']['ChartRef2']['Comment'],
                             color=cfg['Chart']['ChartRef2']['Colour'],
                             ha='center',
                             va='bottom',
                             size=7
                             )

    # rotate date
    plt.xticks(rotation=90, ha='right')
    
    # display task name on y axis / theme name on timeline
    if not cfg['Chart']['YAxisDisplayText']:
        for g in range(len(groups)):
            axs[g].axes.yaxis.set_visible(False)
    
    fig.savefig('output_separate_swimlanes.png', dpi=150, bbox_inches='tight')
    plt.show()



# main process
def main():
    # get the config from json file
    cfg = get_cfg(r'D:\Users\wleong\Documents\_personal\gantt\config_DMS.json')
    #cfg = get_cfg(r'D:\Users\wleong\Documents\_personal\gantt\config_sample.json')
    #cfg = get_cfg(r'D:\Wilson\Documents\Python Scripts\tools\gantt\config_sample.json')
    
    # load issues data & pre-process
    df = get_data(cfg)
    df = preprocess_data(cfg, df)
    
    # filter, aggregate data
    df2 = filter_agg_data(cfg, df)
    #df2.to_excel('agg_output.xlsx', index=False)
    
    # plot gantt chart & save as PNG
    generate_gantt(cfg, df2)


main()