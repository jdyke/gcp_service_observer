module "project-services" {
  source  = "terraform-google-modules/project-factory/google//modules/project_services"
  version = "13.0.0"

  project_id = var.project_id

  activate_apis = [
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
  ]
  disable_services_on_destroy = false
}

resource "google_service_account" "service-observer-sa" {
  project      = var.project_id
  account_id   = "service-observer-sa"
  display_name = "GCP Service Observer Cloud Run SA"
}

# Enable below for org-level project API / service listing
#resource "google_organization_iam_member" "organization-sa-iam" {
#  org_id  = var.org_id
#  role    = google_organization_iam_custom_role.organization-sa-custom-role.id
#  member = "serviceAccount:${google_service_account.service-observer-sa.email}"
#}

#resource "google_organization_iam_custom_role" "organization-sa-custom-role" {
#  role_id     = "ServiceObserverViewerRole"
#  org_id      = var.org_id
#  title       = "Service Observer org IAM role. View only."
#  description = "Provides permissions to view API/services across the organization."
#  permissions = ["resourcemanager.projects.get", "serviceusage.services.list"]
#}

# Disable below if using for org-wide API/service listing
resource "google_project_iam_member" "project-sa-iam" {
  project = var.project_id
  role    = google_project_iam_custom_role.project-sa-custom-role.id
  member  = "serviceAccount:${google_service_account.service-observer-sa.email}"
}

resource "google_project_iam_custom_role" "project-sa-custom-role" {
  project     = var.project_id
  role_id     = "ServiceObserverViewerRole"
  title       = "Service Observer project IAM role. View only."
  description = "Provides permissions to view API/services on a given project."
  permissions = ["resourcemanager.projects.get", "serviceusage.services.list"]
}