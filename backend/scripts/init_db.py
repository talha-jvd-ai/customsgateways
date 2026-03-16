"""Initialize database tables and seed data."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import init_database, test_connection
from app.services.qdrant_service import init_collections, test_connection as test_qdrant

print("=" * 60)
print("DATABASE INITIALIZATION")
print("=" * 60)

print("\n1. Testing PostgreSQL connection...")
if test_connection():
    print("✅ PostgreSQL connected")
    print("\n2. Creating tables...")
    init_database()
else:
    print("❌ PostgreSQL connection failed")
    sys.exit(1)

print("\n3. Testing Qdrant connection...")
if test_qdrant():
    print("✅ Qdrant connected")
    print("\n4. Creating collections...")
    init_collections()
else:
    print("⚠️  Qdrant not available")

print("\n" + "=" * 60)
print("INITIALIZATION COMPLETE")
print("=" * 60)
