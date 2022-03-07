# aws-server-less
sample for aws server less architecture

### How to deploy
 - venv
   - `python3 -m venv .env`
   - `source .env/bin/activate`
   - `pip install -r requirements.txt`
 - deploy
   - `cdk deploy`

### How to use s3
 - access url
   - `{ServerLessApp.BucketUrl}`

### How to use API
 - set url to env
   - `export ENDPOINT_URL={ServerLessApp.ServerLessApiEndpoint}`
   - `echo $ENDPOINT_URL`
 - select_data 
   - `https GET "${ENDPOINT_URL}api"`
 - create_data
```commandline
https POST "${ENDPOINT_URL}api" \
param_1="data1" \
param_2="data2" \
param_3="data3" \
param_4="data4"
```
 - request patch
   - `https POST "${ENDPOINT_URL}api/{id}"`
 - requst delete
   - `https DELETE "${ENDPOINT_URL}api/{id}"`
