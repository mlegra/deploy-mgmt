# migrate.py
from model import create_db, migrate_features_to_normalized

create_db()
migrate_features_to_normalized()

print("✅ Migration complete.")