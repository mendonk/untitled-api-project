# Quickstart

Prerequisites

1. Make sure you have the Wine Management API running:
```bash
cd sample_api
python start_api.py
```

2. Install Dependencies
The monitoring application uses the dependencies from the main project's `requirements.txt`.
```bash
cd /home/mk/Documents/GitHub/untitled-api-project
pip install -r requirements.txt
```

3. Start demo app.

```bash
cd monitoring
python demo.py
```

Optionally, start the monitor with the web dashboard:
```bash
python start_monitor.py dashboard
```

Open http://localhost:8080 in your browser to display the web dashboard.

## Configuration

The monitoring system uses `monitoring_config.yaml` for configuration.
Set these values for your deployment monitoring.
If no yaml is found, defaults are loaded.
```yaml
api:
  base_url: "http://localhost:8000"
  timeout: 10
  endpoints:
    - "/"
    - "/health"
    - "/regions"
    - "/wines"
    - "/search/wines"

monitoring:
  check_interval: 30
  metrics_retention: 1000
  alert_retention_days: 7

monitoring_agent:
  response_time_threshold: 2.0
  error_rate_threshold: 0.05
  anomaly_sensitivity: 2.0
  baseline_window: 50
```

## API Endpoints

The web dashboard provides RESTful API endpoints:

- `GET /api/status` - Current monitoring status and metrics
- `GET /api/health` - Dashboard health check
- `WebSocket /ws` - Real-time updates stream
