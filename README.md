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
   - `https://server-less-app.osaguild.com/index.html`

### How to use API
 - select_data 
   - `https GET "server-less-api.osaguild.com/api"`
 - create_data
```commandline
https POST "server-less-api.osaguild.com/api" \
param_1="data1" \
param_2="data2" \
param_3="data3" \
param_4="data4"
```
 - request patch
   - `https POST "server-less-api.osaguild.com/api/{id}"`
 - requst delete
   - `https DELETE "server-less-api.osaguild.com/api/{id}"`
