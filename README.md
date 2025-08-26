
A wine management application for testing agents and APIs.

## FastAPI server

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

## Wines database

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
