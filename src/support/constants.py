'''
    filesystem constants
'''

APP_DATA_DIR = "./app_data"
TICKER_DATA_DIR = "./ticker-data"
FINANCIAL_DATA_DIR = "./financial-data/"


'''
    Application constnts
'''



'''
    Cloud Infrastructure Constants
'''
APP_CF_STACK_NAMES = ['app-infra-base', 'app-infra-compute']

def s3_data_bucket_export_name(app_ns):
    return "%s-data-bucket-name" % app_ns

S3_TICKER_FILE_FOLDER_PREFIX = "ticker-files"
S3_RECOMMENDATION_SET_FOLDER_PREFIX = "base-recommendations"
S3_RECOMMENDATION_SET_OBJECT_NAME = "security-recommendation-set.json"
S3_PORTFOLIO_FOLDER_PREFIX = "portfolios"
S3_PORTFOLIO_OBJECT_NAME = "current-portfolio.json"
S3_FINANCIAL_CACHE_FOLDER_PREFIX = "financial-cache"

def sns_app_notifications_topic_arn(app_ns):
    return "%s-app-notifications-topic-name" % app_ns