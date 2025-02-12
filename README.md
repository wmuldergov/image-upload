# Image-Upload HTTP test

This is a quick test to see if we can build an HTTPS upload tool for camera images

To test
`docker build -t flask-upload-app . `
`docker run -p 5000:5000 flask-upload-app`

To test an upload locally (provided you have that file in the folder you are running this from)
`curl -X POST -u admin:password123 -F "file=@333.jpg" http://127.0.0.1:5000/upload`