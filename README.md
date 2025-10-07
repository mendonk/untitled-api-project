# Untitled API project

This project aims to stream API logs into a local agent for LLM-powered security assessment.



## Quickstart

Starts the sample application, database, and monitoring service. The agent isn't added yet.

1. Make sure you have the Wine Management API running:
```bash
cd sample_api
python start_api.py
```

2. Install dependencies.
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

### Sample application

A wine management application for testing agents and APIs.

### FastAPI server

The FastAPI server is an interface to the database.

1. To start the frontend server, use the script (for now) at root.

    ```bash
    python3 start_api.py &
    ```

2. To verify startup, run a health check:
    
    ```bash
    curl http://localhost:8000/health
    
    # Returns
    {"status":"healthy","timestamp":"2025-08-26T03:40:00.143544"}
    ```

3. Send a request to the `/wines` endpoint, which queries the connected database.

    ```
    curl -s http://localhost:8000/wines
    [
      {
        "id": "5fb654a4-e9e4-49e1-90b3-229be38e39ff",
        "name": "Château Margaux",
        "vintage": 2015,
        "region_id": "fc0b1779-323f-47ce-b926-b32c9af65d19",
        "grape_variety": "Cabernet Sauvignon Blend",
        "winery": "Château Margaux",
        "alcohol_percentage": 13.5,
        "price": 1500,
        "description": "Exceptional vintage with complex aromas",
        "created_at": "2025-08-26T01:32:42.774277Z",
        "updated_at": "2025-08-26T01:32:42.774277Z",
        "region": {
          "id": "fc0b1779-323f-47ce-b926-b32c9af65d19",
          "name": "Bordeaux",
          "country": "France",
          "description": "Famous wine region known for red blends",
          "climate": "Maritime",
          "soil_type": "Gravel and clay",
          "created_at": "2025-08-26T01:32:42.744880Z",
          "updated_at": "2025-08-26T01:32:42.744880Z"
        }
      },
      ...
    ```


### API Endpoints

The web dashboard provides RESTful API endpoints:

- `GET /api/status` - Current monitoring status and metrics
- `GET /api/health` - Dashboard health check
- `WebSocket /ws` - Real-time updates stream

### Wines database

A PostgreSQL database in Docker.

To start it:

1. Copy the environment configuration and replace your values.
   ```bash
   cp env.example .env
   ```

2. Start the database:
   ```bash
   docker-compose up # add --env-file .env if it's named something else
   ```

   The `init.sql` file automatically runs when the container first starts to create the database schema.


3. Access your database.
   - **PostgreSQL:** `localhost:5432`
     - Database: `untitled_api_db`
     - Username: `postgres`
     - Password: `postgres`

   - **PgAdmin (Web Interface):** `http://localhost:5050`
     - Email: `admin@example.com`
     - Password: `admin`

4. To stop the database:

```bash
docker-compose down
```

To completely reset the database and remove the volume data:

```bash
docker-compose down -v
```
