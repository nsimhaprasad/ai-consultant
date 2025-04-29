variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "ai-consultant-458311"
}

variable "region" {
  description = "GCP region for resources (closest to India: asia-south1 Mumbai)"
  type        = string
  default     = "asia-south1"
}

variable "artifact_repo_name" {
  description = "Name of Artifact Registry repo"
  type        = string
  default     = "ai-consultant-backend-repo"
}

variable "cloud_run_service_name" {
  description = "Cloud Run service name"
  type        = string
  default     = "ai-consultant-backend"
}
