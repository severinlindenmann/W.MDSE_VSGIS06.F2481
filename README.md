# W.MDSE_VSGIS06.F2481
 
docker build -t gis:latest .

gcloud auth activate-service-account

docker run -v "service_key.json":/gcp/creds.json:ro \
  --env GOOGLE_APPLICATION_CREDENTIALS=/gcp/creds.json \
  -p 8080:8080 gis:latest


  docker container prune
  docker image prune
  docker volume prune