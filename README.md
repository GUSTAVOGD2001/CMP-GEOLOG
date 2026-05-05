# SpiralGeoLog Backend

API REST para análisis petrofísico de archivos LAS 2.0 orientada a PEMEX (campo TLENSE).

## Stack
- Python 3.11
- FastAPI
- NumPy + Pandas
- Docker / Docker Compose

## Endpoints
- `GET /` estado básico.
- `GET /health` healthcheck.
- `POST /upload-las?downsample=5` procesa archivo LAS y retorna metadata, petrofísica, zonas, evaporitas y QC.

## Setup local
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Setup VPS
```bash
git clone <repo> /opt/spiralgeolog
cd /opt/spiralgeolog
docker compose up -d --build
```

## GitHub Secrets requeridos
- `VPS_HOST`
- `VPS_USER`
- `VPS_SSH_KEY`
- `VPS_PORT`

## Prueba con curl
```bash
curl -F "file=@POZO_-1.LAS" http://localhost:8000/upload-las
```
