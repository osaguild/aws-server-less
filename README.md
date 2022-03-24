# aws-server-less
sample for aws server less architecture

### How to deploy
 - venv
   - `python3 -m venv .env`
   - `source .env/bin/activate`
   - `pip install -r requirements.txt`
 - deploy
   - `cdk deploy --require-approval never`

### How to use s3
 - access url
   - `https://server-less.osaguild.com`

### How to use API
 - select_data 
   - `https GET "api.osaguild.com/v1/server-less"`
 - create_data
```commandline
https POST "api.osaguild.com/v1/server-less" \
param_1="data1" \
param_2="data2" \
param_3="data3" \
param_4="data4"
```
 - request patch
   - `https POST "api.osaguild.com/v1/server-less/{id}"`
 - requst delete
   - `https DELETE "api.osaguild.com/v1/server-less/{id}"`
