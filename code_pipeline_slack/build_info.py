import json
import logging
import os

logger = logging.getLogger()

LOGLEVEL = os.environ.get("LOGLEVEL", "WARNING").upper()
logging.basicConfig(level=LOGLEVEL)


class CodeBuildInfo(object):
    def __init__(self, pipeline, build_id):
        self.pipeline = pipeline
        self.build_id = build_id

    @staticmethod
    def from_event(event):
        pipeline = event["detail"]["additional-information"]["initiator"][13:]
        bid = event["detail"]["build-id"]

        return CodeBuildInfo(pipeline, bid)


class BuildNotification(object):
    def __init__(self, build_info):
        self.build_info = build_info


class BuildInfo(object):
    def __init__(self, execution_id, pipeline, status=None):
        self.status = status
        self.revisionInfo = None
        self.execution_id = execution_id
        self.pipeline = pipeline

    def has_revision_info(self):
        return len(self.revisionInfo) > 0

    @staticmethod
    def pull_phase_info(event):
        info = event["detail"]["additional-information"]
        return info.get("phases")

    @staticmethod
    def from_event(event):
        if event["source"] == "aws.codepipeline":
            detail = event["detail"]
            return BuildInfo(detail["execution-id"], detail["pipeline"])
        if event["source"] == "aws.codebuild":
            logger.debug(json.dumps(event, indent=2))
            ph = BuildInfo.pull_phase_info(event)
            logger.debug(json.dumps(ph, indent=2))

        return None

    @staticmethod
    def from_message(event):
        fields = event["attachments"][0]["fields"]

        execution_id = fields[0]["value"]
        status = fields[1]["value"]
        pipeline = fields[1]["title"]

        return BuildInfo(execution_id, pipeline, status)
