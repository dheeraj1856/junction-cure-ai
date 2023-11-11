#!/usr/bin/env bash

#=========================================================================
# This script shows how to build the Docker image and push it to ECR to be ready for use
# by SageMaker.

#=========================================================================
# usage:
# build_and_push.sh



org="labradoodle-ai"
app_name="llm-api"
image=${org}-${app_name}

# GIVE LAMBDA PERMISSIONS
LAMBDA_FUNCTION_NAME=${image}
POLICY_NAME=${image}-policy
POLICY_FILE="lambda-policy.json"


parse_env_to_json() {
  echo '{'
  while IFS= read -r line || [ -n "$line" ]; do
    if [[ $line != \#* && $line == *'='* ]]; then
      key=$(echo $line | cut -f1 -d'=')
      value=$(echo $line | cut -f2 -d'=')
      echo "  \"$key\": \"$value\","
    fi
  done < .env
  echo '}'
}
ENV_VARIABLES_JSON=$(parse_env_to_json | sed '$ s/,$//')

if [ "$image" == "" ]
then
    echo "Usage: $0 <image-name>"
    exit 1
fi

echo "Generating container for " $image

# Get the account number associated with the current IAM credentials
account=$(aws sts get-caller-identity --query Account --output text)

if [ $? -ne 0 ]
then
    exit 255
fi


# Get the region defined in the current configuration (default to us-west-2 if none defined)
region=$(aws configure get region)
region=${region:-us-east-1}


fullname="${account}.dkr.ecr.${region}.amazonaws.com/${image}:latest"
echo $fullname

# If the repository doesn't exist in ECR, create it.

aws ecr describe-repositories --repository-names "${image}" > /dev/null 2>&1

if [ $? -ne 0 ]
then
    echo "Doesn't exist"
    aws ecr create-repository --repository-name "${image}" > /dev/null
fi

# Get the login command from ECR and execute it directly
aws ecr get-login-password --region "${region}" | docker login --username AWS --password-stdin "${account}".dkr.ecr."${region}".amazonaws.com

# Build the docker image locally with the image name and then push it to ECR
# with the full name.

echo "===================================================================================================="

docker build  -t ${image} . --build-arg REGION=${region} --platform=linux/amd64
docker tag ${image} ${fullname}

docker push ${fullname}


# CHECK IF LAMBDA FUNCTION EXISTS, IF SO, DELETE IT
aws lambda get-function --function-name ${image} > /dev/null 2>&1

if [ $? -eq 0 ]; then
  # If exists, update
  aws lambda update-function-code --function-name ${LAMBDA_FUNCTION_NAME} --image-uri ${fullname}
  aws lambda update-function-configuration --function-name ${LAMBDA_FUNCTION_NAME} --environment "Variables=$ENV_VARIABLES_JSON"
else
  # If not, create function
  aws lambda create-function \
      --function-name ${image} \
      --package-type Image \
      --code ImageUri=${fullname} \
      --role arn:aws:iam::${account}:role/junction-2023-llm-api \
      --timeout 900 \
      --memory-size 512 \
      --environment "Variables=$ENV_VARIABLES_JSON"

  aws lambda add-permission \
      --function-name ${image} \
      --statement-id AllowInvokeFunctionUrl \
      --action "lambda:InvokeFunctionUrl" \
      --function-url-auth-type NONE \
      --principal "*" 

  # Get the Lambda function's execution role name
  EXECUTION_ROLE_NAME=$(aws lambda get-function --function-name "${LAMBDA_FUNCTION_NAME}" --query 'Configuration.Role' --output text | awk -F'/' '{print $2}')

  # Get the Amazon Resource Name (ARN) of the existing policy
  EXISTING_POLICY_ARN=$(aws iam list-policies --scope Local --query "Policies[?PolicyName=='${POLICY_NAME}'].Arn" --output text)

  # If the policy exists, detach it from the role and delete it
  if [ ! -z "$EXISTING_POLICY_ARN" ]; then
      aws iam detach-role-policy --role-name "${EXECUTION_ROLE_NAME}" --policy-arn "${EXISTING_POLICY_ARN}"
      aws iam delete-policy --policy-arn "${EXISTING_POLICY_ARN}"
  fi

  # Create the IAM policy from the JSON file
  aws iam create-policy --policy-name "${POLICY_NAME}" --policy-document file://"${POLICY_FILE}"

  # Get the Amazon Resource Name (ARN) of the new policy
  POLICY_ARN=$(aws iam list-policies --scope Local --query "Policies[?PolicyName=='${POLICY_NAME}'].Arn" --output text)

  if [ -z "$POLICY_ARN" ]; then
      echo "Failed to create policy or get policy ARN. Please check the policy name and file."
  else
      if [ -z "$EXECUTION_ROLE_NAME" ]; then
          echo "Failed to get the execution role for the Lambda function. Please check the function name."
      else
          # Attach the policy to the Lambda function's execution role
          aws iam attach-role-policy --role-name "${EXECUTION_ROLE_NAME}" --policy-arn "${POLICY_ARN}"
          echo "Policy ${POLICY_NAME} has been attached to the execution role of Lambda function ${LAMBDA_FUNCTION_NAME}."
      fi
  fi


  # Rename policy if not already named
  policy_file_replace_after="aws\/lambda"
  policy_image_name="aws\/lambda\/${image}:*\""
  sed -i "s/${policy_file_replace_after}.*/${policy_image_name}/" lambda-policy.json
fi

  # CHECK IF LAMBDA FUNCTION URL EXISTS
aws lambda get-function-url-config --function-name ${image} > /dev/null 2>&1

if [ $? -eq 0 ]; then
  echo "Lambda function URL '${image}' exists."
else
  # If it does not exist, create it
  echo "Lambda function URL '${image}' does not exist. Creating..."
  aws lambda create-function-url-config \
      --function-name ${image} \
      --auth-type NONE
fi