# ImageMorpher

A public API for morphing two faces together using dlib facial landmark detection and Delaunay triangulation.

![Image Morpher](docs/yin-yang.png "Image Morpher")

The iOS app (React Native): https://github.com/osamja/imagemorpher-mobile

## Stack

- **Backend:** Django 3.2, Django REST Framework
- **Face detection:** dlib (frontal face detector + 68-point shape predictor)
- **Morphing:** scipy, numpy, scikit-image (Delaunay triangulation + affine warping)
- **Task queue:** Dramatiq + Redis
- **Database:** PostgreSQL (production), SQLite (local dev)
- **Deployment:** Docker, Linode (pyaar.ai)

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/morph` | Health check |
| POST | `/morph/morph/upload` | Upload two face images for morphing |
| GET | `/morph/morph/status/<uuid>/` | Poll morph job status |
| GET | `/facemorphs/<filename>` | Serve morphed image |

## Local Development

1. Create a `.env` file in the `imagemorpher/` directory:
   ```
   SECRET_KEY='<generate with command below>'
   ```
   ```bash
   python manage.py shell -c 'from django.core.management import utils; print(utils.get_random_secret_key())'
   ```

2. Build the Docker image:
   ```bash
   docker build -t face-morpher-api:dev -f Dockerfile .
   ```

3. Run locally:
   ```bash
   docker run -it -p 8000:8000 -e SECRET_KEY='your-secret-key' face-morpher-api:dev
   ```

4. Test with curl:
   ```bash
   curl -X POST http://localhost:8000/morph/morph/upload \
     -F "firstImageRef=@path/to/face1.jpg" \
     -F "secondImageRef=@path/to/face2.jpg"
   ```

## Production Deployment (Linode)

The service runs as part of the `nginx_sammyjaved_proxy` docker-compose stack on Linode, behind nginx at `pyaar.ai/morph`.

Services: `face-morpher-api` (gunicorn), `dramatiq_worker`, `my-redis`, `prod-postgres`.

To deploy a new version:
```bash
# Build and transfer
docker build -t face-morpher-api:<version> -f Dockerfile .
docker save face-morpher-api:<version> | gzip > /tmp/face-morpher-api.tar.gz
scp -P 44444 /tmp/face-morpher-api.tar.gz sammy@173.255.217.39:/tmp/

# On Linode
docker load < /tmp/face-morpher-api.tar.gz
# Update image tag in ~/workspace/nginx_sammyjaved_proxy/docker-compose.yml
cd ~/workspace/nginx_sammyjaved_proxy && docker compose up -d
docker exec <api-container> python manage.py migrate
```

## Debug a Container

```bash
docker-compose -f docker-compose.yml run --rm face-morpher-api /bin/bash
python manage.py runserver 0:8000
```
