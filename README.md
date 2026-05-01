# YOLO Object Detection API – Kubernetes Deployment

## Overview
This project implements a **YOLO-based object detection API** using FastAPI, containerised with Docker, and deployed on a Kubernetes cluster. The system is evaluated under concurrent load using Locust to analyse **scalability, latency, and throughput**.

The primary goal is to investigate how **horizontal pod scaling impacts performance** for a CPU-bound machine learning workload.

---

## Architecture
Client (Locust)
↓
Kubernetes Service (Load Balancer)
↓
Multiple Pods (FastAPI + YOLO Inference)
↓
CPU-bound Model Execution


---

## Tech Stack
- **FastAPI** – API framework
- **Ultralytics YOLO** – Object detection model
- **Docker** – Containerisation
- **Kubernetes (kubeadm)** – Orchestration
- **Ansible** – Infrastructure automation
- **Locust** – Load testing

---
## Prerequsites 
Before running the project, ensure the following are installed:
- Docker 
- Python 3
- Ansible
- Kubernetes
- Locust
- Access to virtual machines via cloud providers

Install python dependecies where required:
```bash
pip install -r requirements.txt
```

Install Locust:
```bash
pip install locust
```

## Docker Setup

Login to Docker Hub:
```bash
docker login
```

Build Image:
```bash
docker build -t <dockerhub-username>/yolo-app .
```

Run Locally: 
```bash
docker run -p 8000:8000 <dockerhub-username>/yolo-app
```

Access API:
http://localhost:8000/docs

### Push image to Docker Hub
docker push <dockerhub-username>/yolo-app

## VM Requirements
1. Create 3 VMs. This can be via a cloud service provider.
2. Name one master/control-plane and the other 2 worker-1 and worker-2.
3. Ensure all VMs are set to 4 cores and 8GB RAM each, preferrably Ubuntu LTS 22.02

## Deployment using Ansible (Infrastructure as Code)
The application is deployed using Ansible to ensure a fully automated and reproducible setup.

### Inventory Configuration
Before running Ansible, the configuration files should be updated as follows.

**Inventory.ini**

Ensure your `inventory.ini` contains the correct:
- Control Plane IP address
- Worker Node IP address
- SSH username
- SSH key path if required

*Import image*



### Run Deployment Playbook
```bash
ansible-playbook -i inventory.ini site.yml
```

This will:
- Configure Kubernetes cluster access
- Deploy the YOLO application
- Apply Kubernetes Deployment and Service manifests

### Scaling via Ansible
To scale the application:
```bash 
ansible control_plane -i inventory.ini -m shell -a "kubectl scale deployment yolo-deployment --replicas=4"
```

### Verifying Deployment 
To check the number of pods run:
```bash
ansible control_plane -i inventory.ini -m shell -a "kubectl get pods"
```

To check the service and the port run:
```bash 
ansible control_plane -i inventory.ini -m shell -a "kubectl get services"
```

### Notes
Using Ansible removes a lot of manual commands needed to run the following application. It also ensures 
full deployment of the app and allows the app to be easily redeployed and scaled.

