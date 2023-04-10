import os
import json
import checksumdir
from cdktf import (
    Resource,
    TerraformOutput,
)
from constructs import Construct
from imports.aws.s3_bucket import S3Bucket
from imports.aws.s3_object import S3Object
from imports.aws.s3_bucket_policy import S3BucketPolicy
from imports.aws.s3_bucket_website_configuration import (
    S3BucketWebsiteConfiguration,
    S3BucketWebsiteConfigurationErrorDocument,
    S3BucketWebsiteConfigurationIndexDocument,
)

from imports.null.resource import Resource as NullResource
from lib.EnvironmentOptions import EnvironmentOptions


class Frontend(Resource):
    def __init__(
        self, scope: Construct, id: str, env_opts: EnvironmentOptions, backend_api: str
    ):
        self.env_opts = env_opts
        self.backend_api = backend_api
        super().__init__(scope, id)

        bucket_name = f"{self.env_opts.project_name}-site"
        site_build_path = os.path.join(os.path.dirname(__file__), "site", "build")
        site_path = os.path.join(os.path.dirname(__file__), "site")

        self.site_bucket = S3Bucket(
            self,
            id,
            bucket=bucket_name,
            force_destroy=True,
        )

        self.site_config = S3BucketWebsiteConfiguration(
            self,
            "website-configuration",
            bucket=self.site_bucket.bucket,
            index_document=S3BucketWebsiteConfigurationIndexDocument(
                suffix="index.html"
            ),
            error_document=S3BucketWebsiteConfigurationErrorDocument(key="index.html"),
        )

        S3BucketPolicy(
            self,
            "site-bucket-policy",
            bucket=self.site_bucket.bucket,
            policy=json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Sid": "PublicReadGetObject",
                            "Effect": "Allow",
                            "Principal": "*",
                            "Action": ["s3:GetObject"],
                            "Resource": [f"arn:aws:s3:::{bucket_name}/*"],
                        }
                    ],
                }
            ),
            depends_on=[
                self.site_bucket,
            ],
        )

        self.build_null = NullResource(
            self,
            "build-deploy-site",
            triggers={
                "build-deploy-site": checksumdir.dirhash(site_path),
            },
            depends_on=[
                self.site_bucket,
            ],
        )

        self.build_null.add_override(
            path="provisioner.local-exec.command",
            value=f"""
                REACT_APP_GAPI_CLIENT_ID=559734907080-gf6op9372sk7mv7b5e9u02g9rv8o4b5r.apps.googleusercontent.com \
                REACT_APP_API_ENDPOINT={backend_api} \
                npm run build --prefix {site_path} && \
                aws s3 sync {site_build_path} s3://{bucket_name} --acl public-read
                """,
        )

        TerraformOutput(
            self,
            "s3-website-endpoint",
            value=self.site_config.website_endpoint,
        )
