# Fraud-Risk Intelligence Dashboard for Aged Care

This dashboard visualises simulated fraud-risk indicators for aged care services.

## Features
- Claimed amount trends
- Benchmarking against expected service hours
- Day-of-week anomaly checks
- Provider-level risk profiling
- Interactive drilldowns

## Running Locally with Docker
```bash
docker build -t agedcare-dashboard .
docker run -p 8501:8501 agedcare-dashboard

# agecareSim
