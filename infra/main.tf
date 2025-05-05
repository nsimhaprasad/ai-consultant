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

        # Health check configuration for Python FastAPI
        liveness_probe {
          http_get {
            path = "/health"
            port = 8080
          }
          initial_delay_seconds = 10
          timeout_seconds = 5
          period_seconds = 15
          failure_threshold = 3
        }

        startup_probe {
          http_get {
            path = "/health"
            port = 8080
          }
          initial_delay_seconds = 5
          timeout_seconds = 3
          period_seconds = 5
          failure_threshold = 10
        }

        resources {
          limits = {
            memory = "512Mi"
            cpu    = "1000m"  # Changed to 1 CPU (1000m) to support higher concurrency
          }
        }

        # Environment variables
        env {
          name  = "VERSION"
          value = "1.0.0"
        }
      }
      service_account_name = google_service_account.cloud_run.email

      # Set container concurrency for better scaling - compatible with CPU setting
      container_concurrency = 80
      timeout_seconds = 300
    }

    metadata {
      annotations = {
        # Improved autoscaling settings
        "autoscaling.knative.dev/minScale" = "1"  # Keep at least one instance running
        "autoscaling.knative.dev/maxScale" = "10" # Scale up to 10 instances

        # Define CPU-based autoscaling targets
        "autoscaling.knative.dev/target" = "75"  # Target 75% CPU utilization
        "autoscaling.knative.dev/targetUtilizationPercentage" = "75"

        # Zero-downtime deployment settings
        "run.googleapis.com/startup-cpu-boost" = "true"
        "run.googleapis.com/client-name" = "terraform"

        # Health check timeout setting
        "run.googleapis.com/startup-probe-threshold" = "10"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  # Enable gradual rollout for zero-downtime deployments
  lifecycle {
    ignore_changes = [
      template[0].metadata[0].annotations["client.knative.dev/user-image"],
      template[0].metadata[0].annotations["run.googleapis.com/client-name"],
      template[0].metadata[0].annotations["run.googleapis.com/client-version"],
      metadata[0].annotations["client.knative.dev/user-image"],
      metadata[0].annotations["run.googleapis.com/client-name"],
      metadata[0].annotations["run.googleapis.com/client-version"]
    ]
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
  force_destroy = true
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

resource "google_artifact_registry_repository" "website" {
  provider      = google
  location      = var.region
  repository_id = var.website_artifact_repo_name
  description   = "Docker repo for website frontend"
  format        = "DOCKER"
}

resource "google_service_account" "website_cloud_run" {
  account_id   = "website-cr-sa"
  display_name = "Website Cloud Run Service Account"
}

resource "google_cloud_run_service" "website" {
  name     = var.website_cloud_run_service_name
  location = var.region

  template {
    spec {
      containers {
        image = var.website_image

        # Health check configuration for website
        liveness_probe {
          http_get {
            path = "/health"
            port = 80
          }
          initial_delay_seconds = 10
          timeout_seconds = 5
          period_seconds = 15
          failure_threshold = 3
        }

        startup_probe {
          http_get {
            path = "/health"
            port = 80
          }
          initial_delay_seconds = 5
          timeout_seconds = 3
          period_seconds = 5
          failure_threshold = 10
        }

        resources {
          limits = {
            memory = "256Mi"
            cpu    = "1000m"  # Changed to 1 CPU (1000m) to support higher concurrency
          }
        }
      }
      service_account_name = google_service_account.website_cloud_run.email

      # Set container concurrency for better scaling - compatible with CPU setting
      container_concurrency = 80
      timeout_seconds = 300
    }

    metadata {
      annotations = {
        # Improved autoscaling settings
        "autoscaling.knative.dev/minScale" = "1"  # Keep at least one instance running
        "autoscaling.knative.dev/maxScale" = "5"  # Scale up to 5 instances

        # Define CPU-based autoscaling targets
        "autoscaling.knative.dev/target" = "75"  # Target 75% CPU utilization
        "autoscaling.knative.dev/targetUtilizationPercentage" = "75"

        # Zero-downtime deployment settings
        "run.googleapis.com/startup-cpu-boost" = "true"
        "run.googleapis.com/client-name" = "terraform"

        # Health check timeout setting
        "run.googleapis.com/startup-probe-threshold" = "10"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  # Enable gradual rollout for zero-downtime deployments
  lifecycle {
    ignore_changes = [
      template[0].metadata[0].annotations["client.knative.dev/user-image"],
      template[0].metadata[0].annotations["run.googleapis.com/client-name"],
      template[0].metadata[0].annotations["run.googleapis.com/client-version"],
      metadata[0].annotations["client.knative.dev/user-image"],
      metadata[0].annotations["run.googleapis.com/client-name"],
      metadata[0].annotations["run.googleapis.com/client-version"]
    ]
  }

  autogenerate_revision_name = true
}

resource "google_cloud_run_service_iam_member" "website_public_invoker" {
  service  = google_cloud_run_service.website.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}