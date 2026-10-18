import os

# Set before any test module imports main, which reads INTERNAL_API_KEY at import time.
os.environ.setdefault("INTERNAL_API_KEY", "test-internal-key")
