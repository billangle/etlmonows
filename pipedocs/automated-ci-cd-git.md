# FPAC Release Process for Automated Deployments

This document describes the release process that will be utilized to support the auotmated CI/CD pipelines. 

---

# 1. Executive Summary

The FPAC CI/CD pipeline deploys all changes to the data pipelines. 

---

# 2. Automated Release Process Overview

The automated CI/CD pipeline process will implement a set of rules that enable the effective delivery of data pipeline software through the environemts. The current process does not have automated CI/CD, thus the rules for code deployment have been ad-hoc agreements. This section will provide an overview of the auotmation and the rules that enable this automation. 

## 2.1 Tools and Systems Overview
The data pipeline software is maintained in a series of BitBucket repositories. There are approximately thirty repositories used for mainatining the software used by FPAC. The data pipelines are scheduled and run as batch jobs from Jenkins. There are currently three Jenkins environments, development (DEV), certification (CERT) and production (PROD). The scheduling of the jobs is implemented by manually changing the schedule in Jeknins. The master schedule is maintained as a Confluence document. There is no release process for the changes to the schedule and currently the schedule is not part of source code control.

## 2.2 CI/CD Process Automation
The CI/CD process automation has the following features:

- Deployment is via AWS CDK using an auotmated deployment pieline triggered from BitBucket
- Jenkins will be used to deploy software to one of four environments (DEV,CERT,STAGING, PROD)
- The existing CERT Jenkins system will support both CERT and STAGING
- The AWS CDK implementation is idempotent - ensuring that the AWS CDK command can be run as often as required, without causing the deployment pipeline to break
- The promotion of a release to PROD will be a manual step that is prepared using automation, but must be manually triggered
- Other steps are prepared via automation and automatically triggered
- Manual triggering can be added to any step, as required

## 2.3 GIT Branching 

Automated CI/CD pipelines require the implementation of a well understood branching strategy. This enables rules to be triggered based on the merge, commit or tagging of a particular branch or style of branch. the automation will be impacted by the strict adherance to these branching rules.

### 2.3.1 main branch release overview with tags

The main branch should contain the release to production. This is includes a release target that is on CERT. The release is deployed utiling a GIT tag. The tagging process represents a series of merge requests (MRs), which have been pushed to main. The tag allows for a specific set of changes to be deployed to both PROD and STAGE. Futher, the tag provides a specific point that represents a release. This gives the team the ability to roll-back to a tag. The tagging process also allows active development on the next release even while the production tag is being certified.

### 2.3.2 dev branch process on DEV enironment

The dev branch will contain the current state of development. It is a series of MRs (merge requests), from work done for features that are defined a Jira tickets. Each feature should be a branch from dev with the name of the Jira ticket.

- Example for a ticket called DDAA-2400
- Create a branch called DDAA-2400 from dev branch
- Changes made to DDAA-2400 based on the Jira ticket
- Commit changes to DDAA-2400
- Once changes are complete create an MR for DDAA-2400 to merge to dev
- The MR is reviewed and once approved is merged to dev
- The dev branch changes are automatically pushed to the DEV environment once the MR is approved

### 2.3.3 dev branch changes to CERT environment





### 2.2.1 CI/CD Process Auotmation Steps

1. Code changes to DEV environem
2. 


---
# 3. GIT Branching Strategy

---
# 4. Flow through environments

---
# 5. Release candidate and hot-fixes

---
# 6. Summary