# Dishcovery
A recipe search engine. 



### How to run locally
1. In dishcovery/web/src/store/contants.tsx : Change ```CLOUD_RUN``` value to ``` http://127.0.0.1:8080/api```
2. Open two terminals : a. dishcovery/backend , b. dishcovery/web
3. In dishcovery/web: a. ```npm install```,  b. ```npm start```
4. In dishcovery/backend: a. ```pip install -r requirements.txt```, b. ```python src/app.py```
5. Open localhost:3000 in browser


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

### Downloading lmdb index
The index will be downloaded into the directory from which the command is executed by default. To change the destination, replace the ```.``` with your desired target location.
	
 	1. gsutil -m cp -r gs://index_data_dishcovery/inverted_index_2.lmdb .

### Downloading doc map file
The doc_map will be downloaded into the directory from which the command is executed by default. To change the destination, replace the ```.``` with your desired target location.
	
 	1. gsutil -m cp -r gs://index_data_dishcovery/doc_map.json .

### Frontend

docker build -t dishcovery-web .

docker run -p 8080:8080 dishcovery-web
