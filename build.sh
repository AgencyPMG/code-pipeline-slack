#!/bin/bash -eu
# install dependendies into target folder and create lambda zip package

PROJECT_NAME=code-pipeline-slack-dev
S3_BUCKET="cleverly-cloudformation-artifacts-zai5koow"
TARGET_DIRECTORY=./target
ZIP_FILE=./lambda.zip

echo "Installing dependencies into ${TARGET_DIRECTORY} ... "
poetry run pip install -r <(poetry export -f requirements.txt) --target "${TARGET_DIRECTORY}"

find ./code_pipeline_slack -type f -iname "*.py" -print0 | xargs -0 -I{} cp {} "${TARGET_DIRECTORY}"

[ -f "${ZIP_FILE}" ] && rm -f "${ZIP_FILE}"

pushd "${TARGET_DIRECTORY}"
zip -r ../"${ZIP_FILE}" .
popd

[ -d "${TARGET_DIRECTORY}" ] && rm -rf "${TARGET_DIRECTORY}"

echo "Uploading to s3://${S3_BUCKET}/${PROJECT_NAME}"
aws cloudformation package --template-file ./template.yml --s3-bucket ${S3_BUCKET} --s3-prefix ${PROJECT_NAME} --output-template-file packaged-template.yml
aws s3 cp ./packaged-template.yml s3://${S3_BUCKET}/${PROJECT_NAME}/template.yml

# aws cloudformation deploy --profile=${AWS_PROFILE} --region=${AWS_REGION} --template-file packaged-template.yml --stack-name ${PROJECT_NAME} --capabilities CAPABILITY_IAM
