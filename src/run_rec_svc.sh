#!/bin/sh
#python securities_recommendation_svc.py -ticker_file djia30.txt -output_size 3 test -analysis_year 2019 -analysis_month 8 -price_date 2019/10/30 
python securities_recommendation_svc.py -ticker_file djia30.txt -output_size 3 production -app_namespace sa