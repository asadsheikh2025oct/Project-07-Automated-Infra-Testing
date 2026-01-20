## Automated Infrastructure Testing: Azure VM Reachability

### Project Overview

This project demonstrates a professional CI/CD pattern for **Infrastructure as Code (IaC)** by implementing automated post-deployment validation. The goal is to move beyond simple deployment success logs and verify that the provisioned infrastructure is actually functional and reachable in a live environment.

### Core Objectives

* **Automated Provisioning**: Utilize Azure Bicep to deploy a standardized Linux Virtual Machine environment.
* **Security Compliance**: Implement and verify Network Security Group (NSG) rules to ensure secure yet functional access via SSH.
* **Validation Pipeline**: Orchestrate a multi-stage Azure DevOps pipeline that handles data passing between deployment and testing jobs.
* **Infrastructure Testing**: Use a custom testing framework to perform integration tests against the live infrastructure.

### Architecture & Components

The solution is built using a modular approach to ensure scalability and ease of maintenance:

* **Infrastructure Layer (Bicep)**: Defines the virtual network, subnets, public IP addresses (Standard SKU), and network interfaces. It also includes the critical security layer through NSG rules that explicitly allow inbound traffic on required ports.
* **Orchestration Layer (Azure Pipelines)**: A YAML-based pipeline that manages the lifecycle of the project. It handles the initial resource deployment, captures dynamic data (such as the VM's Public IP), and passes that information securely to the testing stage.
* **Testing Layer (Python/Bash)**: A specialized verification stage that uses native socket libraries to perform TCP handshake tests. This confirms that the VM is not only "active" but that the network path and OS-level services are responding correctly.

### Problem Resolution & Best Practices

A key focus of this project was overcoming common cloud automation hurdles:

* **Cross-Stage Variable Handling**: Successfully implementing logic to pass dynamic environment variables across different pipeline stages.
* **Environment Compatibility**: Opting for cross-platform tools (Python and Bash) to ensure reliable test execution on Linux-based build agents.
* **Default-Deny Security**: Addressing Azure's "secure by default" networking by correctly associating NSGs with subnets to enable connectivity.

### Outcomes

The final result is a robust pipeline that provides immediate feedback. If the infrastructure fails to meet reachability criteria—due to network misconfiguration or OS boot failures—the pipeline fails automatically, preventing the promotion of broken infrastructure to downstream environments.

---

**Would you like me to create a "Cleanup" stage for your pipeline now to automatically decommission these resources after the tests finish?**