from sqlite3 import Error
import sqlite3
import os
from pathlib import Path


def db_create(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS clipboards(
                    id INTEGER UNIQUE,
                    clip TEXT
                    )
                """
        )
        conn.commit()
        print("Scucessfully created database")
    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()


try:
    path = f"/home/{os.uname().nodename}/.nclip/db.sqlite3"
    file_path = Path(path)
    file_path.touch(exist_ok=True)
    db_create(path)
except Exception as e:
    print(f"Error --{e}")
