provider "google" {
  project = var.project_id
}

locals {
  required_apis = [
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "sts.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "discoveryengine.googleapis.com",
    "aiplatform.googleapis.com",
    "serviceusage.googleapis.com",
    "bigquery.googleapis.com",
    "cloudtrace.googleapis.com"
  ]
}

resource "google_project_service" "apis" {
  for_each = toset(local.required_apis)
  service  = each.value
}


resource "google_project_iam_member" "github_oidc_access" {
  project = var.project_id
  role    = "roles/owner"
  member  = "principalSet://iam.googleapis.com/projects/${data.google_project.project.number}/locations/global/workloadIdentityPools/${google_iam_workload_identity_pool.github_pool.workload_identity_pool_id}/attribute.repository/${var.repo}"
  
  depends_on = [google_project_service.apis]
}

resource "google_iam_workload_identity_pool" "github_pool" {
  workload_identity_pool_id = var.pool
  project                   = var.project_id
  display_name              = "GitHub Actions Pool"
  
  depends_on = [google_project_service.apis]
}

resource "google_iam_workload_identity_pool_provider" "github_provider" {
  workload_identity_pool_provider_id = var.oidc_provider
  project                            = var.project_id
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
  display_name                       = "GitHub OIDC Provider"
  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
  attribute_mapping = {
    "google.subject"         = "assertion.sub"
    "attribute.repository"       = "assertion.repository"
    "attribute.repository_owner" = "assertion.repository_owner"
  }
  attribute_condition = "assertion.repository == '${var.repo}'"
  
  depends_on = [google_project_service.apis]
}

data "google_project" "project" {
  depends_on = [google_project_service.apis]
}
