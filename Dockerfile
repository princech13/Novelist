FROM python:3.13-slim

WORKDIR /app

# Create a system group/user WITH a home directory so HuggingFace hub can
# write its lock files.  The model cache itself is redirected to /app/.cache
# (owned by novelist) via HF_HOME so nothing ever touches /home/novelist at
# runtime.
RUN groupadd --system novelist \
 && useradd --system --gid novelist --create-home novelist

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Pre-download the embedding model at build time so the first search request
# does not stall waiting for a ~90 MB download, and so the container works
# fully offline after the image is built.
ENV HF_HOME=/app/.cache/huggingface
RUN python - <<'EOF'
from sentence_transformers import SentenceTransformer
SentenceTransformer("all-MiniLM-L6-v2")
print("Model cached.")
EOF

RUN chown -R novelist:novelist /app

USER novelist
EXPOSE 8081
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8081"]
