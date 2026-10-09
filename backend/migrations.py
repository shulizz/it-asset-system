"""Idempotent additive migrations; ambiguous names never establish ownership."""
from sqlalchemy import text


def migrate_workflow(engine):
    columns = {
        'users': ['token_version INTEGER NOT NULL DEFAULT 0'],
        'transfer_records': ['department_id INTEGER', 'new_department_id INTEGER', 'operator_id INTEGER', 'old_user VARCHAR(50)'],
        'scrap_requests': ['department_id INTEGER', 'applicant_id INTEGER', 'approver_id INTEGER'],
        'delete_requests': ['department_id INTEGER', 'applicant_id INTEGER', 'approver_id INTEGER',
                           'application_type VARCHAR(20)', 'target_user VARCHAR(50)',
                           'target_department_id INTEGER', 'asset_type VARCHAR(20)', 'asset_id INTEGER'],
    }
    with engine.begin() as conn:
        for table, definitions in columns.items():
            existing = {row[1] for row in conn.execute(text(f'PRAGMA table_info({table})'))}
            for definition in definitions:
                name = definition.split()[0]
                if name not in existing:
                    conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {definition}'))
                if name.endswith('_id'):
                    conn.execute(text(f'CREATE INDEX IF NOT EXISTS ix_{table}_{name} ON {table} ({name})'))
        conn.execute(text('CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY)'))
        if conn.execute(text("SELECT name FROM schema_migrations WHERE name='workflow_ids_v1'")).scalar():
            return
        for table in ('scrap_requests', 'transfer_records'):
            conn.execute(text(f'''UPDATE {table} SET department_id=(SELECT id FROM departments WHERE name={table}.department)
                                  WHERE department_id IS NULL AND department IS NOT NULL'''))
        conn.execute(text('''UPDATE transfer_records SET new_department_id=(SELECT id FROM departments WHERE name=transfer_records.new_dept)
                             WHERE new_department_id IS NULL AND new_dept IS NOT NULL'''))
        pairs = {'scrap_requests': [('applicant_id', 'applicant'), ('approver_id', 'auditor')],
                 'delete_requests': [('applicant_id', 'applicant'), ('approver_id', 'approver')],
                 'transfer_records': [('operator_id', 'operator')]}
        for table, fields in pairs.items():
            for identity, name in fields:
                conn.execute(text(f'''UPDATE {table} SET {identity}=(SELECT min(id) FROM users WHERE users.name={table}.{name})
                    WHERE {identity} IS NULL AND (SELECT count(*) FROM users WHERE users.name={table}.{name})=1'''))
        model_tables = {'it': 'it_assets', 'phone': 'phone_assets', 'medical': 'medical_assets'}
        for row in conn.execute(text("SELECT id, reason FROM delete_requests WHERE table_name='apply_requests' AND application_type IS NULL")).all():
            parts = (row.reason or '').split('|')
            if len(parts) != 5 or parts[0] not in ('checkout', 'transfer', 'scrap') or parts[3] not in model_tables:
                continue
            try:
                asset_id = int(parts[4])
            except ValueError:
                continue
            target = conn.execute(text('SELECT id FROM departments WHERE name=:name'), {'name': parts[2]}).scalar()
            source = conn.execute(text(f'SELECT department_id FROM {model_tables[parts[3]]} WHERE id=:id'), {'id': asset_id}).scalar()
            if parts[2] and not target:
                continue
            conn.execute(text('''UPDATE delete_requests SET application_type=:action, target_user=:recipient,
                target_department_id=:target, department_id=:source, asset_type=:type, asset_id=:asset WHERE id=:id'''),
                {'action': parts[0], 'recipient': parts[1], 'target': target, 'source': source,
                 'type': parts[3], 'asset': asset_id, 'id': row.id})
        for table in ('it_assets', 'phone_assets', 'medical_assets', 'phone_numbers', 'scrap_requests', 'transfer_records'):
            conn.execute(text(f'''UPDATE delete_requests SET department_id=(SELECT department_id FROM {table} WHERE id=record_id)
                WHERE department_id IS NULL AND table_name=:table'''), {'table': table})

        conn.execute(text("INSERT INTO schema_migrations(name) VALUES ('workflow_ids_v1')"))
