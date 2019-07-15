import boto3
import yaml
import zipfile
import os
import zipfile
import sys
import logging
import json
import subprocess
import time

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


DEPLOYSPEC_FILENAME=os.environ["DEPLOYSPEC_FILENAME"]
REGION=os.environ["REGION"]
APPLICATION_BUCKET=os.environ["APPLICATION_BUCKET"]
PACKAGE_PREFIX=os.environ["PACKAGE_PREFIX"]



cloudformation = boto3.client('cloudformation', region_name=REGION)
s3 = boto3.client('s3', region_name=REGION)
apigateway = boto3.client("apigateway", region_name=REGION)


def read_yaml(filename):
	try:
		return yaml.load(open(filename, "r"))
	except Exception as e:
		raise

def check_exist(template_name):
	try:
		response = cloudformation.describe_stacks(
			StackName=template_name)
		return True
	except Exception as e:
		return False

def delete_stack(template_name):
	try:
		cloudformation.delete_stack(StackName=template_name)
	except Exception as e:
		raise

def update_stack(template):
	try:
		response = cloudformation.update_stack(
			StackName=template["StackName"],
			TemplateBody=open(template["TemplateName"]).read(),
			Parameters=[ {
				'ParameterKey': key,
				'ParameterValue': template["Properties"][key]
				} for key in template["Properties"].keys()],
			Capabilities=[
			    'CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM', 'CAPABILITY_AUTO_EXPAND'
			]
			)
	except Exception as e:
		print(str(e))

def create_stack(template):
	try:
		response = cloudformation.create_stack(
			StackName=template["StackName"],
			TemplateBody=open(template["TemplateName"]).read(),
			Parameters=[ {
				'ParameterKey': key,
				'ParameterValue': template["Properties"][key]
				} for key in template["Properties"].keys()],
			Capabilities=[
			    'CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM', 'CAPABILITY_AUTO_EXPAND'
			]
			)
	except Exception as e:
		raise

def upload(bucket, key, filename):
	s3.put_object(Bucket=bucket, Key=key, Body=open(filename, "rb").read())

def zipdir(path, ziph):
	zipf = zipfile.ZipFile(ziph, 'w', zipfile.ZIP_DEFLATED)
	for root, dirs, files in os.walk(path):
		for file in files:
			zipf.write(os.path.join(root, file))

def upload_api_specs(bucket, branch, build):
	upload(bucket, "api/{}/{}/specs.yaml".format(branch, build), "application/doc/specs.yaml")

def upload_lambda_code(bucket, branch, build, function_name, module):
	path = 's3://{}/lambda/api/{}/{}/{}.zip'.format(bucket, branch, build, function_name)
	process = subprocess.Popen(['/bin/bash', 'application/package.sh', module, path],
								stdout=subprocess.PIPE,
								stderr=subprocess.STDOUT)
	returncode = process.wait()
	return path

def deploy_api(api_id, stage):
	try:
		if api_id == "NONE":
			return
		response = apigateway.create_deployment(restApiId= api_id,stageName=stage)
	except Exception as e:
		raise
		
def describe_stack(stack_name):
	try:
		response = cloudformation.describe_stacks(
		    StackName=stack_name
		)
		return response["Stacks"][0]
	except Exception as e:
		raise

def wait_for_stack(stack_name, delete=False):
	stack = describe_stack(stack_name)
	status = stack["StackStatus"]
	while status == "CREATE_IN_PROGRESS":
		logging.info("-> CREATE_IN_PROGRESS")
		time.sleep(30)
		stack = describe_stack(stack_name)
		status = stack["StackStatus"]
	logging.info("=> DONE: {}".format(status))
	if delete and status in ["ROLLBACK_IN_PROGRESS", "ROLLBACK_COMPLETE"]:
		delete_stack(stack_name)
	return status

def set_environment_variables(filename, branch):
	try:
		deployspecs = open(filename, "r").read()
		var_filename = "/".join(filename.split("/")[:-1])+"/vars.yaml"
		variables = read_yaml(var_filename)
		for var in variables[branch].keys():
			deployspecs = deployspecs.replace("<{}>".format(var), variables[branch][var])
		with open(filename, "w+") as f:
			f.write(deployspecs)
	except Exception:
		raise
		logging.info("NO ENV VARIABLES")

def main(action, branch, build):
	## READ DEPLOYSPEC.YAML
	logging.info("READING DEPLOYSPEC FILE {}".format(DEPLOYSPEC_FILENAME))
	set_environment_variables(DEPLOYSPEC_FILENAME, branch)
	deployspecs = read_yaml(DEPLOYSPEC_FILENAME)

	logging.info("# TEMPLATES: {}".format(len(deployspecs)))

	## FOR LOOP
	for template in deployspecs:

		template["StackName"] = template["StackName"]+"-{}".format(branch)
		if action == "teardown":
			template["Type"] = "delete_stack"
		if "Properties" in template.keys():
			if "Env" in template["Properties"].keys():
				template["Properties"]["Env"] = branch
			if "Build" in template["Properties"].keys():
				template["Properties"]["Build"] = str(build)

		logging.info("TEMPLATE: {}".format(json.dumps(template)))

		if "SpecialStack" in template.keys() and template["Type"] != "delete_stack":
			if template["SpecialStack"] == "api":
				upload_api_specs(APPLICATION_BUCKET, branch, build)
			if template["SpecialStack"] == "lambda-api":
				print("UPLOADING LAMBDA CODE!")
				upload_lambda_code(APPLICATION_BUCKET, branch, build, template["Properties"]["FunctionName"], template["ModuleName"])

		## CHECK IF EXIST
		exist = check_exist(template["StackName"])
		logging.info("ALREADY EXIST: {}".format(exist))

		## IF EXIST AND DELETE -> DELETE
		if template["Type"] == "delete_stack" and exist:
			logging.info("DELETING...")
			delete_stack(template["StackName"])

		## IF EXIST UPDATE
		if exist and template["Type"] == "create_stack":
			logging.info("UPDATING...")
			update_stack(template)

		## IF NOT EXIST AND CREATE -> CREATE
		if not exist and template["Type"] == "create_stack":
			logging.info("CREATING...")
			create_stack(template)
			wait_for_stack(template["StackName"], delete=True)

		if "SpecialStack" in template.keys() and template["Type"] != "delete_stack":
			wait_for_stack(template["StackName"])
			if template["SpecialStack"] == "api" and "Deployment" in template.keys():
				deploy_api(template["Deployment"]["ApiName"], branch)

	## ZIP FOLDER AND UPLOAD TO S3
	logging.info("CREATING DEPLOYMENT PACKAGE...")
	zipdir(".", "package.zip")
	upload(APPLICATION_BUCKET, PACKAGE_PREFIX+branch+"/"+str(build)+"/package.zip", "package.zip")




if __name__ == '__main__':
	action = sys.argv[1]
	branch = sys.argv[2]
	build = sys.argv[3]

	logging.info("STARTING {}: BRANCH {}, BUILD {}".format(action.upper(), branch, build))

	main(action, branch, build)

	logging.info("DONE")

