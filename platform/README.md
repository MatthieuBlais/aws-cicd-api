# Infrastructure as code

Use deployspec and cloudformation templates to deploy your infrastructure


### Deployspec

List of cloudformation templates to deploy. To manage different environemnts, use "Env" and "Build" parameters. They will be automatically replaced by build number and branch name by the codebuild job. This allows you to create specific resources for each environment.


### Variables

Use the vars.yaml to specify your environment variables. The first key is the branch name, so that you can have different variables for different environment.