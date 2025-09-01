from django.db import migrations

VIEW_SQL = """
CREATE VIEW view_case_summary AS
SELECT c.id as case_id,
       c.case_number,
       c.status,
       (SELECT COUNT(1) FROM crimes_evidence e WHERE e.case_id = c.id) AS evidence_count,
       (SELECT COUNT(1) FROM crimes_caseperson cp WHERE cp.case_id = c.id) AS people_count
FROM crimes_case c;
"""

DROP_SQL = "DROP VIEW IF EXISTS view_case_summary;"


class Migration(migrations.Migration):
    dependencies = [
        ("crimes", "0002_case_case_status_idx_evidence_evidence_case_idx"),
    ]

    operations = [
        migrations.RunSQL(DROP_SQL, reverse_sql=""),
        migrations.RunSQL(VIEW_SQL, reverse_sql=DROP_SQL),
    ]
