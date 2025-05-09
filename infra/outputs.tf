output "cloud_run_url" {
  description = "The URL of the deployed Cloud Run service."
  value       = google_cloud_run_service.default.status[0].url
}

output "artifact_registry_repo" {
  description = "Artifact Registry repo for Docker images."
  value       = google_artifact_registry_repository.default.repository_id
}

output "website_cloud_run_url" {
  description = "The URL of the deployed Website Cloud Run service."
  value       = google_cloud_run_service.website.status[0].url
}

# Output the bucket URL (to use in install scripts)
output "baid_ci_bucket_url" {
  value = "https://storage.googleapis.com/${google_storage_bucket.baid_ci_releases.name}"
}