variable "project_id" {
  description = "The GCP project ID."
  type        = string
  default     = "ai-consultant-458311"
}

variable "region" {
  description = "The GCP region."
  type        = string
  default     = "asia-south1"
}

variable "bucket_name" {
  description = "The name of the GCS bucket for Vertex AI staging."
  type        = string
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
