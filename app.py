from aws_cdk import (
    core,
    aws_dynamodb as ddb,
    aws_s3 as s3,
    aws_s3_deployment as s3_deploy,
    aws_lambda as _lambda,
    aws_ssm as ssm,
    aws_apigateway as apigw,
    aws_cloudfront as cloudfront,
    aws_certificatemanager as acm,
    aws_route53 as r53,
    aws_route53_targets as r53_targets,
)
import os

class ServerLessApp(core.Stack):

    def __init__(self, scope: core.App, name: str, **kwargs) -> None:
        super().__init__(scope, name, **kwargs)

        # dynamoDB
        table = ddb.Table(
            self, "ServerLessTable",
            partition_key=ddb.Attribute(
                name="id",
                type=ddb.AttributeType.STRING
            ),
            billing_mode=ddb.BillingMode.PAY_PER_REQUEST,
            removal_policy=core.RemovalPolicy.DESTROY
        )

        # s3 bucket
        bucket = s3.Bucket(
            self, "ServerLessBucket",
            website_index_document="index.html",
            public_read_access=True,
            removal_policy=core.RemovalPolicy.DESTROY
        )

        # s3 deploy
        s3_deploy.BucketDeployment(
            self, "BucketDeployment",
            destination_bucket=bucket,
            # deploy dir is ./assets
            sources=[s3_deploy.Source.asset("./assets")],
            # todo: meaning of retain_on_delete
            retain_on_delete=False,
        )

        # hosted zone
        hosted_zone=r53.HostedZone.from_lookup(
            self,"HostedZone",
            domain_name="osaguild.com"
        )

        # cloud front
        front = cloudfront.CloudFrontWebDistribution(
            self, "ServerLessFront",
            default_root_object="/index.html",
            viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            http_version=cloudfront.HttpVersion.HTTP2,
            price_class=cloudfront.PriceClass.PRICE_CLASS_ALL,
            origin_configs=[
                cloudfront.SourceConfiguration(
                    s3_origin_source=cloudfront.S3OriginConfig(
                        s3_bucket_source=bucket
                    ),
                    behaviors=[
                        cloudfront.Behavior(
                            is_default_behavior=True,
                        )
                    ],
                )
            ],
            viewer_certificate=cloudfront.ViewerCertificate.from_acm_certificate(
                acm.DnsValidatedCertificate(
                    self, "Certificate",
                    domain_name="*.osaguild.com",
                    subject_alternative_names=[
                        "*.osaguild.com"
                    ],
                    hosted_zone=hosted_zone,
                    region="us-east-1"
                ),
                aliases=["server-less-app.osaguild.com"],
                security_policy=cloudfront.SecurityPolicyProtocol.TLS_V1_2_2019,
                ssl_method=cloudfront.SSLMethod.SNI
            ),
        )

        # A record
        a_record = r53.ARecord(
            self, "ARecord",
            record_name="server-less-app.osaguild.com",
            zone=hosted_zone,
            target=r53.RecordTarget.from_alias(
                r53_targets.CloudFrontTarget(front)
            )
        )

        # common params for lambda
        common_params = {
            # todo: change python ver
            "runtime": _lambda.Runtime.PYTHON_3_7,
            # todo: anything else to add to env?
            "environment": {
                "TABLE_NAME": table.table_name
            }
        }

        # Lambda functions
        select_data_lambda = _lambda.Function(
            self, "SelectData",
            # get code from api.py
            code=_lambda.Code.from_asset("api"),
            # method is select_data
            handler="api.select_data",
            # todo: change memory size
            memory_size=512,
            timeout=core.Duration.seconds(10),
            **common_params,
        )
        create_data_lambda = _lambda.Function(
            self, "CreateData",
            code=_lambda.Code.from_asset("api"),
            handler="api.create_data",
            **common_params,
        )
        update_data_lambda = _lambda.Function(
            self, "UpdateData",
            code=_lambda.Code.from_asset("api"),
            handler="api.update_data",
            **common_params,
        )
        delete_data_lambda = _lambda.Function(
            self, "DeleteData",
            code=_lambda.Code.from_asset("api"),
            handler="api.delete_data",
            **common_params,
        )

        # grant permissions
        table.grant_read_data(select_data_lambda)
        table.grant_read_write_data(create_data_lambda)
        table.grant_read_write_data(update_data_lambda)
        table.grant_read_write_data(delete_data_lambda)

        # API Gateway
        api = apigw.RestApi(
            self, "ServerLessApi",
            default_cors_preflight_options=apigw.CorsOptions(
                # todo: restrict origins and methods
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
            )
        )

        api_api = api.root.add_resource("api")

        # add GET method to /api
        api_api.add_method(
            "GET",
            apigw.LambdaIntegration(select_data_lambda)
        )
        # add POST method to /api
        api_api.add_method(
            "POST",
            apigw.LambdaIntegration(create_data_lambda)
        )

        api_api_id = api_api.add_resource("{id}")

        # add POST method to /api/{id}
        api_api_id.add_method(
            "POST",
            apigw.LambdaIntegration(update_data_lambda)
        )
        # add DELETE method to /api/{id}
        api_api_id.add_method(
            "DELETE",
            apigw.LambdaIntegration(delete_data_lambda)
        )

        # store parameters in SSM
        # todo: check why do I need parameter store?
        ssm.StringParameter(
            self, "TABLE_NAME",
            parameter_name="TABLE_NAME",
            string_value=table.table_name
        )
        ssm.StringParameter(
            self, "ENDPOINT_URL",
            parameter_name="ENDPOINT_URL",
            string_value=api.url
        )

        # Output parameters
        # check your bucket url and endpoint of api
        core.CfnOutput(self, 'BucketUrl', value=bucket.bucket_website_domain_name)

app = core.App()
ServerLessApp(
    app, "ServerLessApp",
    env={
        "region": os.environ["CDK_DEFAULT_REGION"],
        "account": os.environ["CDK_DEFAULT_ACCOUNT"],
    }
)

app.synth()
