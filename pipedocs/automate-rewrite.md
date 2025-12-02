# FPAC Release Process for Automated Deployments

This document describes the standardized release process that will be utilized to support automated CI/CD pipelines and eliminate reliance on manual deployment practices.

---

# 1. Executive Summary

FPAC is transitioning from a predominantly manual software deployment model to a fully automated CI/CD release process designed to support consistent, traceable, and repeatable deployments of data pipeline software. This modernization introduces structured Git branching rules, enforced pull-request workflows, automated quality and security checks, and controlled promotion of code across four environments—DEV, CERT, STAGE, and PROD.

In the new model, all development work begins on short-lived feature branches tied to Jira tickets. These changes are validated through automated scans and deployed to the DEV environment on every commit. Approved changes are merged into the `dev` branch, which drives deployments to CERT, where integration testing and certification occur. Once a collection of features is ready for release, the `dev` branch is merged into `main`, triggering deployment to STAGE for user acceptance testing. Production releases are promoted exclusively through Git tags applied to the `main` branch, ensuring immutable release artifacts, auditability, and rollback capability.

This approach eliminates ad-hoc deployment practices and introduces governance, transparency, and automation into every stage of the deployment process. The result is a standardized and scalable release mechanism that reduces risk, accelerates delivery cycles, and aligns FPAC’s development and operations teams around a common, enforceable process.

---

# 2. Automated Release Process Overview

The automated CI/CD release process introduces standardized rules and controls that govern how code progresses through FPAC environments. Historically, deployments have relied on informal, manual steps and undocumented agreements. The new process replaces that variability with a predictable, rules-driven model that ensures code changes are validated, tested, and deployed consistently.

The CI/CD pipeline coordinates version control, infrastructure management, deployment automation, and scheduling. Each component plays a specific role in enabling reliable releases and ensuring that changes move through environments in a traceable, auditable, and repeatable manner.

## 2.1 Tools and Systems Overview

### 2.1.1 Current State

FPAC's data pipeline software is maintained across more than thirty independent BitBucket repositories. Batch jobs are scheduled and executed using Jenkins instances for DEV, CERT, and PROD environments. Deployment schedules are manually updated in Jenkins, with the authoritative version stored in a static Confluence document. There is no formal release control for schedule changes, and scheduling configurations are not under source code management—making governance, traceability, and rollback challenging.

### 2.1.2 Future State Code Repository

All FPAC pipeline code will be consolidated into a single BitBucket mono-repo. Each project will exist in a defined directory structure that supports:

- Reuse of AWS CDK constructs across pipelines  
- Shared Lambda layers for third-party binaries and common FPAC libraries  
- Centralized CI/CD automation for deployment, governance, and testing

This shift eliminates redundant configuration, simplifies maintenance, and enforces process consistency across all data pipelines.

### 2.1.3 Future State Scheduling

The scheduling of batch jobs will be fully automated and controlled by an application purpose-built to manage and display pipeline execution plans. Users will be able to view what will run, what is running, and what has completed, along with statuses and execution messages. Updates made in this application will directly modify the underlying scheduling system—eliminating manual edits and ensuring all schedule changes are version-controlled and deployed using the same CI/CD pipeline defined in this document.

## 2.2 CI/CD Process Automation

The automated CI/CD process includes the following key capabilities:

- Deployment is performed using AWS CDK and triggered from BitBucket commits, pull requests, or tags
- Jenkins orchestrates deployments across the four environments: **DEV**, **CERT**, **STAGE**, and **PROD**
- A single CERT Jenkins system will support both CERT and STAGE deployments during transition
- AWS CDK provides idempotent deployment behavior, allowing repeat execution without breaking environments
- Promotion to PROD is a controlled manual step initiated after automation prepares the release
- Earlier deployment steps are fully automated and may include optional manual triggers when required

This automation framework ensures repeatable deployments, minimizes human error, and aligns FPAC software delivery with modern DevOps principles.

---

# 3. GIT Branching and CI/CD Automation

Automated CI/CD pipelines require the implementation of a well-understood branching strategy. Branch naming conventions and protected branch rules enable the automation system to execute deployment logic based on merges, commits, and tags.

## 3.0.1 CERT and STAGE Environments

During the transition period, the STAGE environment will serve temporarily as CERT for code moving through automated processes. After the transition:

- **CERT** is deployed from the `dev` branch
- **STAGE** is deployed from the `main` branch

CERT represents the certified state of development for the next release, while STAGE provides a pre-production validation area. After a release, STAGE becomes the environment used for hotfix validation, as CERT moves forward with changes for the next version.

## 3.0.2 main Branch Release Overview with Tags

The `main` branch contains production-ready code and acts as the release branch. Releases are deployed using Git tags that represent specific pull requests merged into `main`. Tags serve as immutable checkpoints, enabling rollback and supporting simultaneous development of future releases.

## 3.0.3.1 Branch Protection

The `main` and `dev` branches are protected. Engineers cannot commit directly to either branch—changes must be introduced through feature branches and merged via pull requests.

## 3.0.3.2 Branch Protection Exceptions

Administrators may directly commit to protected branches for specific purposes:

- Ensuring `main` and `dev` match immediately after a production release
- Resolving complex merge conflicts across multiple feature branches
- Updating automated pipeline definitions

---

# 4. Branching Strategy Identification

This documentation describes a **GitFlow-inspired branching model** adapted to support automated CI/CD pipelines and environment-based deployments. While not a full GitFlow implementation, it adopts GitFlow’s essential branching patterns and enhances them with environment-driven promotion rules and tag-based production releases.

Key characteristics include:

- **Long-lived protected branches:** `dev` (integration) and `main` (production)
- **Short-lived feature branches:** Created from `dev`, named after Jira tickets, merged via PR, then deleted
- **Tag-driven production releases:** Tags on `main` define immutable release artifacts and support rollback

This model is best described as:

**A Modified GitFlow (GitFlow-lite) branching strategy optimized for environment-based deployments and tag-governed production releases.**

---

# 5. Why This Strategy Resembles GitFlow

- `main` ≈ GitFlow `master`  
- `dev` ≈ GitFlow `develop`  
- Feature branches tied to tickets, merged into `dev`, then deleted  
- Releases marked by tags on the production branch  

The alignment is deliberate but lighter-weight than traditional GitFlow, removing unnecessary branching complexity.

---

# 6. Differences From Standard GitFlow

### 6.1 No Dedicated Release Branches
Release preparation occurs through merging `dev` into `main`; the release is finalized via a production tag rather than a `release/*` branch.

### 6.2 Hotfix Approach Is Implicit
Hotfixes are validated in STAGE and handled through standard feature branch flows rather than separate `hotfix/*` branches.

### 6.3 CI/CD Coupled to Branch/Tag Patterns

| Branch/Tag       | Deployment Target |
|------------------|------------------|
| Feature branch    | DEV              |
| `dev` branch      | CERT             |
| `main` branch     | STAGE            |
| Tag on `main`     | PROD             |

---

# 7. CI/CD Behavior in This Strategy

1. **Feature Development**
   - Jira-driven branches from `dev`
   - Commits trigger automated scans and DEV deployments

2. **Certification**
   - Feature branches merge to `dev` via PR
   - Merged changes deploy automatically to CERT

3. **Staging**
   - `dev` merged into `main` via PR
   - `main` deploys automatically to STAGE

4. **Production**
   - Tag created on `main`
   - Tag triggers controlled PROD deployment
   - Tags serve as the immutable release ledger

---

# END OF DOCUMENT
