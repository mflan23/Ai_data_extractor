"""In-process job store (replace with Redis / database for production)."""
from models.schemas import ExtractionJob

jobs: dict[str, ExtractionJob] = {}
