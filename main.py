#!/usr/bin/env python
import os
from constructs import Construct
from cdktf import App, TerraformStack
from constructs import Construct
from imports.aws.provider import AwsProvider
from imports.time.provider import TimeProvider
from lib.EnvironmentOptions import EnvironmentOptions

from frontend.Frontend import Frontend
from backend.Backend import Backend

env_opts = EnvironmentOptions(
    project_name="media-importer",
    region=os.environ["REGION"],
    env=os.environ["ENV"],
    account_id=os.environ["ACCOUNT_ID"],
    key_pair_name=os.environ["KEY_PAIR_NAME"],
)
from imports.null.provider import NullProvider


class MyStack(TerraformStack):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)

        AwsProvider(self, "aws-provider", region=env_opts.region)
        NullProvider(self, "null-provider")
        TimeProvider(self, "time-provider")

        self.backend = Backend(
            self,
            f"{env_opts.project_name}-backend",
            env_opts=env_opts,
        )

        self.frontend = Frontend(
            self,
            f"{env_opts.project_name}-frontend",
            env_opts=env_opts,
            backend_api=self.backend.album_api.api.api_endpoint,
        )

        # Analytics(
        #     self,
        #     "analytics",
        #     env_opts=env_opts,
        # )


app = App()
MyStack(app, "media-importer")

app.synth()
