"""Author: Mark Hanegraaff -- 2020
"""
from abc import ABC, abstractmethod
import logging
import configparser
from support import constants
from exception.exceptions import ValidationError
from support.configuration import Configuration
from model.ticker_list import TickerList


class BaseStrategy(ABC):
    '''
        Base class for all trading strategies. Acts as an interface and
        ensures that certain method signatures exist.

        Attributes:
            STRATEGY_NAME: The display name associated with this strategy
            CONFIG_SECTION: The name of the configuration section in
                /config/strategies.ini
            S3_RECOMMENDATION_SET_OBJECT_NAME: The S3 object name used to store
                the recommendation set.

    '''

    STRATEGY_NAME = ""
    CONFIG_SECTION = ""
    S3_RECOMMENDATION_SET_OBJECT_NAME = ""

    @classmethod
    @abstractmethod
    def from_configuration(cls, configuration: object, app_ns: str):
        '''
            Every Strategy must have the ability to be initialized from a local
            configuration file. This is how strategies must be intialzied in
            production. Specific strategies should also offer traditional
            contstructors can be used for backtesting purposes.

            Parameters
            ----------
            configuration: Configuration
                Configuration object used to initialize this class
            app_ns: str
                Application namespace used to identify

        '''
        pass

    @abstractmethod
    def generate_recommendation(self):
        '''
            Generates a recommendation object and sets the value of the

            self.recommendation_set

            member variable
        '''
        pass

    @abstractmethod
    def display_results(self):
        pass
