FROM python:3.13-slim

WORKDIR /app

# Run the application as an unprivileged user.
RUN groupadd --system novelist \
 && useradd --system --gid novelist --create-home novelist

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

RUN chown -R novelist:novelist /app

USER novelist
EXPOSE 8081
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8081"]
