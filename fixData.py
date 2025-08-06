import sqlite3

conn = sqlite3.connect("deployments.db")
cursor = conn.cursor()

cursor.execute("PRAGMA foreign_keys = ON")

cursor.execute("""
INSERT INTO deployments (feature_id, ambiente, estado, fecha, release_manager)
SELECT id, 'PreDEV', 'Valid', DATE('now'), 'Michel LF'
FROM features
WHERE name IN (
  'sdd-1', 'sdd-2', 'sdd-3', 'sdd-4', 'sdd-5',
  'sdd-6', 'sdd-7', 'sdd-8', 'sdd-9', 'sdd-10',
  'sdd-11', 'sdd-12', 'sdd-13', 'sdd-14', 'sdd-15'
)
""")

conn.commit()
conn.close()
