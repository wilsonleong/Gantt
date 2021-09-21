# -*- coding: utf-8 -*-
"""
Created on Mon Sep  6 14:34:37 2021

@author: WLeong

Reference: https://medium.com/geekculture/create-an-advanced-gantt-chart-in-python-f2608a1fd6cc

"""

# Import Libraries
import data
import chart


# main process
def main():
    # get the config from json file
    #cfg = get_cfg(r'D:\Users\wleong\Documents\_personal\gantt\config_DMS.json')
    cfg = data.get_cfg(r'D:\Users\wleong\Documents\_personal\gantt\config_sample.json')
    #cfg = get_cfg(r'D:\Wilson\Documents\Python Scripts\tools\gantt\config_sample.json')
    
    # load issues data & pre-process
    df = data.get_data(cfg)
    df = data.preprocess_data(cfg, df)
    
    # filter, aggregate data
    df2 = data.filter_agg_data(cfg, df)
    #df2.to_excel('agg_output.xlsx', index=False)
    
    # plot gantt chart & save as PNG
    chart.generate_gantt(cfg, df2)


main()