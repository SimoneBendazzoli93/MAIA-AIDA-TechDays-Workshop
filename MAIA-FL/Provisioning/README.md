# NVIDIA FLARE Setup and Configuration

In this section, we will go through the steps to setup and configure the NVIDIA FLARE framework on different platforms/environments, including local environment, Docker, and Kubernetes.


## Provisioning
Provisioning is required to generate startup kits for FL servers, FL clients and admin users.
To run the provisioning command, be sure to have **nvflare** installed and then run the following command:
```bash
nvflare provision -p project.yaml
```
To dynamically provision additional users/sites, use the following command:
```bash
nvflare provision -p project.yaml --add_user user1.yaml --add_client client1.yaml
```
The startup kits will be generated in the following options:
- Zip file (for local environment)
- Docker Compose (for Docker environment)
- Helm chart (for Kubernetes environment)


The startup kits can be found in the following directory:
```bash
workspace/<project_name>/prod_xx
```
