'''
    filesystem constants
'''

app_data_dir = "./app_data"
ticker_data_dir = "./ticker-data"



'''
    cloud infrastructure constans
'''
app_cf_stack_names = ['app-infra-base', 'app-infra-compute']

def s3_data_bucket_export_name(app_ns):
    return "%s-data-bucket-name" % app_ns

s3_ticker_file_folder_prefix = "ticker-files"
s3_financial_cache_folder_prefix = "financial-cache"
s3_stock_recommendation_folder_prefix = "stock-recommendation"