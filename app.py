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
    aws_iam as iam,
)
import os

class ServerLess(core.Stack):

    def __init__(self, scope: core.App, name: str, **kwargs) -> None:
        super().__init__(scope, name, **kwargs)
        
        # dynamoDB
        table = ddb.Table(
            self, "server-less-table",
            partition_key=ddb.Attribute(
                name="id",
                type=ddb.AttributeType.STRING
            ),
            billing_mode=ddb.BillingMode.PAY_PER_REQUEST,
            removal_policy=core.RemovalPolicy.DESTROY,
            table_name="server-less-table-" + TARGET,
        )

        # s3 bucket
        bucket = s3.Bucket(
            self, "server-less-bucket",
            website_index_document="index.html",
            access_control=s3.BucketAccessControl.PRIVATE,
            removal_policy=core.RemovalPolicy.DESTROY,
            bucket_name="server-less-bucket-" + TARGET,
        )

        # s3 access identity
        identity = cloudfront.OriginAccessIdentity(
            self, "server-less-origin-access-identity",
            comment="s3 access identity　" + TARGET,
        )

        # s3 policy statement
        policy = iam.PolicyStatement(
            actions=['s3:GetObject'],
            effect=iam.Effect.ALLOW,
            principals=[identity.grant_principal],
            resources=[bucket.bucket_arn + "/*"],
        )

        # attach
        bucket.add_to_resource_policy(policy)

        # s3 deploy
        s3_deploy.BucketDeployment(
            self, "server-less-bucket-deployment",
            destination_bucket=bucket,
            # deploy dir is ./dist
            sources=[s3_deploy.Source.asset("./dist")],
            # todo: meaning of retain_on_delete
            retain_on_delete=False,
        )

        # hosted zone
        hosted_zone=r53.HostedZone.from_lookup(
            self,"hosted-zone",
            domain_name=DOMAIN,
        )

        # certificate
        certificate=acm.DnsValidatedCertificate(
            self, "certificate",
            domain_name=CERTIFICATE_DOMAIN,
            subject_alternative_names=[CERTIFICATE_DOMAIN],
            hosted_zone=hosted_zone,
            region="us-east-1",
        )

        # cloud front
        front = cloudfront.CloudFrontWebDistribution(
            self, "server-less-front",
            default_root_object="index.html",
            viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            http_version=cloudfront.HttpVersion.HTTP2,
            price_class=cloudfront.PriceClass.PRICE_CLASS_ALL,
            origin_configs=[
                cloudfront.SourceConfiguration(
                    s3_origin_source=cloudfront.S3OriginConfig(
                        s3_bucket_source=bucket,
                        origin_access_identity=identity
                    ),
                    behaviors=[
                        cloudfront.Behavior(
                            is_default_behavior=True,
                        )
                    ],
                )
            ],
            viewer_certificate=cloudfront.ViewerCertificate.from_acm_certificate(
                certificate,
                aliases=[FRONT_DOMAIN],
                security_policy=cloudfront.SecurityPolicyProtocol.TLS_V1_2_2019,
                ssl_method=cloudfront.SSLMethod.SNI
            ),
            comment="server-less-front-" + TARGET,
        )

        # A record for front
        front_a_record = r53.ARecord(
            self, "front-a-record",
            record_name=FRONT_DOMAIN,
            zone=hosted_zone,
            target=r53.RecordTarget.from_alias(
                r53_targets.CloudFrontTarget(front)
            ),
        )

        # common params for lambda
        common_params = {
            # todo: change python ver
            "runtime": _lambda.Runtime.PYTHON_3_7,
            # todo: anything else to add to env?
            "environment": {
                "TABLE_NAME": table.table_name
            },
        }

        # Lambda functions
        select_data_lambda = _lambda.Function(
            self, "select-data",
            # get code from api.py
            code=_lambda.Code.from_asset("api"),
            # method is select_data
            handler="api.select_data",
            # todo: change memory size
            memory_size=512,
            timeout=core.Duration.seconds(10),
            **common_params,
            function_name="server-less-lambda-select-data-" + TARGET,
            description="server-less-lambda-" + TARGET,
        )
        create_data_lambda = _lambda.Function(
            self, "create-data",
            code=_lambda.Code.from_asset("api"),
            handler="api.create_data",
            **common_params,
            function_name="server-less-lambda-create-data-" + TARGET,
            description="server-less-lambda-" + TARGET,
        )
        update_data_lambda = _lambda.Function(
            self, "update-data",
            code=_lambda.Code.from_asset("api"),
            handler="api.update_data",
            **common_params,
            function_name="server-less-lambda-update-data-" + TARGET,
            description="server-less-lambda-" + TARGET,
        )
        delete_data_lambda = _lambda.Function(
            self, "delete-data",
            code=_lambda.Code.from_asset("api"),
            handler="api.delete_data",
            **common_params,
            function_name="server-less-lambda-delete-data-" + TARGET,
            description="server-less-lambda-" + TARGET,
        )

        # grant permissions
        table.grant_read_data(select_data_lambda)
        table.grant_read_write_data(create_data_lambda)
        table.grant_read_write_data(update_data_lambda)
        table.grant_read_write_data(delete_data_lambda)

        # API Gateway
        api = apigw.RestApi(
            self, "server-less-api",
            default_cors_preflight_options=apigw.CorsOptions(
                # todo: restrict origins and methods
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
            ),
            domain_name=apigw.DomainNameOptions(
                domain_name=API_DOMAIN,
                certificate=certificate
            ),
            rest_api_name="server-less-api-" + TARGET,
        )

        # A record for api
        api_a_record = r53.ARecord(
            self, "api-a-record",
            record_name=API_DOMAIN,
            zone=hosted_zone,
            target=r53.RecordTarget.from_alias(
                r53_targets.ApiGateway(api)
            ),
        )

        api_v1 = api.root.add_resource("v1")
        api_v1_serverless = api_v1.add_resource("server-less")

        # add GET method to /api
        api_v1_serverless.add_method(
            "GET",
            apigw.LambdaIntegration(select_data_lambda),
        )
        # add POST method to /api
        api_v1_serverless.add_method(
            "POST",
            apigw.LambdaIntegration(create_data_lambda),
        )

        api_v1_serverless_id = api_v1_serverless.add_resource("{id}")

        # add POST method to /api/{id}
        api_v1_serverless_id.add_method(
            "POST",
            apigw.LambdaIntegration(update_data_lambda),
        )
        # add DELETE method to /api/{id}
        api_v1_serverless_id.add_method(
            "DELETE",
            apigw.LambdaIntegration(delete_data_lambda),
        )

        # store parameters in SSM
        # todo: check why do I need parameter store?
        ssm.StringParameter(
            self, "TABLE_NAME",
            parameter_name="TABLE_NAME",
            string_value=table.table_name,
        )
        ssm.StringParameter(
            self, "ENDPOINT_URL",
            parameter_name="ENDPOINT_URL",
            string_value=api.url,
        )

app = core.App()

# set context
TARGET = app.node.try_get_context("TARGET")
DOMAIN = app.node.try_get_context("DOMAIN")
FRONT_DOMAIN = app.node.try_get_context("FRONT_DOMAIN")
API_DOMAIN = app.node.try_get_context("API_DOMAIN")
CERTIFICATE_DOMAIN = app.node.try_get_context("CERTIFICATE_DOMAIN")

ServerLess(
    app, "server-less-" + TARGET,
    env={
        "region": os.environ["CDK_DEFAULT_REGION"],
        "account": os.environ["CDK_DEFAULT_ACCOUNT"],
    },
)

app.synth()
