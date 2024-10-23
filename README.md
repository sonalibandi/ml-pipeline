# End-to-End Machine Learning Pipeline: GitHub Actions and AWS SageMaker Integration

This repository demonstrates a CI/CD pipeline for building, training, and deploying machine learning models using **GitHub Actions** and **AWS SageMaker**. The pipeline automatically builds Docker images, pushes them to **Amazon ECR**, triggers SageMaker training jobs, and deploys the trained model to an endpoint.

## Architecture Outline

1. **Code Push to GitHub**
   - Developer pushes code changes to the `dev` or `main` branch.
   - This triggers a GitHub Actions workflow.

2. **CI Pipeline for Docker Build (Dev Branch)**
   - On the `dev` branch:
     - GitHub Actions builds the Docker image using the `Dockerfile`.
     - The image is pushed to **Amazon ECR** (Elastic Container Registry).

3. **SageMaker Training Job**
   - The Docker image is used to start a SageMaker training job.
   - Training and validation data are retrieved from **S3**.
   - After training, the model is saved to **S3**.

4. **Model Deployment (Main Branch)**
   - On the `main` branch:
     - The pipeline triggers the deployment of the trained model to a **SageMaker endpoint** using `deploy.py`.

5. **SageMaker Endpoint**
   - The trained model is deployed to a SageMaker endpoint.
   - The endpoint is available for real-time predictions.

## Setup Instructions

### Prerequisites
- AWS account with access to SageMaker, ECR, and S3.
- GitHub repository with Actions enabled.
- AWS CLI installed and configured.
- Docker installed locally.

### GitHub Secrets

Ensure the following secrets are set up in your GitHub repository:

- `AWS_ACCESS_KEY_ID`: Your AWS Access Key ID.
- `AWS_SECRET_ACCESS_KEY`: Your AWS Secret Access Key.
- `REPO_NAME`: Name of your Amazon ECR repository.
- `BUCKET_NAME`: Name of your S3 bucket for model artifacts.


