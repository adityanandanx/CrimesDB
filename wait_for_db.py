import os
import time
import sys

try:
    import psycopg
except ImportError:  # safety; in our image psycopg is installed
    print("psycopg not installed; skipping wait.")
    sys.exit(0)

MAX_ATTEMPTS = int(os.getenv("DB_MAX_ATTEMPTS", "30"))
SLEEP_SECONDS = float(os.getenv("DB_SLEEP_SECONDS", "2"))

db_url = os.getenv("DATABASE_URL")

def attempt_once():
    if db_url:
        psycopg.connect(db_url).close()
        return
    host = os.getenv("POSTGRES_HOST", "db")
    user = os.getenv("POSTGRES_USER", "criminal")
    password = os.getenv("POSTGRES_PASSWORD", "criminal")
    name = os.getenv("POSTGRES_DB", "criminal")
    port = int(os.getenv("POSTGRES_PORT", "5432"))
    sslmode = os.getenv("DB_SSLMODE")
    conninfo = {
        "host": host,
        "user": user,
        "password": password,
        "dbname": name,
        "port": port,
    }
    if sslmode:
        conninfo["sslmode"] = sslmode
    psycopg.connect(**conninfo).close()

for attempt in range(1, MAX_ATTEMPTS + 1):
    try:
        attempt_once()
        print(f"Database reachable (attempt {attempt}).")
        break
    except Exception as e:  # broad: we just retry
        print(f"Waiting for database (attempt {attempt}/{MAX_ATTEMPTS}): {e}")
        if attempt == MAX_ATTEMPTS:
            print("ERROR: Database not reachable; giving up.", file=sys.stderr)
            sys.exit(1)
        time.sleep(SLEEP_SECONDS)
