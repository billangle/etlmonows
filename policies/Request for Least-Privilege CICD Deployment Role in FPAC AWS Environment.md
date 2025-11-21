**Ticket Title**

Request for Least-Privilege CI/CD Deployment Role in FPAC AWS Environment



**Purpose**

The purpose of this request is to establish a tightly scoped, least-privilege IAM role to be used exclusively by the FPAC CI/CD pipeline for deploying pre-approved application components into the AWS environment. This role is intended to support secure, automated deployments while maintaining OCIO/DISC control over all administrative, networking, and account-level functions.



**Background**

Current deployments into the FPAC AWS environment rely heavily on manual steps performed by individual users. This approach introduces operational and security challenges, including:

\* Inconsistent configuration across environments (DEV/TEST/CERT/PROD)

\* Limited repeatability and auditability of changes

\* Increased risk of human error during deployments

\* Delays in implementing security fixes and patches



*The FPAC team is transitioning to an automated CI/CD model using Bitbucket and AWS-native services. To comply with least-privilege principles, the CI/CD pipeline requires a purpose-built execution role with only the minimum permissions needed to deploy CloudFormation stacks and update a small set of application resources.*



**Current** **Limitation**

Under existing restrictions, the CI/CD pipeline does not have sufficient permissions to:

\* Create or update CloudFormation stacks that encapsulate approved infrastructure-as-code patterns

\* Pass pre-approved execution roles to CloudFormation

\* Interact with S3 and KMS for encrypted pipeline artifacts

\* Update specific Lambda and Glue resources associated with an application release



*As a result, deployments either cannot be fully automated, or they require manual intervention by privileged users, which increases operational risk and reduces traceability.*



**Proposed** **Control**

We propose creating a dedicated CI/CD Deployment Role with the IAM policy attached as described above. This role:

\* Allows CloudFormation to create and update stacks based on approved templates

\* Allows iam:PassRole only for a small set of pre-approved roles, restricted via iam:PassedToService = cloudformation.amazonaws.com

\* Grants S3 and KMS permissions limited to the pipeline artifact bucket and a specific KMS key

\* Grants only the minimal Lambda/Glue actions required to update existing, FPAC-named functions and jobs

\* Does not grant the ability to create, modify, or delete IAM policies, roles, users, VPCs, subnets, EC2 instances, gateways, RDS instances, Organizations, or other account-level services



*An explicit Deny statement is included for high-risk administrative and infrastructure actions to reinforce FPAC’s security boundaries.*



**Security Considerations and Alignment**

This request is designed to comply with federal security requirements and FPAC governance standards, including:

\* NIST SP 800-53 AC-6 (Least Privilege) – Access is limited to the minimum set of actions required for the CI/CD pipeline to perform its function.

\* NIST SP 800-53 CM-5 (Access Restrictions for Change) – The role can only deploy changes via CloudFormation using approved templates and roles; it cannot alter IAM, networking, or Organizations configuration.

\* Separation of Duties – OCIO/DISC retains sole control over creation and modification of IAM roles, SCPs, VPCs, and other high-risk resources. The CI/CD role has no capability to override these controls.

\* Auditability – All changes occur via CloudFormation and CI/CD tooling, producing a consistent audit trail of deployments.



*No permissions are granted that would allow privilege escalation, modification of SCPs, or creation of standalone infrastructure outside the boundaries defined by FPAC and OCIO.*



**Scope and Limitations**

\* The role is non-interactive and is intended to be assumed only by the CI/CD pipeline.

\* It does not grant console access to human users.

\* It does not permit creation or modification of IAM users, groups, or customer-managed policies.

\* It does not permit creation or alteration of VPCs, subnets, gateways, EC2 instances, RDS instances, or similar compute/network resources.

\* It does not modify AWS Organizations, CloudTrail, or Config.



*Any future expansion of scope would require a separate review and approval.*



**Benefits**

Approving this role will:

\* Reduce deployment risk by minimizing manual, ad-hoc changes in the console

\* Improve consistency between environments via repeatable, automated deployments

\* Increase auditability by centralizing changes through CloudFormation and CI/CD logs

\* Maintain strong security boundaries by enforcing least privilege and explicit denies for high-risk actions



*This approach strengthens, rather than weakens, FPAC’s overall security posture.*



**Request**

We respectfully request DISC/OCIO approval to:

1. Create the CI/CD Deployment Role in the FPAC AWS account(s) with the IAM policy defined above.
2. Configure the Bitbucket CI/CD pipeline to assume this role for automated deployments.



We are available to refine the allowed actions and resource scopes further in collaboration with DISC to ensure full alignment with FPAC security requirements.

