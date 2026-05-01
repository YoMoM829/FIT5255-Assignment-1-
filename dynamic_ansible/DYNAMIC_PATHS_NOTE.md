# Dynamic Ansible Path Update

These playbooks no longer hardcode `/home/anand`. Paths now use `/home/{{ ansible_user }}`, meaning Ansible will use the VM username specified in `inventory.ini`.

Before running:

1. Replace placeholders in `inventory.ini` with your VM IPs, SSH username, and SSH key path.
2. Ensure the VM username has a matching home directory, for example `/home/ubuntu` for `ansible_user=ubuntu`.
3. Ensure the Kubernetes YAML files referenced by `site.yml` exist beside the playbook: `yolo-deployment.yaml` and `yolo-service.yaml`.

Run:

```bash
ansible-playbook -i inventory.ini site.yml
```
