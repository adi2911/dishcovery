# Dishcovery
A recipe search engine. 


Command to build & run docker image: 

### Backend
docker build -t dishcovery-backend .

Grant Access to Secret Manager in Google Cloud

	1.	Go to IAM & Admin > IAM.
	2.	Find your service account (or create one) used for Firestore access.
	3.	Assign the role Secret Manager Secret Accessor to your service account.

gcloud auth application-default login

Build then,
```
docker run -p 8081:8081 \
-v $HOME/.config/gcloud:/root/.config/gcloud \
dishcovery-backend
```


### Frontend

docker build -t dishcovery-web .

docker run -p 8080:8080 dishcovery-web
