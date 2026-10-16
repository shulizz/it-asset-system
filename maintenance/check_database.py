"""Read-only integrity/count checks; never imports the application or migrates."""

import argparse
import json
import sqlite3
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    args = parser.parse_args()
    path = args.database.resolve(strict=True)
    with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as db:
        tables = [
            row[0]
            for row in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        ]
        counts = {
            table: db.execute('SELECT count(*) FROM "' + table.replace('"', '""') + '"').fetchone()[
                0
            ]
            for table in tables
        }
        print(
            json.dumps(
                {
                    "integrity": db.execute("PRAGMA integrity_check").fetchone()[0],
                    "foreign_key_violations": len(
                        db.execute("PRAGMA foreign_key_check").fetchall()
                    ),
                    "counts": counts,
                },
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()
