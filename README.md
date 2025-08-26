

## Database

A PostgreSQL database in Docker.

To start it:

1. Copy environment configuration and replace your values.
   ```bash
   cp env.example .env
   ```

2. **Start the database:**
   ```bash
   docker-compose up # add --env-file .env if it's named something else
   ```

The `init.sql` file automatically runs when the container first starts to create the database schema.


3. **Access your database:**
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
