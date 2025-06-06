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
          timeout_seconds       = 5
          period_seconds        = 15
          failure_threshold     = 3
        }

        startup_probe {
          http_get {
            path = "/health"
            port = 8080
          }
          initial_delay_seconds = 5
          timeout_seconds       = 3
          period_seconds        = 5
          failure_threshold     = 10
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
        env {
          name  = "DB_CONNECTION_SECRET"
          value = google_secret_manager_secret.postgres_connection.name
        }
      }
      service_account_name = google_service_account.cloud_run.email

      # Set container concurrency for better scaling - compatible with CPU setting
      container_concurrency = 80
      timeout_seconds       = 300
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
  name          = var.bucket_name
  location      = var.region
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
          timeout_seconds       = 5
          period_seconds        = 15
          failure_threshold     = 3
        }

        startup_probe {
          http_get {
            path = "/health"
            port = 80
          }
          initial_delay_seconds = 5
          timeout_seconds       = 3
          period_seconds        = 5
          failure_threshold     = 10
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
      timeout_seconds       = 300
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

# PostgreSQL Instance
resource "google_sql_database_instance" "postgres" {
  name             = "ai-consultant-postgres-instance"
  database_version = "POSTGRES_14"
  region           = var.region

  settings {
    tier = "db-f1-micro"  # Smallest instance for development

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
    }

    ip_configuration {
      ipv4_enabled    = true
      private_network = null  # You might want to use VPC here in production

      # Allow Cloud Run to connect to this database
      authorized_networks {
        name  = "cloud-run"
        value = "0.0.0.0/0"  # In production, limit this to your specific IP ranges
      }
    }

    database_flags {
      name  = "max_connections"
      value = "100"
    }
  }

  deletion_protection = false  # Set to true for production
}

# Create the database
resource "google_sql_database" "database" {
  name     = "ai_consultant_db"
  instance = google_sql_database_instance.postgres.name
}

# Create the user
resource "google_sql_user" "users" {
  name     = "baid-dev"
  instance = google_sql_database_instance.postgres.name
  password = var.db_password  # Store this in a secret manager in production
}

# Secret Manager to store database credentials
resource "google_secret_manager_secret" "postgres_connection" {
  secret_id = "postgres-connection"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "postgres_connection" {
  secret      = google_secret_manager_secret.postgres_connection.id
  secret_data = "postgresql://${google_sql_user.users.name}:${var.db_password}@${google_sql_database_instance.postgres.public_ip_address}:5432/${google_sql_database.database.name}"
}

# Grant the Cloud Run service account access to the secret
resource "google_secret_manager_secret_iam_member" "cloud_run_secret_access" {
  secret_id = google_secret_manager_secret.postgres_connection.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run.email}"
}

# Add Secret Manager permissions to the Cloud Run service account
resource "google_project_iam_member" "secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

# Create a public GCS bucket for BAID-CI releases
resource "google_storage_bucket" "baid_ci_releases" {
  name          = "baid-ci-releases"
  location      = var.region
  force_destroy = true

  # Configure public access
  uniform_bucket_level_access = false  # Enable ACLs

  # Lifecycle rules to manage old versions
  lifecycle_rule {
    condition {
      age = 365  # Keep objects for 1 year
    }
    action {
      type = "Delete"
    }
  }

  # Enable versioning to keep track of binary history
  versioning {
    enabled = true
  }

  # Set CORS policy for direct browser downloads
  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD", "OPTIONS"]
    response_header = ["Content-Type", "Content-Length", "Content-Disposition"]
    max_age_seconds = 3600
  }

  # Set default object ACL to public-read
  website {
    main_page_suffix = "index.html"
    not_found_page   = "404.html"
  }
}

# Grant public read access to the bucket's objects
resource "google_storage_bucket_iam_binding" "public_read" {
  bucket = google_storage_bucket.baid_ci_releases.name
  role   = "roles/storage.objectViewer"
  members = [
    "allUsers",
  ]
}
