resource "google_artifact_registry_repository" "default" {
  provider      = google
  location      = var.region
  repository_id = var.artifact_repo_name
  description   = "Docker repo for ai-consultant backend"
  format        = "DOCKER"
}

resource "google_service_account" "cloud_run" {
  account_id   = "ai-consultant-cr-sa"
  display_name = "Cloud Run Service Account"
}

resource "google_cloud_run_service" "default" {
  name     = var.cloud_run_service_name
  location = var.region
  template {
    spec {
      containers {
        image = "gcr.io/cloudrun/hello"
        resources {
          limits = {
            memory = "256Mi"
            cpu    = "0.25"
          }
        }
        env {
          name  = "PORT"
          value = "8080"
        }
      }
      service_account_name = google_service_account.cloud_run.email
    }
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = "0"
        "autoscaling.knative.dev/maxScale" = "1"
      }
    }
  }
  traffic {
    percent         = 100
    latest_revision = true
  }
  autogenerate_revision_name = true
}

resource "google_cloud_run_service_iam_member" "public_invoker" {
  service  = google_cloud_run_service.default.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# --- GCP AI Consultant Agent Infra ---

resource "google_service_account" "vertex_agent" {
  account_id   = "vertex-agent-sa"
  display_name = "Vertex Agent Service Account"
}

resource "google_project_iam_member" "vertex_ai_admin" {
  project = var.project_id
  role    = "roles/aiplatform.admin"
  member  = "serviceAccount:${google_service_account.vertex_agent.email}"
}

resource "google_project_iam_member" "storage_admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.vertex_agent.email}"
}

resource "google_storage_bucket" "staging" {
  name     = var.bucket_name
  location = var.region
}

resource "google_project_service" "vertex_ai" {
  project = var.project_id
  service = "aiplatform.googleapis.com"
}

resource "google_project_service" "artifact_registry" {
  project = var.project_id
  service = "artifactregistry.googleapis.com"
}

resource "google_project_service" "iam_credentials" {
  project = var.project_id
  service = "iamcredentials.googleapis.com"
}

resource "google_project_service" "storage" {
  project = var.project_id
  service = "storage.googleapis.com"
}
