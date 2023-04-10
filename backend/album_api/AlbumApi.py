from cdktf import (
    Resource,
    Token,
    Fn,
    TerraformIterator,
    TerraformAsset,
    AssetType,
    TerraformOutput,
)
from constructs import Construct

from imports.aws.security_group import SecurityGroup
from imports.aws.security_group_rule import SecurityGroupRule

from imports.null.resource import Resource as NullResource
import checksumdir

from imports.time.sleep import Sleep

from imports.aws.s3_bucket import S3Bucket, S3BucketWebsite
from imports.aws.s3_object import S3Object
from imports.aws.s3_bucket_policy import S3BucketPolicy
from imports.aws.s3_bucket_website_configuration import (
    S3BucketWebsiteConfiguration,
    S3BucketWebsiteConfigurationErrorDocument,
    S3BucketWebsiteConfigurationIndexDocument,
)


from imports.aws.ecr_repository import EcrRepository
from imports.aws.data_aws_ecr_image import DataAwsEcrImage

from imports.aws.iam_role import IamRole, IamRoleInlinePolicy

from imports.aws.iam_policy_attachment import IamPolicyAttachment
from imports.aws.iam_role_policy_attachment import IamRolePolicyAttachment
from imports.aws.lambda_permission import LambdaPermission
from imports.aws.lambda_function import (
    LambdaFunction,
    LambdaFunctionEnvironment,
    LambdaFunctionVpcConfig,
)

from imports.aws.elasticache_cluster import ElasticacheCluster

from imports.aws.apigatewayv2_api import (
    Apigatewayv2Api,
    Apigatewayv2ApiCorsConfiguration,
)

from imports.aws.apigatewayv2_integration import Apigatewayv2Integration
from imports.aws.apigatewayv2_route import Apigatewayv2Route
from imports.aws.apigatewayv2_stage import Apigatewayv2Stage
from imports.aws.apigatewayv2_deployment import Apigatewayv2Deployment

from imports.aws.lambda_function_event_invoke_config import (
    LambdaFunctionEventInvokeConfig,
)

from imports.aws.dynamodb_table import DynamodbTable, DynamodbTableAttribute

from lib.EnvironmentOptions import EnvironmentOptions
import os
import json


class AlbumApi(Resource):
    def __init__(
        self,
        scope: Construct,
        id: str,
        env_opts: EnvironmentOptions,
        # repository: EcrRepository
        # cache_host: str,
        # cache_port: str,
        # security_group_ids: list[str],
        # subnet_ids: list[str],
    ):
        self.env_opts = env_opts
        # self.repository = repository
        super().__init__(scope, id)

        component_name = f"{self.env_opts.project_name}-album-api"

        # role ----------------------------------------------------------------------------

        role = IamRole(
            self,
            f"{component_name}-lambda-exec",
            name=f"{component_name}-lambda-exec",
            assume_role_policy=json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": {
                        "Action": "sts:AssumeRole",
                        "Principal": {
                            "Service": "lambda.amazonaws.com",
                        },
                        "Effect": "Allow",
                        "Sid": "",
                    },
                }
            ),
            # inline_policy=[
            #     IamRoleInlinePolicy(
            #         name="AllowDynamoDB",
            #         policy=json.dumps(
            #             {
            #                 "Version": "2012-10-17",
            #                 "Statement": {
            #                     "Action": [
            #                         "dynamodb:Scan",
            #                         "dynamodb:Query",
            #                         "dynamodb:BatchGetItem",
            #                         "dynamodb:GetItem",
            #                         "dynamodb:PutItem",
            #                     ],
            #                     "Resource": self.table.arn,
            #                     "Effect": "Allow",
            #                 },
            #             }
            #         ),
            #     )
            # ],
        )

        # IamRolePolicyAttachment(
        #     self,
        #     "lambda-managed-policy-vpc-exec",
        #     policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole",
        #     role=role.name,
        # )

        IamRolePolicyAttachment(
            self,
            "lambda-managed-policy-exec",
            policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
            role=role.name,
        )

        # create api
        self.api = Apigatewayv2Api(
            self,
            f"{env_opts.project_name}-sync_album_api",
            name=f"{env_opts.project_name}-sync_album_api",
            protocol_type="HTTP",
            cors_configuration=Apigatewayv2ApiCorsConfiguration(
                allow_origins=["*"],
                allow_methods=["*"],
                allow_headers=["*"],
            ),
        )

        self.api_stage = Apigatewayv2Stage(
            self,
            f"{env_opts.project_name}-api-stage",
            api_id=self.api.id,
            name="default",
        )

        # sync-album -----------------------------------------------------------------
        # -----------------------------------------------------------------------------
        # create lambda

        image_name = "sync_album_lambda"
        image_tag = "dev"
        image_path = os.path.join(os.path.dirname(__file__), image_name)

        self.sync_album_ecr_repo = EcrRepository(
            self,
            f"{image_name}-repo",
            name="sync_album_lambda",
            force_delete=True,
        )

        repository_url = self.sync_album_ecr_repo.repository_url
        repository_name = self.sync_album_ecr_repo.name

        self.build_null = NullResource(
            self,
            "build-sync-album-container",
            triggers={
                "build-sync-album-container": checksumdir.dirhash(image_path),
            },
            depends_on=[
                self.sync_album_ecr_repo,
            ],
        )
        self.build_null.add_override(
            path="provisioner.local-exec.command",
            value=f"""aws ecr get-login-password --region {self.env_opts.region} | docker login --username AWS --password-stdin {repository_url} && \
            cd {image_path} && docker build -t {image_name} . --no-cache && \
            docker tag {image_name} {repository_url}:{image_tag} && \
            docker push {repository_url}:{image_tag}""",
        )

        # ).add_override(
        #     path="provisioner.local-exec.command",
        #     value=f"""aws ecr get-login-password --region {self.env_opts.region} | docker login --username AWS --password-stdin {repository_url} && \
        #     cd {image_path} && docker build -t {image_name} . --no-cache && \
        #     docker tag {image_name} {repository_url}:{image_tag} && \
        #     docker push {repository_url}:{image_tag}""",
        # )

        TerraformOutput(
            self,
            "ecr-repository-url-output-1",
            value=repository_url,
        )

        self.sleep_90 = Sleep(
            self,
            "wait90",
            depends_on=[
                self.build_null,
            ],
            create_duration="90s",
        )

        # # This resource will create (at least) 30 seconds after null_resource.previous
        # resource "null_resource" "next" {
        #   depends_on = [time_sleep.wait_30_seconds]
        # }

        self.ecr_image = DataAwsEcrImage(
            self,
            f"{image_name}-image",
            registry_id="150290272294",
            repository_name=repository_name,
            image_tag=image_tag,
            # most_recent=True,
            depends_on=[
                self.sleep_90,
            ],
        )

        TerraformOutput(
            self,
            "ecr-repository-url-output",
            value=repository_url,
        )

        # END create ecr and push docker image ==========
        self.sync_album_lambda_role = IamRole(
            self,
            f"{component_name}-sync_album_lambda_role",
            name=f"{component_name}-sync_album_lambda_role",
            assume_role_policy=json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": {
                        "Action": "sts:AssumeRole",
                        "Principal": {
                            "Service": "lambda.amazonaws.com",
                        },
                        "Effect": "Allow",
                        "Sid": "",
                    },
                }
            ),
            managed_policy_arns=[
                "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
            ],
            inline_policy=[
                IamRoleInlinePolicy(
                    name="AllowS3Access",
                    policy=json.dumps(
                        {
                            "Version": "2012-10-17",
                            "Statement": {
                                "Action": [
                                    "s3:GetObject",
                                    "s3:PutObject",
                                ],
                                "Resource": "arn:aws:s3:::media-importer-store/*",
                                "Effect": "Allow",
                            },
                        }
                    ),
                )
            ],
        )

        self.sync_album_lambda = LambdaFunction(
            self,
            f"{env_opts.project_name}-sync_album_lambda",
            function_name=f"{env_opts.project_name}-sync_album_lambda",
            role=self.sync_album_lambda_role.arn,
            depends_on=[
                self.sync_album_lambda_role,
                self.ecr_image,
            ],
            # environment=LambdaFunctionEnvironment(
            #     variables={
            #         "CACHE_HOST": cache_host,
            #         "CACHE_PORT": cache_port,
            #         # "CACHE_AUTH": cache_auth,
            #     }
            # ),
            package_type="Image",
            image_uri=f"{repository_url}:{image_tag}",
        )

        # relate lambda to api
        self.sync_album_integration = Apigatewayv2Integration(
            self,
            f"{env_opts.project_name}-sync_album_api_integration",
            api_id=self.api.id,
            integration_type="AWS_PROXY",
            integration_method="ANY",
            integration_uri=self.sync_album_lambda.arn,
            depends_on=[
                self.sync_album_lambda,
                self.api,
            ],
        )

        # relate route to integration
        self.sync_album_route = Apigatewayv2Route(
            self,
            f"{env_opts.project_name}-sync_album_route",
            api_id=self.api.id,
            route_key="POST /sync-album",
            target=f"integrations/{self.sync_album_integration.id}",
            depends_on=[
                self.sync_album_integration,
            ],
        )

        LambdaPermission(
            self,
            f"{env_opts.project_name}-sync_album_permission",
            function_name=self.sync_album_lambda.function_name,
            action="lambda:InvokeFunction",
            principal="apigateway.amazonaws.com",
            source_arn="{}/*/*".format(self.api.execution_arn),
        )

        self.api_deployment = Apigatewayv2Deployment(
            self,
            f"{env_opts.project_name}-api-deployment",
            api_id=self.api.id,
            description="Deployment One",
            depends_on=[
                self.api,
                self.api_stage,
                self.sync_album_route,
                # self.list_albums_route,
            ],
        )
