# Resume Strength Analyzer - container image (Hugging Face Spaces / any Docker host).
#
# Both models are downloaded at build time so the first visitor never waits for
# them, and a single gunicorn worker is enforced because analysis results live
# in that worker's memory (see resume_analyzer/web/store.py).

FROM python:3.12-slim

# Spaces runs containers as uid 1000; matching it keeps the cache writable.
RUN useradd --create-home --uid 1000 user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    HF_HOME=/home/user/.cache/huggingface \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=7860 \
    WARM_MODEL=1 \
    STRICT_SINGLE_WORKER=1

WORKDIR /app

# CPU-only torch first: the default wheel drags in ~2.5 GB of CUDA libraries
# that are useless here and would not fit a free Space.
COPY requirements.txt ./
RUN pip install --upgrade pip \
 && pip install torch --index-url https://download.pytorch.org/whl/cpu \
 && pip install -r requirements.txt

COPY --chown=user:user . /app
USER user

# Bake the sentence-embedding model into the image (spaCy's model is already a
# pip dependency). Fails the build rather than shipping an image that would
# silently disable JD fit.
RUN python -c "from resume_analyzer.semantic import model; assert model.warm_up(), 'model download failed'"

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:7860/healthz', timeout=8).status == 200 else 1)"

# One worker, several threads: the work is I/O- and CPU-light per request once
# the models are loaded, and results must stay in a single process.
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:7860", "--workers", "1", "--threads", "4", \
     "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-"]
