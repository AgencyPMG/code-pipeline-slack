# -*- coding: utf-8 -*-

import boto3
import logging
import os

from code_pipeline_slack.build_info import BuildInfo, CodeBuildInfo
from code_pipeline_slack.message_builder import MessageBuilder
from code_pipeline_slack.slack_helper import SlackHelper


logger = logging.getLogger()

LOGLEVEL = os.environ.get("LOGLEVEL", "WARNING").upper()
logging.basicConfig(level=LOGLEVEL)

SLACK_TOKEN = os.getenv("SLACK_TOKEN")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "builds2")
SLACK_CHANNEL_TYPE = os.getenv("SLACK_CHANNEL_TYPE", "public_channel")
SLACK_BOT_NAME = os.getenv("SLACK_BOT_NAME", "BuildBot")
SLACK_BOT_ICON = os.getenv("SLACK_BOT_ICON", ":robot_face:")


class Notifier:
    def __init__(self, aws_client, slack_client):
        self.aws_client = aws_client
        self.slack_client = slack_client

    def find_revision_info(self, info):
        r = self.aws_client.get_pipeline_execution(
            pipelineName=info.pipeline, pipelineExecutionId=info.execution_id
        )["pipelineExecution"]

        revs = r.get("artifactRevisions", [])

        if len(revs) > 0:
            return revs[0]

        return None

    def pipeline_from_build(self, code_build_info):
        print(vars(code_build_info))
        r = self.aws_client.get_pipeline_state(name=code_build_info.pipeline)

        for s in r["stageStates"]:
            for a in s["actionStates"]:
                execution_id = a.get("latestExecution", {}).get("externalExecutionId")

                if execution_id and code_build_info.build_id.endswith(execution_id):
                    pe = s["latestExecution"]["pipelineExecutionId"]
                    return s["stageName"], pe, a

        return None, None, None

    def process_code_pipeline(self, event):
        if "execution-id" not in event["detail"]:
            logger.debug("Skipping due to no executionId")
            return

        build_info = BuildInfo.from_event(event)
        existing_msg = self.slack_client.find_message_for_build(build_info.execution_id)

        builder = MessageBuilder(build_info, existing_msg)
        builder.update_pipeline_event(event)

        if builder.needs_revision_info():
            revision = self.find_revision_info(build_info)
            builder.attach_revision_info(revision)

        self.slack_client.post_build_message(
            builder.message(), builder.message_id, build_info.execution_id
        )

    def process_code_build(self, event):
        if "additional-information" not in event["detail"]:
            logger.debug("Skipping due to no additional-information")
            return

        cbi = CodeBuildInfo.from_event(event)

        logger.debug(vars(cbi))

        (stage, pid, actionStates) = self.pipeline_from_build(cbi)

        logger.debug(stage, pid, actionStates)

        if not pid:
            return

        build_info = BuildInfo(pid, cbi.pipeline)

        existing_msg = self.slack_client.find_message_for_build(build_info.execution_id)

        builder = MessageBuilder(build_info, existing_msg)

        if "phases" in event["detail"]["additional-information"]:
            phases = event["detail"]["additional-information"]["phases"]
            builder.update_build_stage_info(stage, phases, actionStates)

        self.slack_client.post_build_message(
            builder.message(), builder.message_id, build_info.execution_id
        )

    def process(self, event):
        if event["source"] == "aws.codepipeline":
            self.process_code_pipeline(event)
        if event["source"] == "aws.codebuild":
            self.process_code_build(event)


def run(event, context):
    aws_client = boto3.client("codepipeline")
    slack_client = SlackHelper(
        SLACK_TOKEN, SLACK_CHANNEL, SLACK_CHANNEL_TYPE, SLACK_BOT_NAME, SLACK_BOT_ICON
    )

    notifier = Notifier(aws_client, slack_client)
    notifier.process(event)
