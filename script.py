import boto3
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
API_GATEWAY_NAME = "sports-api-gw"
HEALTH_CHECK_PATH = "/sports"
IMAGE_TAG = "sports-api-latest"
EXECUTION_ROLE_ARN = "arn:aws:iam::443370693600:role/ecsTaskExecutionRole"
SUBNETS = ["subnet-023863d2535821480",
          "subnet-0eeb018c552f1801c", "subnet-072732b43c768c4fb"]
VPC_ID = "vpc-037608f5ddf68b438"
SECURITY_GROUPS = ["sg-006d3ebb0bac7b387"]

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
        subprocess.run(
            f"aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin {registry_url}", check=True, text=True, shell=True)
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
        subprocess.run(
            f"docker build --platform linux/amd64 -t {ECR_REPO_NAME} .", shell=True, check=True)

        print("Tagging Docker image...")
        tagged_image = f"{repository_uri}:{IMAGE_TAG}"
        subprocess.run(
            f"docker tag {ECR_REPO_NAME}:latest {tagged_image}", shell=True, check=True)

        print("Pushing Docker image...")
        subprocess.run(f"docker push {tagged_image}", shell=True, check=True)

    except Exception as e:
        print(f"An error occurred trying to build, push, or tag Docker image: {str(e)}")
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
                        "environment": [{"name": "ENV", "value": "prod"}],
                    }
                ]
            )
            print(
                f"Task Definition in Family: {TASK_DEF_FAMILY} registered successfully.")
            return response["taskDefinition"]["taskDefinitionArn"]
    except Exception as e:
        print(
            f"An error occurred during task definition registration: {str(e)}")
        exit(1)

# Create ECS Service
def create_ecs_service(task_definition_arn):
    services = ecs_client.list_services(
        cluster=ECS_CLUSTER_NAME)["serviceArns"]
    if SERVICE_NAME in services:
        print(f'ECS Service: {SERVICE_NAME} already exists')
        return
    else:
        try:
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
                        "securityGroups": SECURITY_GROUPS,
                        "assignPublicIp": "ENABLED"
                    }
                }
            )
            print(f'ECS Service: {response["service"]["serviceName"]}, {response["service"]["serviceArn"]} created successfully.')
            return response["service"]["serviceArn"]
        except Exception as e:
            print(f'An error occurred during service creation: {str(e)}')
            exit(1)

# Create Load Balancer
def create_load_balancer():
    alb_arn = None
    target_group_arn = None
    try: 
        print("Creating Load Balancer...")
        response = elb_client.create_load_balancer(
            Name=LOAD_BALANCER_NAME,
            Subnets=SUBNETS,
            SecurityGroups=SECURITY_GROUPS,
            Scheme="internet-facing",
            Type="application",
        )
        alb = response["LoadBalancers"][0]
        alb_arn = response["LoadBalancers"][0]["LoadBalancerArn"]
        print(f"Load Balancer created successfully: {alb_arn}")
    except Exception as e:
        print(f"An error occurred during load balancer creation: {str(e)}")
        exit(1)
    
    try:
        print("Creating Target Group...")
        response = elb_client.create_target_group(
            Name=TARGET_GROUP_NAME,
            Protocol="HTTP",
            Port=8080,
            VpcId=VPC_ID,
            HealthCheckPath=HEALTH_CHECK_PATH,
        )
        target_group_arn = response["TargetGroups"][0]["TargetGroupArn"]
        print(f"Target Group created successfully: {target_group_arn}")
    except Exception as e:
        print(f"An error occurred during target group creation: {str(e)}")
        exit(1)
        
    try:
        print("Attaching target group to load balancer...")
        response = elb_client.create_listener(
            LoadBalancerArn=alb_arn,
            Protocol="HTTP",
            Port=80,
            DefaultActions=[
                {
                    "Type": "forward",
                    "TargetGroupArn": target_group_arn,
                }
            ]
        )
        print("Target group attached to load balancer successfully.")
    except Exception as e:
        print(f"An error occurred during target group attachment: {str(e)}")
        exit(1)
    
    return alb["DNSName"]

# Create API Gateway
def create_api_gateway(alb_dns):
    try:
        print("Creating Rest API for gateway...")
        response = api_gateway_client.create_rest_api(
            name=API_GATEWAY_NAME
        )
        api_id = response["id"]
        print(f"Rest API for gateway created successfully with api id: {api_id}")

        root_id = api_gateway_client.get_resources(
          restApiId=api_id)["items"][0]["id"]
        print(f"Root resource id: {root_id}")

        print(f"Creating resource for /sports...")
        resource = api_gateway_client.create_resource(
            restApiId=api_id,
            parentId=root_id,
            pathPart="sports"
        )
        resource_id = resource["id"]
        print(f"/sports resource created successfully with id: {resource_id}")
        print("Creating GET method for /sports...")
        api_gateway_client.put_method(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod="GET",
            authorizationType="NONE"
        )
        endpoint = f'https://{alb_dns}{HEALTH_CHECK_PATH}'
        print(f"Creating integration for /sports with endpoint: {endpoint}")
        api_gateway_client.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod="GET",
            type="HTTP_PROXY",
            integrationHttpMethod="GET",
            uri=endpoint
        )
        print("Creating deployment for /sports...")
        api_gateway_client.create_deployment(
            restApiId=api_id,
            stageName="prod"
        )
    except Exception as e:
        print(f"An error occurred during API Gateway creation: {str(e)}")
        exit(1)

if __name__ == "__main__":
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

  print("Attemtping to create ECS Service...")
  create_ecs_service(task_definition_arn)
  print("ECS Service created successfully.")

  print("Attempting to create load balancer...")
  load_balancer_dns = create_load_balancer()
  print(f"Load Balancer with DNS: {load_balancer_dns} successfully created")

  print("Attempting to create API Gateway...")
  create_api_gateway(load_balancer_dns)
  print("API Gateway created successfully.")
