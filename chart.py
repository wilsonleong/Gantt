# -*- coding: utf-8 -*-
"""
Created on Mon Sep 20 17:17:09 2021

@author: WLeong
"""

import datetime
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors


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
            # only plot if task name is displayed on y-axis instead of on the timeline bar
            if cfg['Chart']['YAxisDisplayText']:
                plt.text(x=df2.rel_start[i]+df2.w_comp[i],
                         y=yticks[i],
                         s=comment_str,
                         verticalalignment='center',
                         color='gray')
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
        
        # add theme display text
        if not cfg['Chart']['YAxisDisplayText']:
            plt.text(x=df2.rel_start[i],
                     y=yticks[i],
                     s=df2.task[i],
                     color='black',
                     verticalalignment='center'
                     )

        # plot row reference date 1 (optional data field)
        ref1_date = cfg['InputFile']['ColName_Ref1_Date']
        ref1_marker_style = cfg['Chart']['RowRef1']['MarkerStyle']
        ref1_marker_colour = cfg['Chart']['RowRef1']['MarkerColour']
        ref1_marker_edgewidth = cfg['Chart']['RowRef1']['MarkerEdgeWidth']
        ref1_marker_size = cfg['Chart']['RowRef1']['MarkerSize']
        if ref1_date is not None:
            if not pd.isnull(df2[ref1_date][i]):
                ax.plot(df2.rel_ref1_date[i],                 # this x-axis needs to be relative to the chart start date
                        yticks[i],
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
    
    # add chart reference line 1
    row_ref1_date_str = cfg['Chart']['ChartRef1']['Date']
    if row_ref1_date_str is not None:
        row_ref1_date = datetime.datetime.strptime(row_ref1_date_str, '%Y-%m-%d')
        xticks_ref1_pos = [(p_start+datetime.timedelta(days=i)).strftime('%d-%b-%y') for i in x_ticks].index(row_ref1_date.strftime('%d-%b-%y'))
        plt.axvline(x=xticks_ref1_pos,
                    linestyle=cfg['Chart']['ChartRef1']['MarkerStyle'],
                    color=cfg['Chart']['ChartRef1']['Colour'],
                    lw=cfg['Chart']['ChartRef1']['LineWidth'],
                    alpha=cfg['Chart']['ChartRef1']['Alpha']
                    )
        plt.text(x=xticks_ref1_pos,
                 y=len(df2) + 0.6,
                 s=cfg['Chart']['ChartRef1']['Comment'],
                 color=cfg['Chart']['ChartRef1']['Colour'],
                 ha='center',
                 va='bottom',
                 size=7
                 )

    # add chart reference line 2
    row_ref2_date_str = cfg['Chart']['ChartRef2']['Date']
    if row_ref2_date_str is not None:
        row_ref2_date = datetime.datetime.strptime(row_ref2_date_str, '%Y-%m-%d')
        xticks_ref2_pos = [(p_start+datetime.timedelta(days=i)).strftime('%d-%b-%y') for i in x_ticks].index(row_ref2_date.strftime('%d-%b-%y'))
        plt.axvline(x=xticks_ref2_pos,
                    linestyle=cfg['Chart']['ChartRef2']['MarkerStyle'],
                    color=cfg['Chart']['ChartRef2']['Colour'],
                    lw=cfg['Chart']['ChartRef2']['LineWidth'],
                    alpha=cfg['Chart']['ChartRef2']['Alpha']
                    )
        plt.text(x=xticks_ref2_pos,
                 y=len(df2) + 0.6,
                 s=cfg['Chart']['ChartRef2']['Comment'],
                 color=cfg['Chart']['ChartRef2']['Colour'],
                 ha='center',
                 va='bottom',
                 size=7
                 )

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
    
    # display task name on y axis / theme name on timeline
    if not cfg['Chart']['YAxisDisplayText']:
        ax.axes.yaxis.set_visible(False)
    
    fig.savefig('output.png', dpi=150, bbox_inches='tight')
    plt.show()