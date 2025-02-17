# Dishcovery
A recipe search engine. 


Command to build & run docker image: 
docker build -t dishcovery-backend .
docker run -p 8080:8080 \
-v $HOME/.config/gcloud:/root/.config/gcloud \
dishcovery-backend