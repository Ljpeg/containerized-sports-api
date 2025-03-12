import boto3 
import time
from script import AWS_ACCOUNT_ID, AWS_REGION, ECR_REPO_NAME, API_GATEWAY_NAME, LOAD_BALANCER_NAME, TASK_DEF_FAMILY, SERVICE_NAME, ECS_CLUSTER_NAME

api_gateway_client = boto3.client('apigateway', region_name=AWS_REGION)
elb_client = boto3.client('elbv2', region_name=AWS_REGION)
ecr_client = boto3.client('ecr', region_name=AWS_REGION)
ecs_client = boto3.client('ecs', region_name=AWS_REGION)


# Delete API Gateway
def delete_API_Gateway():
  api_response = api_gateway_client.get_rest_apis()
  api_id = None
  for api in api_response['items']:
      if api['name'] == API_GATEWAY_NAME:
          api_id = api['id']
          break
  if api_id:
    try:
        api_gateway_client.delete_rest_api(restApiId=api_id)
        print(f"Deleted API Gateway {API_GATEWAY_NAME}")
    except Exception as e:
        print(f"Error deleting API Gateway {API_GATEWAY_NAME}: {str(e)}")
  else: 
      print(f"API Gateway {API_GATEWAY_NAME} not found")

# Delete ALB
def delete_load_balancer():
  elb_response = elb_client.describe_load_balancers()
  alb_arn = None
  for lb in elb_response['LoadBalancers']:
      if lb['LoadBalancerName'] == LOAD_BALANCER_NAME:
          alb_arn = lb['LoadBalancerArn']
          break
  if alb_arn:
    try:
        elb_client.delete_load_balancer(LoadBalancerArn=alb_arn)
        print(f"Deleted Load Balancer {LOAD_BALANCER_NAME}")
    except Exception as e:
        print(f"Error deleting Load Balancer {LOAD_BALANCER_NAME}: {str(e)}")
  else:
      print(f"Load Balancer {LOAD_BALANCER_NAME} not found")


# Delete ECR Repository
def delete_ecr_Repo():
  ecr_response = ecr_client.describe_repositories()
  repo_name = None
  for repo in ecr_response['repositories']:
      if repo['repositoryName'] == ECR_REPO_NAME:
          repo_name = repo['repositoryName']
          break
  if repo_name:
    try:
        ecr_client.delete_repository(repositoryName=repo_name, force=True)
        print(f"Deleted ECR Repository {ECR_REPO_NAME}")
    except Exception as e:
        print(f"Error deleting ECR Repository {ECR_REPO_NAME}: {str(e)}")
  else:
      print(f"ECR Repository {ECR_REPO_NAME} not found")

# Deregister Task Definition
def deregister_task_definition():
  td_response = None
  td_arn = None
  try:
    td_response = ecs_client.describe_task_definition(taskDefinition=TASK_DEF_FAMILY)
    print(td_response['taskDefinition']['family'])
    if td_response['taskDefinition']['family'] == TASK_DEF_FAMILY:
        td_arn = td_response['taskDefinition']['taskDefinitionArn']
        ecs_client.deregister_task_definition(taskDefinition=td_arn)
        print(f"Deregistered Task Definition {TASK_DEF_FAMILY}")
    else:
        print(f"Task Definition {TASK_DEF_FAMILY} not found")
  except Exception as e:
        print(f"Error deregistering Task Definition {TASK_DEF_FAMILY}: {str(e)}")

# Update ECS Service tasks to 0 
def update_service_count():
  try:
    ecs_client.update_service(cluster=ECS_CLUSTER_NAME, service=SERVICE_NAME, desiredCount=0)
    print(f"Updated ECS Service {SERVICE_NAME} to 0 tasks")
  except Exception as e:
    print(f"Error updating ECS Service {SERVICE_NAME} to 0 tasks: {str(e)}")

# Delete ECS Service
def delete_service():
  try:
    ecs_client.delete_service(cluster=ECS_CLUSTER_NAME, service=SERVICE_NAME)
    print(f"Deleted ECS Service {SERVICE_NAME}")
  except Exception as e:
    print(f"Error deleting ECS Service {SERVICE_NAME}: {str(e)}")

# Delete Cluster
def delete_cluster():
  try:
    ecs_client.delete_cluster(cluster=ECS_CLUSTER_NAME)
    print(f"Deleted ECS Cluster {ECS_CLUSTER_NAME}")
  except Exception as e:
    print(f"Error deleting ECS Cluster {ECS_CLUSTER_NAME}: {str(e)}")

if __name__ == "__main__":
  # Script to delete resources
  print("Deleting resources...")
  print("------------------------------")
  print("Attempting to delete Api Gateway")
  delete_API_Gateway()
  print("Api Gateway successfully deleted")

  print("Attempting to delete Load Balancer")
  delete_load_balancer()
  print("Load Balancer successfully deleted")

  print("Attempting to delete ECR Repository")
  delete_ecr_Repo()
  print("ECR Repo successfully deleted")

  print("Attempting to deregister Task Definition")
  deregister_task_definition()
  print("Task definition successfully deregistered")

  print("Attempting to update ECS Service to 0 tasks")
  update_service_count()
  print("ECS Service successfully updated")

  print("Waiting for 2 minutes for ECS Service to scale down to 0 tasks")
  time.sleep(120)

  print("Attepting to delete ECS Service")
  delete_service()
  print("ESC Service successfully deleted")

  print("Attempting to delete Cluster")
  delete_cluster()
  print("Cluster successfully deleted")

  print("------------------------------")
  print("All resources succesfully deleted")