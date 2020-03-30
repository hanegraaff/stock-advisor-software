import boto3
from exception.exceptions import ValidationError, AWSError
from support import util
"""
This module wraps the boto SDK an offers the following value add to the application:

    1) simplify AWS responses and make them easier to use.
    2) Use paginators when available and combine results.
    2) Automatically catch AWS exceptions and rethrow them as a custom exception
    3) Provide filtering options that are meaningful to the application
"""

#Global clients available to this module
cf_client = boto3.client('cloudformation')
s3_client = boto3.client('s3')


def cf_list_exports(stack_name_filter : list):
    '''
        Reads all ClouFormation exports and returns only the ones
        included in the stack_name_filter list

        Parmeters
        ---------
        stack_name_filter : list
            A list of strings representing the names of the stacks used as a filter

        Returns
        ---------
        A dictionary {export_name, export_value} with the filtered values. e.g.

        {
            'export-name-1': 'value1',
            'export-name-2': 'value2',
        }
    '''
    def get_stackname_from_stackarn(arn: str):
        
        #arn:aws:cloudformation:region:acct:stack/app-infra-base/c9481160-6df5-11ea-ac9f-121b58656156
        try:
            arn_elements = arn.split(':')
            stack_id = arn_elements[5]

            stack_elements = stack_id.split("/")
            return stack_elements[1]    
        except Exception as e:
            raise ValidationError("Could not parse stack ID from arn", e)
    
    if stack_name_filter == None:
        stack_name_filter = []

    return_dict = {}
    try:
        paginator = cf_client.get_paginator('list_exports')
        response_iterator = paginator.paginate()

        for page in response_iterator:
            for export in page['Exports']:
                stack_name = get_stackname_from_stackarn(export['ExportingStackId'])
                if (stack_name in stack_name_filter):
                    return_dict[export['Name']] = export['Value']

        return return_dict

    except Exception as e:
        raise AWSError("Could not list Cloudformation exports", e)

def s3_download_object(bucket_name : str, object_name : str, dest_path : str):
    '''
        Downloads an s3 object to the local filesystem and saves it to 
        the destination path (path + filename)
    '''
    try:
        s3_client.download_file(bucket_name, object_name, dest_path)
    except Exception as e:
        raise AWSError("Could not download s3://%s/%s --> %s" % (bucket_name, object_name, dest_path), e)


def s3_upload_object(source_path : str, bucket_name : str, object_name : str):
    '''
        Uploads a file from the source_path (path + file) to the destination bucket
    '''
    try:
        s3_client.upload_file(source_path, bucket_name, object_name)
    except Exception as e:
        raise AWSError("Could not upload %s --> s3://%s/%s" % (source_path, bucket_name, object_name), e)
