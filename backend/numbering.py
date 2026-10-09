"""Persisted high-water marks; callers hold the database write transaction."""
from datetime import date
from sqlalchemy import text


def next_asset_number(db, model, prefix):
    stem = f'{prefix}-{date.today().year}-'
    # Also accommodate externally supplied/imported numbers above the sequence.
    numbers = db.query(model.asset_number).filter(model.asset_number.like(stem + '%')).all()
    maximum = max((int(n[len(stem):]) for (n,) in numbers if n[len(stem):].isdigit()), default=0)
    value = db.execute(text('''
        INSERT INTO asset_sequences (name, value) VALUES (:name, :initial)
        ON CONFLICT(name) DO UPDATE SET value = max(asset_sequences.value, :maximum) + 1
        RETURNING value
    '''), {'name': stem, 'initial': maximum + 1, 'maximum': maximum}).scalar_one()
    return f'{stem}{value:03d}'
