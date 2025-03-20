# Sports API Management System

## **Project Overview**
This project demonstrates building a containerized API management system for querying sports data. It leverages **Amazon ECS (Fargate)** for running containers, **Amazon API Gateway** for exposing REST endpoints, an external **Sports API** for real-time sports datam, and **Boto3** for automating the provisioning of resources. The project showcases advanced cloud computing practices, including API management, container orchestration, and secure AWS integrations. 

---

## **Features**
- Fetches real time WNBA game schedules from a search API
- Runs a containerized backend using Amazon ECS with Fargate
- Scalable and serverless architecture
- API management and routing using Amazon API Gateway
- Automated resource management 
 
---

## **Prerequisites**
- AWS account with appropriate permissions
- AWS CLI
- SerpApi API key 
- Docker Desktop/ Docker CLI

---

## **Technical Architecture**
![Flow chart depicting the interaction and data flow of the architecture](https://dev-to-uploads.s3.amazonaws.com/uploads/articles/hsohede4yv2pwedea4u9.jpeg)

---

## **Technologies**
- **Cloud Provider**: AWS
- **Core Services**: Amazon ECS (Fargate), API Gateway, CloudWatch
- **Programming Language**: Python 3.x
- **Containerization**: Docker
- **IAM Security**: Custom least privilege policies for ECS task execution and API Gateway

---

## **Project Structure**

```bash
containerized-sports-api/
├─] .env (ignored)
├── .gitignore
├── Dockerfile
├── LICENSE
├── README.md
├── app.py
├── deletion_script.py
├── requirements.txt
└── script.py

```

---

## **Setup Instructions**

### **Fork and then clone the repository**
- fork the [repo](https://github.com/Ljpeg/containerized-sports-api)
- create a folder locally
- change directories into that folder
- git clone the forked repo into the new folder/directory
- change directories into that folder
- set up a virtual environment
- open in VS Code
```bash
mkdir containerized-sports-api
cd containerized-sports-api
git clone https://github.com/Ljpeg/containerized-sports-api.git
cd containerized-sports-api
python3 -m venv venv
source venv/bin/activate
code . 
```


### **Set AWS environment variables**
- Navigate to the accounts tab of the AWS access portal, select the Access Keys symbol link, and copy the text from **Option 1: Set AWS environment variables**
- Paste the copied text into terminal in VS Code.
  
### Run python script to provision resources
- In the docker or bash terminal, enter `python3 script.py`  to provision the necessary resources. 
- After script finishes running, manually verify resources exist in AWS console. 


### **Test the System**
1. Get API Gateway URL and test it
- Get API Gatway URL by going to **AWS Console -> API Gateway -> Your API**
- curl*
- Make a request to your API Gateway URL (replace URL)
``` bash
curl https://xyz123.execute-api.us-east-1.amazonaws.com/prod/your-route
```
- This should trigger the load balancer, send traffic to a container, and return a response.
  
- Go to **AWS CloudWatch Logs -> Log Groups**
- Find the log group for API Gateway and your Flask app and check if request are coming through

2. Confirm Load Balancing works
- Find Load Balancer DNS name in AWS Console under **EC2 -> Load Balancers**
- call the load balancer directly (replace URL)
``` bash
curl http://my-load-balancer-1234567890.us-east-1.elb.amazonaws.com/your-route
```
- Run `docker logs` on both containers to see if traffic is distributed.
  
### **What We Learned**
Setting up a scalable, containerized application with ECS
Creating public APIs using API Gateway.
Automating AWS service provisioning. 

### **Future Enhancements**
Create a more stylized front end for user interaction.
Implement CI/CD for automating container deployments.


