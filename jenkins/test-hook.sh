#! /bin/bash

curl -X POST \ 
  -u "<user id>:<api token> \ 
  "https://jenkinsfsa-dev.dl.usda.gov/job/run-sonar-scanner/build?token=<sonar-token>" 