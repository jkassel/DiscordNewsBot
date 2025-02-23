import os
from aws_cdk import (
    Stack,
    CfnOutput,
    aws_apigatewayv2 as apigw,
    aws_apigatewayv2_integrations as integrations,
    Duration,
    RemovalPolicy,
    aws_secretsmanager as secretsmanager,
    BundlingOptions,
    aws_s3 as s3,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_events as events,
    aws_events_targets as targets,
    Fn,
)
from constructs import Construct


class DiscordNewsBotStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, app_name: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # Import API Gateway ID and Endpoint from Shared Stack
        api_gateway_id = Fn.import_value("ApiGatewayId")
        api_endpoint = Fn.import_value("ApiGatewayEndpoint")

        # Import the existing API Gateway
        http_api = apigw.HttpApi.from_http_api_attributes(
            self, f"{app_name}DiscordBotSharedApi",
            http_api_id=api_gateway_id,
            api_endpoint=api_endpoint
        )

        # S3 Bucket for Processed News Files
        news_bucket = s3.Bucket(
            self,
            f"{app_name}NewsBotProcessedPostsBucket",
            versioned=True,
            removal_policy=RemovalPolicy.RETAIN,
            auto_delete_objects=False,
        )

        news_discord_bot_secret = secretsmanager.Secret.from_secret_name_v2(
            self,
            f"{app_name}NewsDiscordBotSecrets",
            secret_name=f"{app_name}/Prod/NewsBot/DiscordSecrets",
        )

        news_bluesky_secret = secretsmanager.Secret.from_secret_name_v2(
            self,
            "NewsBotBlueskySecrets",
            secret_name=f"{app_name}/Prod/NewsBot/BlueskySecrets",
        )

        news_bot_lambda_role = iam.Role(
            self,
            f"{app_name}NewsBotLambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
            ],
        )

        news_discord_bot_secret.grant_read(news_bot_lambda_role)
        news_bluesky_secret.grant_read(news_bot_lambda_role)
        news_bucket.grant_read_write(news_bot_lambda_role)

        lambda_code_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../")
        )

        news_bot_lambda = _lambda.Function(
            self,
            f"{app_name}NewsBotLambda",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="news_bot_main.lambda_handler",
            code=_lambda.Code.from_asset(
                lambda_code_path + "/lambda",
                bundling=BundlingOptions(
                    image=_lambda.Runtime.PYTHON_3_11.bundling_image,
                    command=[
                        "bash",
                        "-c",
                        """pip install \
                            --cache-dir=/tmp/.pip-cache \
                            -r requirements.txt \
                            -t /asset-output && \
                        cp -r . /asset-output""",
                    ],
                ),
            ),
            role=news_bot_lambda_role,
            environment={
                "DISCORD_BOT_SECRET_ARN": news_discord_bot_secret.secret_arn,
                "DISCORD_POST_TYPE": "forum",  # or channel
                "BLUESKY_SECRET_ARN": news_bluesky_secret.secret_arn,
                "S3_BUCKET": news_bucket.bucket_name,
                "LOG_LEVEL": "DEBUG",
            },
            timeout=Duration.seconds(300),
            memory_size=512
        )

        # Add a Scheduled Event for News Bot
        news_bot_schedule_rule = events.Rule(
            self,
            f"{app_name}NewsBotScheduleRule",
            schedule=events.Schedule.rate(Duration.minutes(10)),
        )

        # Add the Lambda as Target with Task Parameter
        news_bot_schedule_rule.add_target(
            targets.LambdaFunction(
                news_bot_lambda,
                event=events.RuleTargetInput.from_object(
                    {
                        "source": "aws.events",
                        "detail": {"task": "news_post"},
                    }
                ),
            )
        )

        # Grant EventBridge Permission to Invoke Lambda
        news_bot_lambda.add_permission(
            "AllowEventBridgeInvoke",
            principal=iam.ServicePrincipal("events.amazonaws.com"),
            action="lambda:InvokeFunction",
        )

        # Define the integration
        http_integration = integrations.HttpLambdaIntegration(
            f"{app_name}NewsBotIntegration",
            handler=news_bot_lambda,
            payload_format_version=apigw.PayloadFormatVersion.VERSION_2_0,
        )

        # Create the route explicitly
        apigw.HttpRoute(
            self,
            f"{app_name}NewsBotRoute",
            http_api=http_api,
            route_key=apigw.HttpRouteKey.with_("/news-bot", apigw.HttpMethod.POST),
            integration=http_integration,
        )

        # Output the API Gateway URL for easy access
        CfnOutput(
            self,
            f"{app_name}NewsBotApiEndpoint",
            value=http_api.api_endpoint + "/news-bot",
        )
