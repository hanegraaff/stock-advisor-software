'''
    Author: Mark Hanegraaff

    A Utility script that will encode (decode) a URL encoded (decoded) string
'''

import urllib.parse
import argparse
import logging
import urllib.parse
from exception.exceptions import ValidationError
from support import logging_definition

log = logging.getLogger()


def parse_params():
    """
        Parse command line parameters

        Returns
        ----------
        A String containing the mode (encode/decode) of the app

    """

    description = """ Utility script with the ability to URL encode (decode) a
                URL encoded (decoded) string
              """

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "-mode", help="The mode of the script. allowed values are 'encode' or 'decode'", type=str, required=True)
    parser.add_argument(
        "-string", help="the string to be converted", type=str, required=True)

    args = parser.parse_args()

    mode = args.mode
    string = args.string

    if mode.lower() not in ['encode', 'decode']:
        raise ValidationError(
            "Invalid mode supplied. Allowed values are: 'encode', 'decode'", None)

    return (mode, string)


def main():
    """
        Main function for this script
    """
    (mode, string) = parse_params()

    if mode == 'encode':
        log.info("Encoding: %s" % string)
        log.info("Results: %s" % urllib.parse.quote(string))
    else:
        log.info("Decoding: %s" % string)
        log.info("Results: %s" % urllib.parse.unquote(string))

if __name__ == "__main__":
    main()
