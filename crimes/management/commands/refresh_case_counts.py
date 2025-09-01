from django.core.management.base import BaseCommand
from django.db import connection

MATERIALIZED_VIEW = "mv_case_counts"

SQL_CREATE = f"""
CREATE TABLE IF NOT EXISTS {MATERIALIZED_VIEW} (status TEXT PRIMARY KEY, count INTEGER NOT NULL);
"""

SQL_REFRESH = f"""
DELETE FROM {MATERIALIZED_VIEW};
INSERT INTO {MATERIALIZED_VIEW}(status, count)
SELECT status, COUNT(1) FROM crimes_case GROUP BY status;
"""


class Command(BaseCommand):
    help = "Refresh materialized view mv_case_counts (simulated table for SQLite)."

    def handle(self, *args, **options):
        with connection.cursor() as cur:
            cur.execute(SQL_CREATE)
            cur.execute(SQL_REFRESH)
        self.stdout.write(self.style.SUCCESS("mv_case_counts refreshed"))
