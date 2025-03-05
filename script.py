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
EXECUTION_ROLE_ARN = "arn:aws:iam::443370693600:role/ecsTaskExecutionRole"
SUBNETS = ["subnet-023863d2535821480", "subnet-0eeb018c552f1801c", "subnet-072732b43c768c4fb"]

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
        registry_url = f"{AWS_ACCOUNT_ID}.dkr.ecr.{AWS_REGION}.amazonaws.com"
        subprocess.run(f"aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin {registry_url}", check=True, text=True, shell=True)
        return registry_url
    except subprocess.CalledProcessError as e:
      print(f"Error during Docker login: {e.stderr}")
      exit(1)
    except Exception as e:
        print(f"An error occurred trying to log into ECR: {str(e)}")
        exit(1)

# Build, push, and tag Docker image
def build_and_push_docker_image(repository_uri):
    try:
        print("Building Docker image...")
        subprocess.run(f"docker build --platform linux/amd64 -t {ECR_REPO_NAME} .", shell=True, check=True)

        print("Tagging Docker image...")
        tagged_image = f"{repository_uri}:{IMAGE_TAG}"
        subprocess.run(f"docker tag {ECR_REPO_NAME}:latest {tagged_image}", shell=True, check=True)

        print("Pushing Docker image...")
        subprocess.run(f"docker push {tagged_image}", shell=True, check=True)

    except Exception as e:
        print(
            f"An error occurred trying to build, push, or tag Docker image: {str(e)}")
        exit(1)

# Create ECS Cluster
def create_ecs_cluster():
    response = ecs_client.list_clusters()
    if ECS_CLUSTER_NAME in response["clusterArns"]:
        print(f'ECS Cluster: {ECS_CLUSTER_NAME} already exists')
        return
    else:
        try:
            response = ecs_client.create_cluster(clusterName=ECS_CLUSTER_NAME)
            print(f'ECS Cluster: {ECS_CLUSTER_NAME} created successfully.')
            return response
        except Exception as e:
            print(f"An error occurred during cluster creation: {str(e)}")
            exit(1)

# Register Task Definition
def register_task_definition(repository_uri):
    try:
        response = ecs_client.list_task_definitions(
            familyPrefix=TASK_DEF_FAMILY, status="ACTIVE")
        if response["taskDefinitionArns"]:
            print(
                f"Task Definition Family: {TASK_DEF_FAMILY} already exists.")
            return response["taskDefinitionArns"][0]
        else:
            response = ecs_client.register_task_definition(
                family=TASK_DEF_FAMILY,
                networkMode="awsvpc",
                executionRoleArn=EXECUTION_ROLE_ARN,
                requiresCompatibilities=["FARGATE"],
                cpu="256",
                memory="512",
                containerDefinitions=[
                    {
                        "name": ECR_REPO_NAME,
                        "image": f"{repository_uri}:{IMAGE_TAG}",
                        "portMappings": [
                            {
                                "containerPort": 8080,
                                "hostPort": 8080,
                            }
                        ],
                        "environment": [{"name": "ENV", "value": "production"}],
                    }
                ]
            )
            print(f"Task Definition in Family: {TASK_DEF_FAMILY} registered successfully.") 
            return response["taskDefinition"]["taskDefinitionArn"]
    except Exception as e:
        print(f"An error occurred during task definition registration: {str(e)}")
        exit(1)

# Create ECS Service
def create_ecs_service(task_definition_arn):
    services = ecs_client.list_services(cluster=ECS_CLUSTER_NAME)["serviceArns"]
    if SERVICE_NAME in services:
        print(f'ECS Service: {SERVICE_NAME} already exists')
        return
    else: 
        print("Creating ECS Service...")
        response = ecs_client.create_service(
            cluster=ECS_CLUSTER_NAME,
            serviceName=SERVICE_NAME,
            taskDefinition=task_definition_arn,
            desiredCount=2,
            launchType="FARGATE",
            networkConfiguration={
                "awsvpcConfiguration": {
                    "subnets": SUBNETS,
                    "assignPublicIp": "ENABLED"
                }
            }
        )

    


print("Starting deployment...")
repository_uri = create_ecr_repo()
print(f"Repository URI: {repository_uri}")

print("Attempting to log into ECR...")
registry_url = login_to_ecr()
print(f"Logged in to Registry: {registry_url}")

print("Starting to configure Docker image...")
build_and_push_docker_image(repository_uri)
print("Docker image configured successfully.")

print("Attemtping to create ECS Cluster...")
create_ecs_cluster()
print("ECS Cluster created successfully.")

print("Attemtping to register Task Definition...")
task_definition_arn = register_task_definition(repository_uri)
print(f"Task registered, Task Definition ARN: {task_definition_arn}")