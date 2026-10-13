
variable "project_id" {
  description = "The GCP project ID."
  type        = string
}

variable "service_account" {
  description = "The name of the service account."
  type        = string
}

variable "repo" {
  description = "The GitHub repository in 'owner/repo' format."
  type        = string
}

variable "pool" {
  description = "The name of the Workload Identity Pool."
  type        = string
}

variable "oidc_provider" {
  description = "The name of the OIDC provider."
  type        = string
}

variable "organization" {
  description = "The GitHub organization or username."
  type        = string
}
