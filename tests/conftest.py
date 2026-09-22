import pytest

from resume_analyzer.extraction.document import load_document
from scripts.sample_resumes import BUILDERS


@pytest.fixture(scope="session")
def samples():
    """Generated layout variants: key -> (filename, bytes)."""
    return {key: build() for key, build in BUILDERS.items()}


@pytest.fixture(scope="session")
def docs(samples):
    """Loaded Documents for every sample, keyed like ``samples``."""
    return {key: load_document(data, name) for key, (name, data) in samples.items()}
