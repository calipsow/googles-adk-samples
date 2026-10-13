terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0.0"
    }
  }
  backend "gcs" {
    bucket = "adk-devops-terraform-state"
    prefix = "github-oidc"
  }
}
