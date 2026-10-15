# <Project name>

<One sentence: what it does and who it is for.>

[Live demo](<url>) · [Architecture](#architecture) · [CI/CD](#cicd-pipeline) · [Cost](#cost-notes)

## Architecture

![Architecture diagram](docs/architecture.png)

| Layer | Choice | Why |
|---|---|---|
| Compute | AWS EKS Fargate | No node management, per-pod billing |
| Network | VPC with private subnets, ALB ingress | Workloads not exposed directly |
| Data | RDS PostgreSQL / S3 | <reason> |
| IaC | Terraform (modules: vpc, eks, rds, ecr) | Reusable, remote state in S3 + DynamoDB lock |
| Delivery | GitHub Actions build/push, ArgoCD sync | Git is the source of truth |
| Secrets | External Secrets + AWS Secrets Manager | No secrets in Git |

## CI/CD pipeline

1. Pull request: lint, unit tests, `terraform fmt/validate/plan`.
2. Merge to main: build image, scan (Trivy), push to ECR, bump image tag in the GitOps manifest.
3. ArgoCD detects the change and rolls it out.

## Run it yourself

```bash
terraform -chdir=infra init && terraform -chdir=infra apply
```

## Observability

<Prometheus/Grafana dashboards, log location, alerts. Add a screenshot.>

## What went wrong and what I learned

- **Problem:** <e.g. pods stuck Pending on Fargate>. **Cause:** <...>. **Fix:** <...>.
- **Problem:** <...>

## Cost notes

<Approximate monthly cost and how to tear it down: `terraform destroy`.>

## Next steps

- <e.g. add Prometheus alerts, blue/green deploys, load tests>
