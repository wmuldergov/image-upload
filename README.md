# Image-Upload HTTP test

This is a quick test to see if we can build an HTTPS upload tool for camera images

# Run Locally
`docker build -t flask-upload-app . `
`docker run -p 5000:5000 flask-upload-app`

To test an upload locally (provided you have that file in the folder you are running this from)
`curl -X POST -u admin:password123 -F "file=@333.jpg" http://127.0.0.1:5000/upload`


## Initial Setup in OpenShift
To quickly get you started in a new namespace, follow these steps. 
1. In the OpenShift Folder there is a `full_config.yaml` file
1. Replace the two instances of `<NAMESPACE>` with the namespace you are installing this on (ie `abc123-dev`)
1. In OpenShift, click the `+` button on the top bar
1. Copy and Paste the YAML file into the page
1. Click `Create` which will automatically create all the required components for the application to function:
    1. Deployment
    1. Service
    1. Route
    1. Network Policy
    1. ImageStream
1. Follow the `Github Action Setup` steps below and trigger the workflow. This should then automatically cause the container to start. Since we are using an ImageStream with Auto Redeploy's configured in the Deployment, anytime you trigger the workflow it will automatically redeploy the application.

#### To Note:
- Route is configured to require being on a BC Gov Network
- The Environment Variables in OpenShift are in the Deployment.
- The application will automatically restart with the latest image from the last build.yml run

## GitHub Action Setup
The build.yml github action will build the Dockerfile and push it to the OpenShift ImageStream you have configured. The Deployment in OpenShift is configured to update when there is a new image available so it will restart.
Before you can run the workflow, ensure you have these variables and secrets configured in the Repo:
- `OPENSHIFT_IMAGESTREAM_URL` variable
    - Looks like: `image-registry.apps.silver.devops.gov.bc.ca/NAMESPACE/` (including -dev, test, prod or tools)
- `OPENSHIFT_IMAGESTREAM_USERNAME` secret
    - You can use the Pipeline user
- `OPENSHIFT_IMAGESTREAM_TOKEN` secret
    - You can use the Pipeline Token (From pipeline-token-xxxxxxxx)


## License
```
Copyright 2025 Province of British Columbia

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```