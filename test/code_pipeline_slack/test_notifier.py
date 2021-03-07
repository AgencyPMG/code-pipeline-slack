from doubles import allow

from code_pipeline_slack.notifier import Notifier
from code_pipeline_slack.slack_helper import SlackHelper

import boto3
import json


def get_event(name):
    with open(f"./test/code_pipeline_slack/events/{name}.json") as json_file:
        return json.load(json_file)


pipeline_execution_state = {
    "pipelineExecution": {
        "pipelineName": "01234567-EXAMPLE",
        "pipelineVersion": 4,
        "pipelineExecutionId": "05dfe8b6-1bf6-4ac2-906c-0ae37c7cbbb8",
        "status": "InProgress",
        "artifactRevisions": [
            {
                "name": "SourceArtifact",
                "revisionId": "e2353574a4bde7f29bdbc912cf6d3685e3a2c041",
                "revisionSummary": "Merge pull request #1413 from cleverly-ai/allow-interaction-reclassification-via-flag\n\nAllow interaction reclassification via a flag in integration",
                "revisionUrl": "https://github.com/cleverly-ai/sample-project/commit/e2353574a4bde7f29bdbc912cf6d3685e3a2c041",
            }
        ],
    }
}

pipeline_state = {
    "pipelineName": "01234567-EXAMPLE",
    "pipelineVersion": 4,
    "stageStates": [
        {
            "stageName": "Source",
            "inboundTransitionState": {"enabled": True},
            "actionStates": [
                {
                    "actionName": "Source",
                    "currentRevision": {
                        "revisionId": "e2353574a4bde7f29bdbc912cf6d3685e3a2c041"
                    },
                    "latestExecution": {
                        "actionExecutionId": "eee42ad8-e955-4789-9e07-4fdb20de418c",
                        "status": "Succeeded",
                        "summary": "Merge pull request #1413 from cleverly-ai/allow-interaction-reclassification-via-flag\n\nAllow interaction reclassification via a flag in integration",
                        "lastStatusChange": "2021-03-05T20:04:56.083000+00:00",
                        "externalExecutionId": "e2353574a4bde7f29bdbc912cf6d3685e3a2c041",
                    },
                    "entityUrl": "https://github.com/cleverly-ai/sample-project/tree/master",
                    "revisionUrl": "https://github.com/cleverly-ai/sample-project/commit/e2353574a4bde7f29bdbc912cf6d3685e3a2c041",
                }
            ],
            "latestExecution": {
                "pipelineExecutionId": "05dfe8b6-1bf6-4ac2-906c-0ae37c7cbbb8",
                "status": "Succeeded",
            },
        },
        {
            "stageName": "Build",
            "inboundTransitionState": {"enabled": True},
            "actionStates": [
                {
                    "actionName": "Build",
                    "latestExecution": {
                        "actionExecutionId": "ce4aae0e-93d8-4a11-be06-ca48ae8659d9",
                        "status": "Succeeded",
                        "lastStatusChange": "2021-03-05T20:16:16.725000+00:00",
                        "externalExecutionId": "sample-project-build-and-deploy:a87fcecb-35e5-4c1d-9789-cf58241b7d6d",
                        "externalExecutionUrl": "https://console.aws.amazon.com/codebuild/home?region=eu-west-1#/builds/sample-project-build-and-deploy:a87fcecb-35e5-4c1d-9789-cf58241b7d6d/view/new",
                    },
                    "entityUrl": "https://console.aws.amazon.com/codebuild/home?region=eu-west-1#/projects/sample-project-build-and-deploy/view",
                }
            ],
            "latestExecution": {
                "pipelineExecutionId": "05dfe8b6-1bf6-4ac2-906c-0ae37c7cbbb8",
                "status": "Succeeded",
            },
        },
    ],
    "created": "2019-04-06T23:56:38.387000+01:00",
    "updated": "2019-08-22T22:53:24.708000+01:00",
}


slack_message = {
    "type": "message",
    "subtype": "bot_message",
    "text": "",
    "ts": "1615145805.000300",
    "username": "CodePipeline",
    "icons": {
        "emoji": ":rocket:",
        "image_64": "https://a.slack-edge.com/production-standard-emoji-assets/13.0/apple-large/1f680.png",
    },
    "bot_id": "BLBNZ8JLD",
    "attachments": [
        {
            "footer": "05dfe8b6-1bf6-4ac2-906c-0ae37c7cbbb8",
            "id": 1,
            "color": "2eb886",
            "fields": [
                {
                    "title": "ml-models-pipeline",
                    "value": "SUCCEEDED",
                    "short": True,
                },
                {
                    "title": "Stages",
                    "value": ":white_check_mark: Source\t:white_check_mark: Build",
                    "short": True,
                },
                {
                    "title": "Build",
                    "value": ":white_check_mark: QUEUED (1.0)\n:white_check_mark: PROVISIONING (33.0)\n:white_check_mark: INSTALL (160.0)\n:white_check_mark: POST_BUILD (6.0)\n:white_check_mark: FINALIZING (2.0)",
                    "short": False,
                },
            ],
            "actions": [
                {
                    "id": "1",
                    "text": "Build dashboard",
                    "type": "button",
                    "style": "",
                    "url": "https://console.aws.amazon.com/codebuild/home?region=eu-west-1#/builds/ml-model-manifests-build-and-deploy:041941f3-133d-433c-9de8-341f2316e97b/view/new",
                }
            ],
            "fallback": "[no preview available]",
        }
    ],
    "edited": {"user": "BLBNZ8JLD", "ts": "1615146026.000000"},
}


def test_codepipeline_event(mocker):
    aws_client = boto3.client("codepipeline")
    slack_client = SlackHelper(
        "xoxp-xxxxxxxxx-xxxx", "dev", "public_channel", "codepipeline", ":robot:"
    )

    allow(aws_client).get_pipeline_execution.and_return(
        pipeline_execution_state)
    allow(aws_client).get_pipeline_state.and_return(pipeline_state)

    allow(slack_client).find_message_for_build
    allow(slack_client).post_build_message

    event = get_event("event_pipeline")
    notifier = Notifier(aws_client, slack_client)
    notifier.process(event)


def test_codebuild_event(mocker):
    aws_client = boto3.client("codepipeline")
    slack_client = SlackHelper(
        "xoxp-xxxxxxxxx-xxxx", "dev", "public_channel", "codepipeline", ":robot:"
    )

    allow(aws_client).get_pipeline_execution.and_return(
        pipeline_execution_state)
    allow(aws_client).get_pipeline_state.and_return(pipeline_state)

    allow(slack_client).find_message_for_build
    allow(slack_client).post_build_message

    event = get_event("event_codebuild")
    notifier = Notifier(aws_client, slack_client)
    notifier.process(event)
