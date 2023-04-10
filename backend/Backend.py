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


from imports.aws.s3_bucket import S3Bucket, S3BucketWebsite
from imports.aws.s3_object import S3Object
from imports.aws.s3_bucket_policy import S3BucketPolicy
from imports.aws.s3_bucket_website_configuration import (
    S3BucketWebsiteConfiguration,
    S3BucketWebsiteConfigurationErrorDocument,
    S3BucketWebsiteConfigurationIndexDocument,
)

from imports.aws.iam_role import IamRole, IamRoleInlinePolicy

from imports.aws.iam_policy_attachment import IamPolicyAttachment
from imports.aws.iam_role_policy_attachment import IamRolePolicyAttachment
from imports.aws.lambda_permission import LambdaPermission
from imports.aws.lambda_function import LambdaFunction, LambdaFunctionEnvironment

from imports.aws.elasticache_cluster import ElasticacheCluster

from imports.aws.apigatewayv2_api import (
    Apigatewayv2Api,
    Apigatewayv2ApiCorsConfiguration,
)

from imports.aws.lambda_function_event_invoke_config import (
    LambdaFunctionEventInvokeConfig,
)

from imports.aws.ecr_repository import EcrRepository

from imports.aws.elasticache_subnet_group import ElasticacheSubnetGroup

from imports.aws.dynamodb_table import DynamodbTable, DynamodbTableAttribute

from lib.EnvironmentOptions import EnvironmentOptions
import os
import json

# from backend.auth_api.AuthApi import AuthApi
from backend.album_api.AlbumApi import AlbumApi

from imports.vpc import Vpc


class Backend(Resource):
    def __init__(self, scope: Construct, id: str, env_opts: EnvironmentOptions):
        self.env_opts = env_opts
        super().__init__(scope, id)

        component_name = f"{self.env_opts.project_name}-backend"

        # create media store bucket
        self.bucket = S3Bucket(
            self,
            f"{self.env_opts.project_name}-store",
            bucket=f"{self.env_opts.project_name}-store",
            force_destroy=True,
        )

        # create album api
        self.album_api = AlbumApi(
            self,
            f"{env_opts.project_name}-album_api",
            env_opts=self.env_opts,
        )

        TerraformOutput(
            self,
            "output-api-url",
            value=self.album_api.api.api_endpoint,
        )
