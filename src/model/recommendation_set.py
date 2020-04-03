from datetime import datetime
import uuid 
import pytz
import dateutil.parser as parser
from exception.exceptions import ValidationError
from cloud import aws_service_wrapper
from support import constants, util
import logging

log = logging.getLogger()

class SecurityRecommendationSet():
    """
        A data structure representing a set of recommendations generated
        by a selection strategy

        It can be serialized into a json document that looks like this:
        {
            "set_id": uuid (str),
            "creation_date": ISO8601 Date - UTC Timezone,
            "analysis_start_date": ISO8601 Date - No Time component,
            "analysis_end_date": ISO8601 Date - No Time component,
            "price_date": ISO8601 Date - UTC Timezone,
            "strategy_name": str,
            "security_type": str
            "security_set": {
                "str": float,
                "str": float,
                "str": float
            }
        }

        Attributes: 
            set_id: str
                A uniquely generated ID for this set.
            creation_date : str
                Date and time this set was created. (UTC format).
            analysis_start_date : str
                The start date of the financial data used for the analysis (No time component).  
            analysis_end_date : str
                The end date of the financial data used for the analysis (No time component).
            price_date : str
                The current price date used price set of securities. (UTC format).
            strategy_name : str
                Name of the strategy used to generate this set.
            security_type
                Types of securities included in this set, e.g. "US Equities"
            security_set
                The set of securities. Represented as a map of {ticker -> current price}
    """

    def __init__(self, creation_date : datetime, analysis_start_date : datetime,
            analysis_end_date : datetime, price_date : datetime,
            strategy_name : str, security_type : str, security_set : dict):
        '''
            Initializes This class by supplying paraeters directly to it.
        '''

        def validate(*argv):
            '''
                Validates several paramters in one shot.
                Check wether params is not null and not empty
            '''
            isValid = True
            for arg in argv:  
                if arg == None or (isinstance(arg, (dict, list, str)) and len(arg) == 0):
                    isValid = False

            if isValid == False:
                raise ValidationError("One or more parameters is either null or empty: %s" % str(argv), None)
        
        
        validate(creation_date, 
                    analysis_start_date, analysis_end_date,
                    price_date, strategy_name, security_type, 
                    security_set
        )

        if not isinstance(security_set, dict):
            raise ValidationError("Security Set parameter is not a dictionary", None)
        

        self.set_id = str(uuid.uuid1())
        self.creation_date = creation_date
        self.analysis_start_date = analysis_start_date
        self.analysis_end_date = analysis_end_date
        self.price_date = price_date
        self.strategy_name = strategy_name
        self.security_type = security_type
        self.security_set = security_set


    @classmethod
    def from_dict(cls, recommendation_dict : dict):
        '''
            Initializes the class from a dictionary or raises a ValidationError
            
            Date objects are kept in UTC timezone. Clients using this data structure
            are responsible for the localization of time

            Paramters
            ---------
            recommendation_dict : dict A dictionary representation of the portfolio

            Returns
            ---------
            A SecurityRecommendationSet instance matching the dictionary

            Raises
            ---------
            ValidationError in case the dictionary is invalid 
        '''
        try:
            set_id = recommendation_dict['set_id']
            creation_date = parser.parse(recommendation_dict['creation_date'])
            analysis_start_date = parser.parse(recommendation_dict['analysis_start_date'])
            analysis_end_date = parser.parse(recommendation_dict['analysis_end_date'])
            price_date = parser.parse(recommendation_dict['price_date'])
            strategy_name = recommendation_dict['strategy_name']
            security_type = recommendation_dict['security_type']
            security_set = recommendation_dict['security_set']
            
            p = cls(creation_date, analysis_start_date, analysis_end_date, price_date,
                    strategy_name, security_type, security_set
            )

            p.set_id = set_id

            return p

        except Exception as e:
            raise ValidationError("Could not initialize Security Recommendation Set from dictionary", e)

    @classmethod
    def from_s3(cls):
        '''
            loads the recommendation set from S3. Implementation is TBD
        '''
        pass

    def to_dict(self):
        """
            serialized this object and returns it as a dictionary.

            Note that creation time and Price Date are automatically converted to UTC
        """

        return {
            "set_id": self.set_id,
            "creation_date": self.creation_date.astimezone(pytz.UTC).isoformat(),
            "analysis_start_date": self.analysis_start_date.isoformat(),
            "analysis_end_date": self.analysis_end_date.isoformat(),
            "price_date": self.price_date.astimezone(pytz.UTC).isoformat(),
            "strategy_name": self.strategy_name,
            "security_type": self.security_type,
            "security_set": self.security_set
        }

    def save_to_s3(self, app_ns : str):
        '''
            Uploads the Recommendation Set to S3

            Parameters
            ----------
            app_ns : str
                The application namespace supplied to the command line
                used to identify the appropriate CloudFormation exports
        '''
    
        s3_data_bucket_name = aws_service_wrapper.cf_read_export_value(constants.s3_data_bucket_export_name(app_ns))
        recommendation_set_object_name = "%s/%s" % (constants.s3_recommendation_set_folder_prefix, constants.s3_recommendation_set_object_name)

        log.info("Uploading Security Recommendation Set to S3")

        aws_service_wrapper.s3_upload_ascii_string(util.format_dict(self.to_dict()), s3_data_bucket_name, recommendation_set_object_name)
        
    
