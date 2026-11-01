FROM node:22-bookworm-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN CI=true npm run build

FROM python:3.12-slim-bookworm
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . ./
COPY --from=frontend /app/frontend/build ./frontend/build
RUN python manage.py collectstatic --noinput
ENV DJANGO_DEBUG=false
EXPOSE 8000
RUN chmod +x /app/entrypoint.sh
CMD ["/app/entrypoint.sh"]
