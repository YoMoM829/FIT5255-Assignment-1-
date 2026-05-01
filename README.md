# YOLO Object Detection API – Kubernetes Deployment

## Overview

This project implements a YOLO-based object detection API using FastAPI, containerised with Docker, and deployed on a Kubernetes cluster. The system is evaluated under concurrent load using Locust to analyse scalability, latency, throughput, and pod scaling behaviour.

The primary goal is to investigate how horizontal pod scaling impacts performance for a CPU-bound machine learning workload.

---

## Architecture

Client / Locust
      ↓
NodePort Kubernetes Service
      ↓
Kubernetes Deployment
      ↓
Multiple Pods running FastAPI + YOLO
      ↓
CPU-bound YOLO inference

---

## Tech Stack

- FastAPI
- Ultralytics YOLO
- Docker + Docker Hub
- Kubernetes
- Ansible
- Locust

---

## Prerequisites

Before running this project, ensure the following are installed:

- Docker
- Python 3
- pip
- Ansible
- Locust
- Access to virtual machines
- Docker Hub account

Install Python dependencies where required:

pip install -r requirements.txt

Install Locust if required:

pip install locust

Docker should be installed and running. The user should also have access to a Docker Hub account.

Login to Docker Hub:

docker login

---

## Virtual Machine Setup

This project assumes a Kubernetes cluster deployed across multiple virtual machines.

A typical setup includes:

- 1 control plane VM
- 1 or more worker VMs

Each VM should:

- Run a Linux-based operating system, preferably Ubuntu
- Have SSH access enabled
- Have a reachable IP address
- Allow traffic between Kubernetes nodes
- Allow SSH access on port 22
- Allow NodePort access, usually in the range 30000–32767

The exact VM creation process depends on the cloud provider being used. Provider-specific settings such as VM image, machine type, networking, firewall rules, SSH keys, and public IP addresses should be configured by the user.

---

## Docker Setup

Build the Docker image:

docker build -t <dockerhub-username>/yolo-app .

Run locally:

docker run -p 8000:8000 <dockerhub-username>/yolo-app

Access the local API documentation:

http://localhost:8000/docs

Push the Docker image to Docker Hub:

docker push <dockerhub-username>/yolo-app

The Kubernetes deployment file should reference this pushed Docker image.

---

## Important Configuration Notes

Several files contain environment-specific values. These must be updated before running the deployment.

### 1. Ansible Inventory

The inventory.ini file must contain the correct:

- control plane IP address
- worker node IP addresses
- SSH username
- SSH key path, if required

Example:

[control_plane]
cp1 ansible_host=<CONTROL_PLANE_IP> ansible_user=<USERNAME>

[workers]
worker1 ansible_host=<WORKER_1_IP> ansible_user=<USERNAME>
worker2 ansible_host=<WORKER_2_IP> ansible_user=<USERNAME>

---

### 2. Finding ansible_user

The ansible_user is the Linux username used to SSH into the VM.

For example, if this command works:

ssh anand@<VM_IP>

then the inventory should use:

ansible_user=anand

To confirm the current VM user, SSH into the VM and run:

whoami

The output of whoami is the username that should generally be used as ansible_user.

---

### 3. Dynamic Ansible Paths

Some Ansible files originally used hardcoded paths such as:

/home/anand

To make the playbooks portable, these paths should be written dynamically as:

/home/{{ ansible_user }}

This means Ansible automatically replaces ansible_user with the username defined in inventory.ini.

Example:

If inventory.ini contains:

ansible_user=anand

then:

/home/{{ ansible_user }}

becomes:

/home/anand

This applies only to Ansible and VM-level file paths.

---

### 4. Kubernetes YAML Files

Kubernetes deployment YAML files are separate from Ansible user settings.

The Kubernetes deployment file should be checked for:

- correct Docker image name
- correct container port
- correct service port
- correct resource requests and limits
- correct labels and selectors

Example Docker image field:

image: <dockerhub-username>/yolo-app

Important:

Kubernetes YAML files do not automatically use ansible_user unless the YAML files are specifically templated by Ansible. The ansible_user variable mainly affects SSH access and VM-level file paths in Ansible playbooks.

---

### 5. SSH Access

Before running the full playbook, test that Ansible can connect to all VMs:

ansible all -i inventory.ini -m ping

If a private key is required, add it to inventory.ini:

ansible_ssh_private_key_file=~/.ssh/id_rsa

---

## Running Ansible

Ansible should be run from a terminal environment such as:

- Linux terminal
- macOS terminal
- Windows WSL / Ubuntu terminal

Using WSL or Ubuntu on Windows is recommended because Ansible works more naturally in a Linux-like environment.

Run the deployment playbook:

ansible-playbook -i inventory.ini site.yml

This will:

- connect to the configured VMs
- run the required setup tasks
- apply Kubernetes deployment files
- deploy the YOLO application

---

## Scaling the Application

To scale the number of pods:

ansible control_plane -i inventory.ini -m shell -a "kubectl scale deployment yolo-deployment --replicas=4"

Example pod counts used during testing:

1 pod
2 pods
4 pods
8 pods

---

## Verifying Deployment

Check running pods:

ansible control_plane -i inventory.ini -m shell -a "kubectl get pods"

Check pod placement across nodes:

ansible control_plane -i inventory.ini -m shell -a "kubectl get pods -o wide"

Check services and exposed ports:

ansible control_plane -i inventory.ini -m shell -a "kubectl get services"

---

## Accessing the Application using NodePort

The application is exposed using a Kubernetes NodePort service.

To access the API:

http://<NODE_PUBLIC_IP>:<NODE_PORT>

To access the FastAPI documentation:

http://<NODE_PUBLIC_IP>:<NODE_PORT>/docs

The NodePort can be found by running:

ansible control_plane -i inventory.ini -m shell -a "kubectl get services"

Example service output may show:

8000:30080/TCP

In this case, access the application using:

http://<NODE_PUBLIC_IP>:30080/docs

---

## Monitoring and Debugging

Check pod logs:

ansible control_plane -i inventory.ini -m shell -a "kubectl logs <pod-name>"

Check pod resource usage:

ansible control_plane -i inventory.ini -m shell -a "kubectl top pods"

Check node resource usage:

ansible control_plane -i inventory.ini -m shell -a "kubectl top nodes"

Restart the deployment:

ansible control_plane -i inventory.ini -m shell -a "kubectl rollout restart deployment/yolo-deployment"

---

## Locust Load Testing

This project includes two Locust files.

### Manual Locust Testing

locust.py is a simple Locust file used for manual testing through the Locust web interface.

Run:

locust -f locust.py

Then open:

http://localhost:8089

In the Locust web interface, set the host to:

http://<NODE_PUBLIC_IP>:<NODE_PORT>

This allows manual testing by selecting the number of users and spawn rate.

---

### Automated Locust Testing

locustfile.py is the automated testing version. It runs tests across a range of users and records results into CSV files.

Run:

python locustfile.py

This script is used to collect benchmark data for comparing performance across different pod counts.

---

## Testing Predict and Annotate Endpoints

The API supports both prediction and annotation testing.

To test /api/predict:

- uncomment the predict request section
- comment out the annotate request section

To test /api/annotate:

- uncomment the annotate request section
- comment out the predict request section

Only one endpoint should be tested at a time so that the collected results remain clear and comparable.

---

## Performance Testing Strategy

The system was tested by increasing the number of concurrent users while changing the number of Kubernetes pods.

Testing was performed across pod counts such as:

1 pod
2 pods
4 pods
8 pods

For each pod count, concurrent users were gradually increased until latency increased significantly or the error rate became too high.

The key metrics recorded were:

- average latency
- requests per second
- failure rate
- maximum supported users
- effect of pod scaling

---

## Performance Analysis

Increasing pod count did not produce perfectly linear performance improvement. This is expected because YOLO inference is CPU-bound and each request requires significant compute resources.

The main bottlenecks observed were:

- CPU saturation on the worker nodes
- high inference time per request
- limited available compute despite additional pods
- increased latency once the system reached saturation

Horizontal scaling improves performance only when there is enough underlying CPU capacity available. If the nodes are already saturated, adding more pods mainly causes the pods to share the same limited compute resources.

---

## Key Insight

Kubernetes pod scaling improves availability and potential throughput, but it does not guarantee linear performance scaling. For CPU-heavy machine learning workloads such as YOLO inference, the limiting factor is often the available node CPU rather than the number of pods.

---

## Future Improvements

Possible improvements include:

- using GPU-enabled nodes
- using a smaller YOLO model
- improving asynchronous request handling
- adding readiness and liveness probes
- implementing Horizontal Pod Autoscaler
- collecting more fine-grained CPU and memory metrics
- testing with more worker nodes
- comparing /api/predict and /api/annotate performance separately

---

## Author

Anand Vannalath
Monash University – Software Engineering (Honours)
