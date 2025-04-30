# Terraform GCP Infra for ai-consultant

This config will provision minimal, low-cost Google Cloud infra in the Mumbai region (asia-south1):
- Artifact Registry (Docker)
- Cloud Run (FastAPI backend, public endpoint)
- Service Account for deployment

## Usage
1. Install Terraform & authenticate with Google Cloud (`gcloud auth application-default login`).
2. `terraform init`
3. `terraform apply`

## Outputs
- Cloud Run URL
- Artifact Registry repo

## Cost
- Uses lowest-tier Cloud Run (1 instance, always-off by default, only pay per request)
- No VPC, no static IP, no minimums

## Integration with Deployment Pipeline

- The Terraform infra provisions the GCP resources needed for both agent and server deployment, including Artifact Registry and Cloud Run.
- The CI/CD pipeline depends on these resources for artifact storage and server hosting.

---
Edit `variables.tf` for custom names or region.
