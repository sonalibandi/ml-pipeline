#!/usr/bin/env python

import os
import pandas as pd
import boto3
import botocore
from sagemaker.estimator import Estimator

# Replace with your desired configuration
initial_instance_count = 1
endpoint_instance_type = 'ml.m5.large'

BUCKET_NAME = 'sample-sagemaker-cicd1'
PREFIX = 'boston-housing-regression'
OBJECT_KEY = f'{PREFIX}/reports.csv'

# Ensure the AWS region is set
region = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')

# Initialize the S3 resource
s3 = boto3.resource('s3', region_name=region)

try:
    # Try to download the reports.csv from S3
    s3.Bucket(BUCKET_NAME).download_file(OBJECT_KEY, 'reports.csv')
    
    # Load the CSV into a DataFrame
    reports_df = pd.read_csv('reports.csv')
    print("Successfully loaded reports.csv")
    print(reports_df)

    # Ensure 'date_time' and 'training_job_name' columns exist
    if 'date_time' in reports_df.columns and 'training_job_name' in reports_df.columns:
        # Convert the 'date_time' column to datetime format
        reports_df['date_time'] = pd.to_datetime(reports_df['date_time'], format='%Y-%m-%d %H:%M:%S')
        
        # Get the latest training job name by sorting the dataframe
        latest_training_job_name = reports_df.sort_values('date_time', ascending=False).iloc[0]['training_job_name']
        print(f"Latest Training Job: {latest_training_job_name}")
        
        # Attach to the latest training job using SageMaker Estimator
        attached_estimator = Estimator.attach(latest_training_job_name)

        # Deploy the attached estimator to create a new endpoint
        attached_predictor = attached_estimator.deploy(
            initial_instance_count=initial_instance_count,
            instance_type=endpoint_instance_type,
            endpoint_name=latest_training_job_name,
            tags=[{"Key": "email", "Value": "bandi.so+dev@northeastern.edu"}],
            wait=False
        )
        print(f"Endpoint Name: {attached_predictor.endpoint_name}")
    else:
        print("Required columns 'date_time' or 'training_job_name' not found in reports.csv")

except botocore.exceptions.ClientError as e:
    # Handle the case where the file is not found or another S3 error occurs
    if e.response['Error']['Code'] == '404':
        print("reports.csv not found in S3!")
    else:
        print(f"Unexpected error: {e}")
        raise

except Exception as e:
    # General error handling for other issues like pandas, SageMaker, etc.
    print(f"An error occurred: {e}")
    raise
