#!/bin/bash -eu

# package.sh
# Installs dependendies into target folder and create lambda zip package
#

PROJECT_NAME=code-pipeline-slack
S3_BUCKET="cleverly-cloudformation-artifacts-zai5koow"
TARGET_DIRECTORY=./target
ZIP_FILE=./lambda.zip

echo "Installing dependencies into ${TARGET_DIRECTORY} ... "
pipenv run pip install -r <(pipenv lock -r) --target ${TARGET_DIRECTORY}
cp ./src/* ${TARGET_DIRECTORY}
rm -f ${ZIP_FILE}

pushd ${TARGET_DIRECTORY}
zip -r ../${ZIP_FILE} .
popd

rm -rf ${TARGET_DIRECTORY}

# echo "Uploading to s3://${S3_BUCKET} ${PROJECT_NAME}"
aws cloudformation package --template-file ./template.yml --s3-bucket ${S3_BUCKET} --s3-prefix ${PROJECT_NAME} --output-template-file packaged-template.yml
aws s3 cp ./packaged-template.yml s3://${S3_BUCKET}/${PROJECT_NAME}/template.yml

# aws cloudformation deploy --profile=${AWS_PROFILE} --region=${AWS_REGION} --template-file packaged-template.yml --stack-name ${PROJECT_NAME} --capabilities CAPABILITY_IAM
