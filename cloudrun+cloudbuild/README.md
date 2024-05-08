# Overview

Cloud Run is a managed compute platform that enables you to run stateless containers that are invocable via HTTP requests. Cloud Run is serverless: it abstracts away all infrastructure management, so you can focus on what matters most — building great applications.

Cloud Run is built from Knative, letting you choose to run your containers either fully managed with Cloud Run, or in your Google Kubernetes Engine cluster with Cloud Run on GKE.

The goal of this lab is for you to build a simple containerized application image and deploy it to Cloud Run.

# Objectives

- Enable the Cloud Run API.
- Create a simple Node.js application that can be deployed as a serverless, stateless container.
- Containerize your application and upload to Container Registry (now called "Artifact Registry.")
- Deploy a containerized application on Cloud Run.
- Delete unneeded images to avoid incurring extra storage charges.

# Enable the Cloud Run API and configure your Shell environment

- From Cloud Shell, enable the Cloud Run API :

```
gcloud services enable run.googleapis.com
```

Set the compute region:

```
gcloud config set compute/region us-central1
```

Create a LOCATION environment variable:

```
export LOCATION=us-central1
```

# Write the sample application

- In Cloud Shell create a new directory named helloworld, then move your view into that directory:

```
mkdir helloworld && cd helloworld
```

- Create a package.json file, then add the following content to it:

```
{
  "name": "helloworld",
  "description": "Simple hello world sample in Node",
  "version": "1.0.0",
  "main": "index.js",
  "scripts": {
    "start": "node index.js"
  },
  "author": "Google LLC",
  "license": "Apache-2.0",
  "dependencies": {
    "express": "^4.17.1"
  }
}
```

- In the same directory, create a index.js file, and copy the following lines into it:

```
const express = require('express');
const app = express();
const port = process.env.PORT || 8080;

app.get('/', (req, res) => {
  const name = process.env.NAME || 'World';
  res.send(`Hello ${name}!`);
});

app.listen(port, () => {
  console.log(`helloworld: listening on port ${port}`);
});
```

# Containerize your app and upload it to Artifact Registry

- Create a Dockerfile in the same directory as the source files, and add the following content:

```
# Use the official lightweight Node.js 12 image.
# https://hub.docker.com/_/node
FROM node:12-slim

# Create and change to the app directory.
WORKDIR /usr/src/app

# Copy application dependency manifests to the container image.
# A wildcard is used to ensure copying both package.json AND package-lock.json (when available).
# Copying this first prevents re-running npm install on every code change.
COPY package*.json ./

# Install production dependencies.
# If you add a package-lock.json, speed your build by switching to 'npm ci'.
# RUN npm ci --only=production
RUN npm install --only=production

# Copy local code to the container image.
COPY . ./

# Run the web service on container startup.
CMD [ "npm", "start" ]
```

# Cloud Build

Build your container image using Cloud Build by running the following command from the directory containing the Dockerfile. (Note the $GOOGLE_CLOUD_PROJECT environmental variable in the command, which contains your lab's Project ID):

```
gcloud builds submit --tag gcr.io/$GOOGLE_CLOUD_PROJECT/helloworld
```

Cloud Build is a service that executes your builds on Google Cloud. It executes a series of build steps, where each build step is run in a Docker container to produce your application container (or other artifacts) and push it to Cloud Registry, all in one command.

Once pushed to the registry, you will see a SUCCESS message containing the image name (gcr.io/[PROJECT-ID]/helloworld). The image is stored in Artifact Registry and can be re-used if desired.

- List all the container images associated with your current project using this command:

```
gcloud container images list
```

- Register gcloud as the credential helper for all Google-supported Docker registries:

```
gcloud auth configure-docker
```

- To run and test the application locally from Cloud Shell, start it using this standard docker command:

```
docker run -d -p 8080:8080 gcr.io/$GOOGLE_CLOUD_PROJECT/helloworld
```

- In the Cloud Shell window, click on Web preview and select Preview on port 8080. This should open a browser window showing the "Hello World!" message.

# Deploy to Cloud Run

- Deploying your containerized application to Cloud Run is done using the following command adding your Project-ID:


```
gcloud run deploy helloworld --image gcr.io/$GOOGLE_CLOUD_PROJECT/helloworld --allow-unauthenticated --region $LOCATION

# Note: The allow-unauthenticated flag in the command above makes your service publicly accessible.
```

- On success, the command line displays the service URL:

```
Service [helloworld] revision [helloworld-00001-xit] has been deployed
and is serving 100 percent of traffic.

Service URL: https://helloworld-h6cp412q3a-uc.a.run.app
```

- You can now visit your deployed container by opening the service URL in any browser window. This is a functioning url that points to the deployed container.
- From the Navigation menu, in the Serverless section, click Cloud Run and you should see your helloworld service listed.










