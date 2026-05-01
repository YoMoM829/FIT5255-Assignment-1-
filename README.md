# YOLO Object Detection API – Kubernetes Deployment

## Overview

This project implements a YOLO-based object detection API using FastAPI, containerised with Docker, and deployed on a Kubernetes cluster. The system is evaluated under concurrent load using Locust to analyse scalability, latency, throughput, and pod scaling behaviour.

The primary goal is to investigate how horizontal pod scaling impacts performance for a CPU-bound machine learning workload.

---

## Architecture
- Client / Locust
- NodePort Kubernetes Service
- Kubernetes Deployment
- Multiple Pods running FastAPI + YOLO
- CPU-bound YOLO inference

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

Install Python dependencies where required:
```
pip install -r requirements.txt
```

Install Locust if required:
```
pip install locust
```

---


## Docker Setup
Docker should be installed and running. The user should also have access to a Docker Hub account.

Open terminal and navigate to your folder. Login to Docker Hub:
```
docker login
```

Build the Docker image:
```
docker build -t <dockerhub-username>/yolo-app .
```

Run locally:
```
docker run -p 8000:8000 <dockerhub-username>/yolo-app
```

Access the local API documentation:
```
http://localhost:8000/docs
```

Push the Docker image to Docker Hub:
```
docker push <dockerhub-username>/yolo-app
```

---

## Virtual Machine Setup

This project assumes a Kubernetes cluster deployed across multiple virtual machines.

A typical setup includes:

- 1 control plane VM
- 1 or more worker VMs, ideally 2 VMs

Each VM should:

- Run a Linux-based operating system, preferably Ubuntu
- Have SSH access enabled
- Have a reachable IP address
- Allow traffic between Kubernetes nodes
- Allow SSH access on port 22
- Allow NodePort access, usually in the range 30000–32767

Specific VM Settings:
- 4CPU cores
- 8GB RAM

The exact VM creation process depends on the cloud provider being used. Provider-specific settings such as VM image, machine type, networking, firewall rules, SSH keys, and public IP addresses should be configured by the user.

---

## Important Configuration Notes

Several files contain environment-specific values. These must be updated before running the deployment.
Sign in CMD, Powershell or Mac equivalent and sign into Ubuntu.

Copy over the following files into a directory of your choice:
- inventory.ini
- init_master.yml
- install-k8s-tools.yml
- setup-k8s.yml
- site.yml
- yolo-deployment.yaml
- yolo-service.yaml

### 1. Ansible Inventory

The inventory.ini file must contain the correct:

- control plane IP address
- worker node IP addresses
- SSH username
- SSH key path, if required

Example:
```
[control_plane]
cp1 ansible_host=<CONTROL_PLANE__EXTERNAL_IP> ansible_user=<USERNAME> 

[workers]
worker1 ansible_host=<WORKER_1_EXTERNAL_IP> ansible_user=<USERNAME> 
worker2 ansible_host=<WORKER_2_EXTERNAL_IP> ansible_user=<USERNAME> 
```

---

### 2. Finding ansible_user

The ansible_user is the Linux username used to SSH into the VM.

For example, if this command works:
```
ssh anand@<VM_IP>
```

then the inventory should use:
```
ansible_user=anand
```

To confirm the current VM user, SSH into the VM and run:
```
whoami
```
The output of whoami is the username that should generally be used as ansible_user.

Otherwise when running:
```
ssh-keygen -t rsa -b 4096 -f <PATH_NAME>
```

The user of the local machine is the ansible user.
```
E.g if user=anand, ansible_user=anand
```

---

### 3. Dynamic Ansible Paths

Some Ansible files originally used hardcoded paths such as:
```
/home/anand
```

To make the playbooks portable, these paths should be written dynamically as:
```
/home/{{ ansible_user }}
```

This means Ansible automatically replaces ansible_user with the username defined in inventory.ini.

Example:

If inventory.ini contains:
```
ansible_user=anand
```

then:
```
/home/{{ ansible_user }}
```

becomes:
```
/home/anand
```

This applies only to Ansible and VM-level file paths.

---

### 4. Kubernetes YAML Files

Kubernetes deployment YAML files are separate from Ansible user settings.

In yolo-deployment.yaml, use the Docker Username in dockerhub-username

Example Docker image field:
```
image: <dockerhub-username>/yolo-app
```

Important:

Kubernetes YAML files do not automatically use ansible_user unless the YAML files are specifically templated by Ansible. The ansible_user variable mainly affects SSH access and VM-level file paths in Ansible playbooks.

---

### 5. SSH Access

Before running the full playbook, test that Ansible can connect to all VMs:
```
ansible all -i inventory.ini -m ping
```

If a private key is required, add it to inventory.ini:
```
[control_plane]
cp1 ansible_host=<CONTROL_PLANE__EXTERNAL_IP> ansible_user=<USERNAME> ansible_ssh_private_key_file=<PATH_TO_PRIVATE_KEY>

[workers]
worker1 ansible_host=<WORKER_1_EXTERNAL_IP> ansible_user=<USERNAME> ansible_ssh_private_key_file=<PATH_TO_PRIVATE_KEY>
worker2 ansible_host=<WORKER_2_EXTERNAL_IP> ansible_user=<USERNAME> ansible_ssh_private_key_file=<PATH_TO_PRIVATE_KEY>
```

---

## Running Ansible

Ansible should be run from a terminal environment such as:

- Linux terminal
- macOS terminal
- Windows WSL / Ubuntu terminal

Using WSL or Ubuntu on Windows is recommended because Ansible works more naturally in a Linux-like environment.

Run the deployment playbook:
```
ansible-playbook -i inventory.ini site.yml
```

This will:

- connect to the configured VMs
- run the required setup tasks
- apply Kubernetes deployment files
- deploy the YOLO application

### SSH Host Key Verification

When running Ansible for the first time, SSH may prompt:

"Are you sure you want to continue connecting (yes/no)?"

This occurs because the VMs are being connected to for the first time and their host keys are not yet known.

In some cases, Ansible may only prompt for one VM at a time. If this happens:
- type "yes" to accept the host key
- re-run the playbook to trigger the remaining prompts for other VMs

This step only needs to be performed once per VM. After all host keys are accepted, future Ansible runs will execute without interruption.

---

## Scaling the Application

To scale the number of pods:
```
ansible control_plane -i inventory.ini -m shell -a "kubectl scale deployment yolo-app --replicas=4"
```

Example pod counts used during testing:
- 1 pod
- 2 pods
- 4 pods
- 8 pods

---

## Verifying Deployment

Check running pods:
```
ansible control_plane -i inventory.ini -m shell -a "kubectl get pods"
```

Check pod placement across nodes:
```
ansible control_plane -i inventory.ini -m shell -a "kubectl get pods -o wide"
```

Check services and exposed ports:
```
ansible control_plane -i inventory.ini -m shell -a "kubectl get services"
```

---

## Accessing the Application using NodePort

The application is exposed using a Kubernetes NodePort service.

To access the API:
```
http://<NODE_PUBLIC_IP>:<NODE_PORT>
```

To access the FastAPI documentation:
```
http://<NODE_PUBLIC_IP>:<NODE_PORT>/docs
```

The NodePort can be found by running:
```
ansible control_plane -i inventory.ini -m shell -a "kubectl get services"
```

Example service output may show:
```
8000:30080/TCP
```

In this case, access the application using:
```
http://<NODE_PUBLIC_IP>:30080/docs
```

---

## Monitoring and Debugging

Check pod logs:
```
ansible control_plane -i inventory.ini -m shell -a "kubectl logs <pod-name>"
```

Check pod resource usage:
```
ansible control_plane -i inventory.ini -m shell -a "kubectl top pods"
```

Check node resource usage:
```
ansible control_plane -i inventory.ini -m shell -a "kubectl top nodes"
```

Restart the deployment:
```
ansible control_plane -i inventory.ini -m shell -a "kubectl rollout restart deployment/yolo-app"
```

---

## Locust Load Testing

This project includes two Locust files.

### Manual Locust Testing

locust.py is a simple Locust file used for manual testing through the Locust web interface.

Run:
```
locust -f locust.py
```

Then open:
```
http://localhost:8089
```

In the Locust web interface, set the host to:
```
http://<NODE_PUBLIC_IP>:<NODE_PORT>
```

This allows manual testing by selecting the number of users and spawn rate.

---

### Automated Locust Testing (locustfile.py)

locustfile.py is a custom automated load testing script used to generate performance data across increasing user levels.

This script:
- progressively increases concurrent users
- stops each stage based on request limits or failure thresholds
- automatically records results into a CSV file (`auto_results_summary.csv`)

Run the script using:
```
locust -f locustfile.py --headless --host=http://<NODE_PUBLIC_IP>:<NODE_PORT>
```

Example:
```
locust -f locustfile.py --headless --host=http://34.xxx.xxx.xxx:30080
```

You may need to augment the file path for locustfile.py to testing/locustfile.py

Key behaviour:
- Users increase in predefined steps (e.g. 1, 10, 25, 50, …)
- Each stage runs until:
  - a request limit is reached, OR
  - failure rate exceeds the threshold (e.g. 50%)
- Results are saved automatically for analysis

---

### Switching Endpoints

The script supports both `/api/annotate` and `/api/predict`.

To test `/api/annotate`:
- ensure the `annotate` task is active

To test `/api/predict`:
- comment out the annotate task
- uncomment the predict task

Only one endpoint should be active at a time to ensure clean benchmarking results.

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

It was observed that increasing pod count did not result in linear performance improvements due to CPU-bound YOLO inference, 
indicating that system performance is constrained by node-level compute resources rather than pod availability alone.

In summary, horizontal pod scaling improved throughput and supported higher concurrent users, 
but did not significantly reduce latency due to the CPU-bound nature of YOLO inference. 
This demonstrates that scaling efficiency is limited by underlying node compute resources rather than pod count alone.

---
## Author

Anand Vannalath
Monash University – Software Engineering (Honours)