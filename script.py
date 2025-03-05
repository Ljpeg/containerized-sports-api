import boto3
import time
import subprocess

# Set Variables
AWS_ACCOUNT_ID = "443370693600"
AWS_REGION = "us-east-2"
ECR_REPO_NAME = "sports-api"
ECS_CLUSTER_NAME = "sports-api-cluster"
TASK_DEF_FAMILY = "sports-api-task-def"
SERVICE_NAME = "sports-api-service"
LOAD_BALANCER_NAME = "sports-api-lb"
TARGET_GROUP_NAME = "sports-api-tg"
HEALTH_CHECK_PATH = "/sports"
IMAGE_TAG = "sports-api-latest"

ecr_client = boto3.client('ecr', region_name=AWS_REGION)
ecs_client = boto3.client('ecs', region_name=AWS_REGION)
elb_client = boto3.client('elbv2', region_name=AWS_REGION)
api_gateway_client = boto3.client('apigateway', region_name=AWS_REGION)

# If it doens't exist, create ECR Repo and verify creation
def create_ecr_repo():
    try:
        response = ecr_client.create_repository(repositoryName=ECR_REPO_NAME)
        print("ECR Repo created successfully.")
        print(f'{response["repository"]["repositoryUri"]}')
        return response["repository"]["repositoryUri"]
    except ecr_client.exceptions.RepositoryAlreadyExistsException:
        print("ECR Repo already exists.")
        response = ecr_client.describe_repositories(
            repositoryNames=[ECR_REPO_NAME])
        print(f'{response["repositories"][0]["repositoryUri"]}')
        return response["repositories"][0]["repositoryUri"]
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        exit(1)

# Log into ECR
def login_to_ecr():
    try:
        print("Logging into ECR...")
        token = ecr_client.get_authorization_token(
        )["authorizationData"][0]["authorizationToken"]
        print(f"Token: {token}")
        registry_url = f"{AWS_ACCOUNT_ID}.dkr.ecr.{AWS_REGION}.amazonaws.com"
        subprocess.run(["docker", "login", "--username", "AWS",
                        "--password-stdin", registry_url], input=token, shell=True, text=True, check=True)
        return registry_url
    except Exception as e:
        print(f"An error occurred trying to log into ECR: {str(e)}")
        exit(1)

# Build, push, and tag Docker image
def build_and_push_docker_image(repository_uri):
    try:
        print("Building Docker image...")
        subprocess.run(["docker", "build", "--platform",
                        "linux/amd64", "-t", ECR_REPO_NAME, "."], shell=True, check=True)

        print("Tagging Docker image...")
        tagged_image = f"{repository_uri}:{IMAGE_TAG}"
        subprocess.run(
            ["docker", "tag", f"{ECR_REPO_NAME}:latest", tagged_image], shell=True, check=True)

        print("Pushing Docker image...")
        subprocess.run(["docker", "push", tagged_image],
                      shell=True, check=True)
    except Exception as e:
        print(
            f"An error occurred trying to build, push, or tag Docker image: {str(e)}")
        exit(1)


print("Starting deployment...")
repository_uri = create_ecr_repo()
print(f"Repository URI: {repository_uri}")

print("Attempting to log into ECR...")
registry_url = login_to_ecr()
print(f"Logged in to Registry: {registry_url}")

print("Starting to configure Docker image...")
build_and_push_docker_image(repository_uri)
print("Docker image configured successfully.")
