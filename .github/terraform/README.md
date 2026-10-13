# Terraform for GitHub OIDC

This directory contains Terraform configuration to set up Google Cloud authentication for GitHub Actions using Workload Identity Federation.

## Usage

1.  **Initialize Terraform:**
    ```bash
    terraform init
    ```

2.  **Create a `terraform.tfvars` file with the following content:**
    ```
    project_id      = "your-gcp-project-id"
    service_account = "your-service-account-name"
    repo            = "your-github-organization/your-repo-name"
    pool            = "github-pool"
    provider        = "github-provider"
    organization    = "your-github-organization"
    ```

3.  **Apply the Terraform configuration:**
    ```bash
    terraform apply
    ```

4.  **The output will provide the `workload_identity_provider` to use in your GitHub Actions workflow.**
