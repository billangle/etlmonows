# FPAC CI/CD Least-Privilege Deployment Model Using AWS CDK

This document defines the secure, least-privilege architecture used by the FPAC CI/CD pipeline for deploying AWS infrastructure using the AWS Cloud Development Kit (CDK). It provides a detailed explanation of the identity model, permission boundaries, idempotency requirements, and the automated deployment workflow that ensures consistent, compliant, and secure cloud operations.

---

# 1. Executive Summary

The FPAC CI/CD pipeline deploys all cloud application components using a tightly scoped, least-privilege security model built on the AWS Cloud Development Kit (CDK). This model ensures that:

- Infrastructure is defined and provisioned **exclusively through IaC** (no console changes).  
- All deployments are **idempotent**, deterministic, and safe to re-run.  
- Permissions for CI/CD are **minimized**, reducing blast radius.  
- All modifications are version-controlled and automated.  
- CloudFormation acts as the only provisioning engine, with restricted permissions.  

The result is a secure, automated, repeatable deployment framework aligned with FPAC and USDA security requirements.

---

# 2. Architecture Overview

The architecture uses a **two-role model**:

### **2.1 Deployer Role (FPAC-CDK-DeployerRole)**
Used by the CI/CD pipeline to:
- Synthesize CDK templates  
- Create/Update/Delete CloudFormation stacks  
- Pass a restricted execution role to CloudFormation  
- Perform read-only environment lookups  

**Critical:**  
This role **does NOT** have permission to create AWS resources directly.

---

### **2.2 Execution Role (FPAC-CDK-ExecutionRole)**  
Assumed by CloudFormation during deployment.  
This is the only role permitted to:

- Create application infrastructure  
- Modify AWS services approved by FPAC  
- Delete resources during stack updates  
- Work within a restricted service and resource set  
- Operate under a permissions boundary  

This role enforces the **allowed services list** and prevents creation of unauthorized resources (e.g., DynamoDB unless explicitly enabled).

---

# 3. Idempotency and CDK Requirements

The architecture assumes:

- All infrastructure is defined in CDK.
- CDK code is **idempotent**—safe to run repeatedly without manual resets.
- No resource is created or modified outside the pipeline.
- CDK synthesizes CloudFormation templates that fully describe desired state.

Manual console changes are prohibited because they break idempotency and lead to drift.

**All infrastructure must be deployed exclusively through CDK pipelines.**

---

# 4. CI/CD Deployment Workflow

```text
Developer → Commit Code → CI/CD Pipeline → Assume DeployerRole →
CloudFormation → Assume ExecutionRole → Provision Allowed AWS Services
