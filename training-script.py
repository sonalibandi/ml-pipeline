#!/usr/bin/env python
import os
import joblib
import requests
import time
import json
from datetime import datetime, timezone
import logging 


import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
import boto3
import botocore

# Configure logging
logging.basicConfig(level=logging.INFO)


def update_report_file(metrics_dictionary: dict, hyperparameters: dict,
                       commit_hash: str, training_job_name: str,
                       prefix: str, bucket_name: str,) -> None:
    """This funtion update the report file located in the S3 bucket according to the provided metrics
    if report file doesn't exist, it will create a template based on metrics_dictionary schema and upload it to S3
    Args:
        metrics_dictionary (dict): the training job metrics with this format: {"Metric_1_Name": "Metric_1_Value", ...}
        hyperparameters (dict): the training job hyperparameters with this format: {"Hyperparameter_1_Name": "Hyperparameter_1_Value", ...}
        commit_hash (str): the 7 digit hash of the commit that started this training job
        training_job_name (str): name of the current training job
        prefix (str): name of the folder in the S3 bucket
        bucket_name (str): name of the S3 bucket
    Returns:
        None
    """
    object_key = f'{prefix}/reports.csv'

    s3 = boto3.resource('s3')

    try:
        logging.info(f"Attempting to download {object_key} from S3 bucket {bucket_name}")
        s3.Bucket(bucket_name).download_file(object_key, 'reports.csv')

        # Load reports df
        reports_df = pd.read_csv('reports.csv')

    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == '404':
            logging.info(f"reports.csv not found in S3 at {bucket_name}/{object_key}. Creating a new template.")
            columns = ['date_time', 'hyperparameters', 'commit_hash',
                       'training_job_name'] + list(metrics_dictionary.keys())
            pd.DataFrame(columns=columns).to_csv('./reports.csv', index=False)

            # Upload template reports df
            logging.info(f"Uploading the newly created reports.csv to S3: {bucket_name}/{object_key}")
            s3.Bucket(bucket_name).upload_file('./reports.csv', object_key)

            # Load reports df
            reports_df = pd.read_csv('./reports.csv')
          
        elif e.response['Error']['Code'] == 'AccessDenied':
            logging.error(f"Access denied to S3 bucket {bucket_name}. Check IAM permissions.")
            raise

        else:
            logging.error(f"Unexpected error: {e}")
            raise

    # Add new report to reports.csv
    # Use UTC time to avoid timezone heterogeneity
    date_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # Add new row
    new_row = dict({'date_time': date_time, 'hyperparameters': json.dumps(hyperparameters), 'commit_hash': commit_hash, 'training_job_name': training_job_name},
                   **metrics_dictionary)
    new_report = pd.DataFrame([new_row])
   # Concatenate the new report to the existing reports_df
    reports_df = pd.concat([reports_df, new_report], ignore_index=True)

    # Upload new reports dataframe
    reports_df.to_csv('./reports.csv', index=False)
    s3.Bucket(bucket_name).upload_file('./reports.csv', object_key)


# Define main training function
def main():
  try:
    with open('/opt/ml/input/config/hyperparameters.json', 'r') as json_file:
        hyperparameters = json.load(json_file)
        print(hyperparameters)

    with open('/opt/ml/input/config/inputdataconfig.json', 'r') as json_file:
        inputdataconfig = json.load(json_file)
    print(inputdataconfig)

    with open('/opt/ml/input/config/resourceconfig.json', 'r') as json_file:
        resourceconfig = json.load(json_file)
    print(resourceconfig)

    # Load Data
    training_data_path = '/opt/ml/input/data/training'
    validation_data_path = '/opt/ml/input/data/validation'
    training_data = pd.read_csv(os.path.join(
        training_data_path, 'train.csv'))
    validation_data = pd.read_csv(os.path.join(
        validation_data_path, 'valid.csv'))

    print(training_data)
    print(validation_data)

    X_train, y_train = training_data.iloc[:,
                                          1:].values, training_data.iloc[:, :1].values
    X_val, y_val = validation_data.iloc[:,
                                        1:].values, validation_data.iloc[:, :1].values

    # Fit the model
    #hardcoded the value to 10 
    n_estimators = 10
    model = RandomForestRegressor(n_estimators=n_estimators)
    model.fit(X_train, y_train)

    # Evaluate model
    train_mse = mean_squared_error(model.predict(X_train), y_train)
    val_mse = mean_squared_error(model.predict(X_val), y_val)

    metrics_dictionary = {'Train_MSE': train_mse,
                          'Validation_MSE': val_mse,}
    metrics_dataframe = pd.DataFrame(metrics_dictionary, index=[0])

    print(metrics_dictionary)
    
    # Save the model
    model_path = '/opt/ml/model'
    model_path_full = os.path.join(model_path, 'model.joblib')
    joblib.dump(model, model_path_full)

    
    # Update the Report File
    REGION = os.environ['REGION']
    PREFIX = os.environ['PREFIX']
    BUCKET_NAME = os.environ['BUCKET_NAME']
    GITHUB_SHA = os.environ['GITHUB_SHA']
    TRAINING_JOB_NAME = os.environ['TRAINING_JOB_NAME']

    if not all([REGION, PREFIX, BUCKET_NAME, GITHUB_SHA, TRAINING_JOB_NAME]):
            logging.error("One or more environment variables are missing. Cannot update report.")
            return

    update_report_file(metrics_dictionary=metrics_dictionary, hyperparameters=hyperparameters,
                       commit_hash=GITHUB_SHA, training_job_name=TRAINING_JOB_NAME, prefix=PREFIX, bucket_name=BUCKET_NAME)
  except Exception as e:
        logging.error(f"Error during training: {e}")
        raise

if __name__ == '__main__':
    main()
