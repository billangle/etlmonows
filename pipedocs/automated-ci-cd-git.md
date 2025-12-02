# FPAC Release Process for Automated Deployments

This document describes the release process that will be utilized to support the auotmated CI/CD pipelines. 

---

# 1. Executive Summary

The FPAC CI/CD pipeline deploys all changes to the data pipelines. 

---

# 2. Automated Release Process Overview

The automated CI/CD pipeline process will implement a set of rules that enable the effective delivery of data pipeline software through the environemts. The current process does not have automated CI/CD, thus the rules for code deployment have been ad-hoc agreements. This section will provide an overview of the auotmation and the rules that enable this automation. 

## 2.1 Tools and Systems Overview

### 2.1.1 Current State

The data pipeline software is maintained in a series of BitBucket repositories. There are approximately thirty repositories used for mainatining the software used by FPAC. The data pipelines are scheduled and run as batch jobs from Jenkins. There are currently three Jenkins environments, development (DEV), certification (CERT) and production (PROD). The scheduling of the jobs is implemented by manually changing the schedule in Jeknins. The master schedule is maintained as a Confluence document. There is no release process for the changes to the schedule and currently the schedule is not part of source code control.

### 2.1.2 Future State Code Repository

The data pipeline software will be migrated to a BitBucket mono-repo, which will have a directory for each project. This solution will support sharing common CDK constructs across data pipelines. It will also support sharing common Lambda layers across projects. These layers include both binary third-party builds as well as common FPAC code, shared across pipelines. The goal of this is to provide the CI/CD automation from a single repository, rather than having the automation replicated across many repositories.

### 2.1.3 Future State Scheduling

The schedule of data pipeline jobs is critical to the success of these data pipelines. There will be an application that will display and maintain the schedule. Changes made in this application will directly impect the scheduling software, whether that is Jenkins or other tools. The goal is that this scheduling applcation will have the ability to display what is going to run, what is running and what has run. Within this display, the user should be able to obtain the status and any relevant messages. The deployment of this applcation code, will follow the GIT branching and CI/CD process, defined in this document.


## 2.2 CI/CD Process Automation
The CI/CD process automation has the following features:

- Deployment is via AWS CDK using an automated deployment pipeline triggered from BitBucket
- Jenkins will be used to deploy software to one of four environments (DEV,CERT,STAGING, PROD)
- The existing CERT Jenkins system will support both CERT and STAGING
- The AWS CDK implementation is idempotent - ensuring that the AWS CDK command can be run as often as required, without causing the deployment pipeline to break
- The promotion of a release to PROD will be a manual step that is prepared using automation, but must be manually triggered to deploy to the PROD environment
- Other steps are prepared via automation and automatically triggered
- Manual triggering of a deployment, can be added to any step, as required

# 3. GIT Branching and CI/CD automation

Automated CI/CD pipelines require the implementation of a well understood branching strategy. This enables rules to be triggered based on the merge, commit or tagging of a particular branch or style of branch. the automation will be impacted by the strict adherance to these branching rules.

### 3.0.1 CERT and STAGE environments

During the transition from the manual process to the automated process, the STAGE environment will be the CERT environment for code that is moving through the automated process. Once the transition is complete, the STAGE environment will become the pre-production staging environment for a release. This means that some number of end-users will be able to preview the release in the STAGE environment. After a release the STAGE environment will become the place to test hot-fixes for a release, since CERT will likely have changes approved for the next release. In the final implementation - CERT will be deployed from the dev branch and STAGE will be deployed from the main branch. This is the most significant difference between these evironments. 

### 3.0.2 main branch release overview with tags

The main branch should contain the release to production. This is includes a release target that is on STAGE. The release is deployed utilizing a GIT tag. The tagging process represents a series of pull requests (PRs), which have been pushed to main. The tag allows for a specific set of changes to be deployed to PROD. Futher, the tag provides a specific point that represents a release. This gives the team the ability to roll-back to a tag. The tagging process also allows active development on the next release even while the production tag is being certified.

### 3.0.3.1 branch protection

The main and dev branches are protected, which means that engineers cannot commit code directly to these branches. Changes must be made on feature branches, which are merged to protected branches via pull requests (PRs).

### 3.0.3.2 branch protection exceptions

The exception to branch protection is that the administrator can make commits directly to protected branches. These are done to:

- Ensure that main and dev are the same immediately after a release to PROD
- Correct conflicts that span multiple feature branches
- Changes for automated pipeline definition and pipeline testing

## 3.1 dev branch process on DEV enironment

The dev branch will contain the current state of development. It is a series of PRs (pull requests), from work done for features that are defined a Jira tickets. Each feature should be a branch from dev with the name of the Jira ticket. The dev environment will be a series of chnages related to commits made on these feature branches, directly correlated to Jira tickets. The CERT environment will have all of the approved PRs that have been merged into the dev branch. These actions will be automated via the CI/CD pipeline. 

- Jira ticket example called DDAA-2400
- Create a branch called DDAA-2400 from the dev branch
- Changes made to DDAA-2400 based on the Jira ticket
- Commit changes to DDAA-2400
- Updates are automatically pushed to DEV environment via CI/CD pipeline
- All code quality and security scans must be passed for each commit, otherwise the deployment to the DEV environment will fail
- It is at this point that any and all automated scans are run and these must be passed for every commit

## 3.2 dev branch process on CERT environment

The process to promote work to the CERT environment. The feature branch will utilize a PR to merge changes to the dev branch. The PR process will involve a manual code review, to ensure that the code should be promoted to the CERT environment. Once the PR is approved, the CI/CD process will automatically deploy the updated dev branch to the CERT environment.

- Data Engineer or Lead creates a PR for DDAA-2400 to merge to dev
- The PR is reviewed and any changes are resolved
- Any merge conflicts must be corrected
- The PR is approved and feature branch is merged to dev branch
- The dev branch changes are automatically pushed to the CERT environment once the PR is approved
- Automated scans are not run, to ensure that the PR is successfully merged
- The changes are available for QA testing
- The feature branch DDAA-2400 is deleted after the successful merge
- Changes based on QA testing should be done on a new feature branch - starting the process back to section 2.3.2

## 3.3 dev branch to main deployed to STAGE environment

Based on criteria external to this process, a PR will be created to merge the current state of dev to main. The STAGE environment will always contain the most current stage of the main branch.

- Once the PR from dev to main is approved, the updated main branch is automatically deployed to STAGE
- The CI/CD deployment automation is trigged by the PR from dev to main
- User testing can cause changes to flow back through the process, so that multiple release candidates can exist

## 3.4 main branch deployed to PROD environment

This tag name should follow a common release naming convetion. FPAC appears to be using a date-based versioning solution, so the tag should have the convention [PI]YYYY.MM.STAGE[-N], where -N is the incremental number of the next tag for this year and month combination, starting with 1. This will represent the relase candidate on the STAGE environment for this month and year. 

- Tagging is a manual process after the successful merge from dev to main 
- Tag is created on the main branch
- *EXAMPLE: First merge to main deployed to STAGE for 2026 in January would be tagged as PI2026.01.STAGE.01*
- The STAGE tags are for reference, no automation is triggered on a STAGE tag
- Each STAGE tag becomes a release candidate



### 2.2.1 CI/CD Process Automation Steps

1. Code changes to DEV environem
2. 


---


---
# 4. Flow through environments

---
# 5. Release candidate and hot-fixes

---
# 6. Summary