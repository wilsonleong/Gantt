# -*- coding: utf-8 -*-
"""
Created on Mon Sep 20 17:17:09 2021

@author: WLeong
"""

import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as patches
import numpy as np


# plot gantt chart and save as PNG
def generate_gantt(cfg, df2):
    time_now = datetime.datetime.now()
    # import data from CFG file
    chart_start_date = datetime.datetime.strptime(cfg['Chart']['ChartStartDate'],'%Y-%m-%d')
    chart_title = cfg['Chart']['ChartTitle'] + str(" - %s" % datetime.datetime.strftime(time_now, '%Y-%m-%d %H:%M:%S'))
    xticks_size = cfg['Chart']['XAxisMajor_NoOfDays']
    
    # if data was aggregated, legend will need to be forced
    if cfg['DataSelection']['Aggregation']['IsActive']:
        aggby = cfg['DataSelection']['Aggregation']['AggregateBy'][0]
        chart_legend_title = aggby
        chart_legend_by = aggby
    else:
        #chart_legend_title = cfg['Chart']['LegendTitle']
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

    fig, ax = plt.subplots(1,1, figsize=(cfg['OutputFile']['WidthInInch'],cfg['OutputFile']['HeightInInch']))
    plt.title(chart_title, size=14)
    
    # plot each issue row by row
    for i in range(len(df2)):
        color = c_dict[df2[chart_legend_by][i]]

        # if completion % is available, add value label
        if cfg['InputFile']['ColumnNameMapping']['Completion'] is not None:
            alpha_completed = 0.4
            if df2.comment[i]=='':
                #comment_str = f"{df2[cfg['InputFile']['ColumnNameMapping']['Completion']][i]}%"
                comment_str = str(df2[cfg['InputFile']['ColumnNameMapping']['Completion']][i].astype(np.int64)) + "%"
            else:
                #comment_str = f"{df2[cfg['InputFile']['ColumnNameMapping']['Completion']][i]}%" + ' - %s' % df2.comment[i]
                comment_str = str(df2[cfg['InputFile']['ColumnNameMapping']['Completion']][i].astype(np.int64)) + "%" + ' - %s' % df2.comment[i]
            # only plot if task name is displayed on y-axis instead of on the timeline bar
            if cfg['Chart']['YAxisDisplayText']:
                plt.text(x=df2.rel_start[i]+df2.w_comp[i],
                         y=yticks[i],
                         s=comment_str,
                         verticalalignment='center',
                         color='gray',
                         fontsize=7)
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
        if cfg['Chart']['RowRef1']['IsActive']:
            ref1_date = cfg['InputFile']['ColumnNameMapping']['Ref1_Date']
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
        if cfg['Chart']['RowRef2']['IsActive']:
            ref2_date = cfg['InputFile']['ColumnNameMapping']['Ref2_Date']
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
    plt.yticks(ticks=yticks, labels=df2.task, fontsize=9)
    plt.grid(axis='x', alpha=0.1)
    
    # add reference line for today
    xticks_today_pos = [(p_start+datetime.timedelta(days=i)).strftime('%d-%b-%y') for i in x_ticks].index(datetime.datetime.today().strftime('%d-%b-%y'))
    plt.axvline(x=xticks_today_pos, linestyle='--', color='red', lw=0.5, alpha=0.75)
    
    #ref_line_position = 3
    ref_line_position = cfg['Chart']['ChartRefLine']['Position']
    ref_line_fontsize = cfg['Chart']['ChartRefLine']['FontSize']
    ref_line_va = cfg['Chart']['ChartRefLine']['VerticalAlignment']
    
    # add Quarter Separators
    if cfg['Chart']['QuarterSeparators']['IsActive']:
        # take earliest start date (p_start), work out next quarter, check if its before the latest end date (p_end)
        def get_quarter(p_date: datetime.date) -> int:
            return (p_date.month - 1) // 3 + 1
        
        def get_first_day_of_the_quarter(p_date: datetime.date):
            return datetime.datetime(p_date.year, 3 * ((p_date.month - 1) // 3) + 1, 1)
        
        def get_last_day_of_the_quarter(p_date: datetime.date):
            quarter = get_quarter(p_date)
            return datetime.datetime(p_date.year + 3 * quarter // 12, 3 * quarter % 12 + 1, 1) + datetime.timedelta(days=-1)

        # identify the lines that need to be plotted
        quarter_dates = []
        next_q_date = get_last_day_of_the_quarter(p_start) + datetime.timedelta(days=1)
        next_q_date = next_q_date.date()
        if p_start==next_q_date:
            next_q_date = get_last_day_of_the_quarter(p_start + datetime.timedelta(days=1)).date()
        final_q_date = get_first_day_of_the_quarter(p_end)
        final_q_date = final_q_date.date()
        
        while next_q_date <= final_q_date:
            quarter_dates.append(next_q_date)
            next_q_date = next_q_date + relativedelta(months=3)
        
        # plot each of the dates
        for d in range(len(quarter_dates)):
            qdate = quarter_dates[d]
            xticks_qdate_pos = [(p_start+datetime.timedelta(days=i)).strftime('%d-%b-%y') for i in x_ticks].index(qdate.strftime('%d-%b-%y'))
            # plot the line
            plt.axvline(x = xticks_qdate_pos,
                        linestyle = cfg['Chart']['QuarterSeparators']['LineStyle'],
                        color = cfg['Chart']['QuarterSeparators']['Colour'],
                        lw = cfg['Chart']['QuarterSeparators']['LineWidth'],
                        alpha = cfg['Chart']['QuarterSeparators']['Alpha'],
                        )
            # annotate
            if qdate.month==1:
                qdate_text = 'End of %s' % (qdate - datetime.timedelta(days=1)).year
            else:
                qdate_text = 'Q%s' % get_quarter(qdate)
                
            plt.text(
                x = xticks_qdate_pos,
                y = len(df2) + ref_line_position,
                s = qdate_text,
                color = cfg['Chart']['QuarterSeparators']['Colour'],
                ha = 'center',
                va = ref_line_va,
                size = ref_line_fontsize
                )












    
    # add chart reference line 1
    if cfg['Chart']['ChartRef1']['IsActive']:
        row_ref1_date_str = cfg['Chart']['ChartRef1']['Date']
        row_ref1_date = datetime.datetime.strptime(row_ref1_date_str, '%Y-%m-%d')
        xticks_ref1_pos = [(p_start+datetime.timedelta(days=i)).strftime('%d-%b-%y') for i in x_ticks].index(row_ref1_date.strftime('%d-%b-%y'))
        plt.axvline(x=xticks_ref1_pos,
                    linestyle=cfg['Chart']['ChartRef1']['LineStyle'],
                    color=cfg['Chart']['ChartRef1']['Colour'],
                    lw=cfg['Chart']['ChartRef1']['LineWidth'],
                    alpha=cfg['Chart']['ChartRef1']['Alpha']
                    )
        plt.text(x=xticks_ref1_pos,
                 y=len(df2) + ref_line_position,
                 s=cfg['Chart']['ChartRef1']['Comment'],
                 color=cfg['Chart']['ChartRef1']['Colour'],
                 ha='center',
                 va=ref_line_va,
                 size=ref_line_fontsize
                 )

    # add chart reference line 2
    if cfg['Chart']['ChartRef2']['IsActive']:
        row_ref2_date_str = cfg['Chart']['ChartRef2']['Date']
        row_ref2_date = datetime.datetime.strptime(row_ref2_date_str, '%Y-%m-%d')
        xticks_ref2_pos = [(p_start+datetime.timedelta(days=i)).strftime('%d-%b-%y') for i in x_ticks].index(row_ref2_date.strftime('%d-%b-%y'))
        plt.axvline(x=xticks_ref2_pos,
                    linestyle=cfg['Chart']['ChartRef2']['LineStyle'],
                    color=cfg['Chart']['ChartRef2']['Colour'],
                    lw=cfg['Chart']['ChartRef2']['LineWidth'],
                    alpha=cfg['Chart']['ChartRef2']['Alpha']
                    )
        plt.text(x=xticks_ref2_pos,
                 y=len(df2) + ref_line_position,
                 s=cfg['Chart']['ChartRef2']['Comment'],
                 color=cfg['Chart']['ChartRef2']['Colour'],
                 ha='center',
                 va=ref_line_va,
                 size=ref_line_fontsize
                 )


    # add chart reference line 3
    if cfg['Chart']['ChartRef3']['IsActive']:
        row_ref3_date_str = cfg['Chart']['ChartRef3']['Date']
        row_ref3_date = datetime.datetime.strptime(row_ref3_date_str, '%Y-%m-%d')
        xticks_ref3_pos = [(p_start+datetime.timedelta(days=i)).strftime('%d-%b-%y') for i in x_ticks].index(row_ref3_date.strftime('%d-%b-%y'))
        plt.axvline(x=xticks_ref3_pos,
                    linestyle=cfg['Chart']['ChartRef3']['LineStyle'],
                    color=cfg['Chart']['ChartRef3']['Colour'],
                    lw=cfg['Chart']['ChartRef3']['LineWidth'],
                    alpha=cfg['Chart']['ChartRef3']['Alpha']
                    )
        plt.text(x=xticks_ref3_pos,
                 y=len(df2) + ref_line_position,
                 s=cfg['Chart']['ChartRef3']['Comment'],
                 color=cfg['Chart']['ChartRef3']['Colour'],
                 ha='center',
                 va=ref_line_va,
                 size=ref_line_fontsize
                 )

    # add chart reference line 4
    if cfg['Chart']['ChartRef4']['IsActive']:
        row_ref4_date_str = cfg['Chart']['ChartRef4']['Date']
        row_ref4_date = datetime.datetime.strptime(row_ref4_date_str, '%Y-%m-%d')
        xticks_ref4_pos = [(p_start+datetime.timedelta(days=i)).strftime('%d-%b-%y') for i in x_ticks].index(row_ref4_date.strftime('%d-%b-%y'))
        plt.axvline(x=xticks_ref4_pos,
                    linestyle=cfg['Chart']['ChartRef4']['LineStyle'],
                    color=cfg['Chart']['ChartRef4']['Colour'],
                    lw=cfg['Chart']['ChartRef4']['LineWidth'],
                    alpha=cfg['Chart']['ChartRef4']['Alpha']
                    )
        plt.text(x=xticks_ref4_pos,
                 y=len(df2) + ref_line_position,
                 s=cfg['Chart']['ChartRef4']['Comment'],
                 color=cfg['Chart']['ChartRef4']['Colour'],
                 ha='center',
                 va=ref_line_va,
                 size=ref_line_fontsize
                 )

    # add chart reference line 5
    if cfg['Chart']['ChartRef5']['IsActive']:
        row_ref5_date_str = cfg['Chart']['ChartRef5']['Date']
        row_ref5_date = datetime.datetime.strptime(row_ref2_date_str, '%Y-%m-%d')
        xticks_ref5_pos = [(p_start+datetime.timedelta(days=i)).strftime('%d-%b-%y') for i in x_ticks].index(row_ref5_date.strftime('%d-%b-%y'))
        plt.axvline(x=xticks_ref5_pos,
                    linestyle=cfg['Chart']['ChartRef5']['LineStyle'],
                    color=cfg['Chart']['ChartRef5']['Colour'],
                    lw=cfg['Chart']['ChartRef5']['LineWidth'],
                    alpha=cfg['Chart']['ChartRef5']['Alpha']
                    )
        plt.text(x=xticks_ref5_pos,
                 y=len(df2) + ref_line_position,
                 s=cfg['Chart']['ChartRef5']['Comment'],
                 color=cfg['Chart']['ChartRef5']['Colour'],
                 ha='center',
                 va=ref_line_va,
                 size=ref_line_fontsize
                 )
    
    # add grey out period 1
    if cfg['Chart']['GreyOutPeriod1']['IsActive']:
        period_date_from = cfg['Chart']['GreyOutPeriod1']['DateFrom']
        period_date_to = cfg['Chart']['GreyOutPeriod1']['DateTo']
        xaxis_start_pos = datetime.datetime.strptime(period_date_from, '%Y-%m-%d') - p_start
        xaxis_no_of_days = datetime.datetime.strptime(period_date_to, '%Y-%m-%d') - datetime.datetime.strptime(period_date_from, '%Y-%m-%d')
        rect = patches.Rectangle((xaxis_start_pos.days, -2),
                                 xaxis_no_of_days.days, len(df2)+3,
                                 linewidth=1,
                                 edgecolor='none',
                                 facecolor=cfg['Chart']['GreyOutPeriod1']['Colour'],
                                 alpha=cfg['Chart']['GreyOutPeriod2']['Alpha'])
        plt.text(x=xaxis_start_pos.days + xaxis_no_of_days.days/2,
                 #y=len(df2),
                 y=0-1,
                 s=cfg['Chart']['GreyOutPeriod1']['DisplayText'],
                 color=cfg['Chart']['GreyOutPeriod1']['DisplayTextColour'],
                 fontsize=cfg['Chart']['GreyOutPeriod1']['DisplayTextFontSize'],
                 ha='center',
                 va='bottom'
                 )
        ax.add_patch(rect)

    # add grey out period 2
    if cfg['Chart']['GreyOutPeriod2']['IsActive']:
        period_date_from = cfg['Chart']['GreyOutPeriod2']['DateFrom']
        period_date_to = cfg['Chart']['GreyOutPeriod2']['DateTo']
        xaxis_start_pos = datetime.datetime.strptime(period_date_from, '%Y-%m-%d') - p_start
        xaxis_no_of_days = datetime.datetime.strptime(period_date_to, '%Y-%m-%d') - datetime.datetime.strptime(period_date_from, '%Y-%m-%d')
        rect = patches.Rectangle((xaxis_start_pos.days, -2),
                                 xaxis_no_of_days.days, len(df2)+3,
                                 linewidth=1,
                                 edgecolor='none',
                                 facecolor=cfg['Chart']['GreyOutPeriod2']['Colour'],
                                 alpha=cfg['Chart']['GreyOutPeriod2']['Alpha'])
        plt.text(x=xaxis_start_pos.days + xaxis_no_of_days.days/2,
                 #y=len(df2),
                 y=0-1,
                 s=cfg['Chart']['GreyOutPeriod2']['DisplayText'],
                 color=cfg['Chart']['GreyOutPeriod2']['DisplayTextColour'],
                 fontsize=cfg['Chart']['GreyOutPeriod2']['DisplayTextFontSize'],
                 ha='center',
                 va='bottom'
                 )
        ax.add_patch(rect)

    # add grey out period 3
    if cfg['Chart']['GreyOutPeriod3']['IsActive']:
        period_date_from = cfg['Chart']['GreyOutPeriod3']['DateFrom']
        period_date_to = cfg['Chart']['GreyOutPeriod3']['DateTo']
        xaxis_start_pos = datetime.datetime.strptime(period_date_from, '%Y-%m-%d') - p_start
        xaxis_no_of_days = datetime.datetime.strptime(period_date_to, '%Y-%m-%d') - datetime.datetime.strptime(period_date_from, '%Y-%m-%d')
        rect = patches.Rectangle((xaxis_start_pos.days, -2),
                                 xaxis_no_of_days.days, len(df2)+3,
                                 linewidth=1,
                                 edgecolor='none',
                                 facecolor=cfg['Chart']['GreyOutPeriod3']['Colour'],
                                 alpha=cfg['Chart']['GreyOutPeriod3']['Alpha'])
        plt.text(x=xaxis_start_pos.days + xaxis_no_of_days.days/2,
                 #y=len(df2),
                 y=0-1,
                 s=cfg['Chart']['GreyOutPeriod3']['DisplayText'],
                 color=cfg['Chart']['GreyOutPeriod3']['DisplayTextColour'],
                 fontsize=cfg['Chart']['GreyOutPeriod3']['DisplayTextFontSize'],
                 ha='center',
                 va='bottom'
                 )
        ax.add_patch(rect)
    
    #fix legends
    handles, labels = plt.gca().get_legend_handles_labels()
    handle_list, label_list = [], []
    for handle, label in zip(handles, labels):
        if label not in label_list:
            handle_list.append(handle)
            label_list.append(label)
    plt.legend(handle_list, label_list, fontsize=9, 
               title=chart_legend_by, title_fontsize=9)
    
    # rotate date
    plt.xticks(rotation=90, ha='right', fontsize=7)
    
    # display task name on y axis / theme name on timeline
    if not cfg['Chart']['YAxisDisplayText']:
        ax.axes.yaxis.set_visible(False)
    
    fig.savefig(cfg['OutputFile']['FileName'], dpi=cfg['OutputFile']['DotsPerInch'], bbox_inches='tight')
    plt.show()