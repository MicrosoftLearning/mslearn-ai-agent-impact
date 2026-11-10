# Prepare the isolated Fabric foundation

Complete this setup before the timed exercises. Reuse the existing lab session and
recorded resources when resuming. Capacity creation is a billed operation; assign
an approved existing capacity when one is available.

## Check the prerequisites

1. Sign in to Azure and Fabric with the assigned learner identity. Verify the tenant
   and subscription against your environment record; browser sign-in to Azure does
   not automatically establish every Fabric, Foundry or GitHub connection.
1. Confirm Fabric is enabled for this identity and that its per-user entitlement is
   active. Complete the learner's first Fabric portal sign-in before diagnosing a
   licensing failure as a missing capacity.
1. Confirm subscription permission to create a Fabric capacity, registration of
   `Microsoft.Fabric`, sufficient regional CU quota, capacity assignment permission,
   and workspace creation/admin permission. Azure subscription Owner does not grant
   every Fabric or Microsoft 365 permission. Resolve missing grants with the tenant
   administrator; do not grant broad roles merely to silence an error.
1. Record the approved processing regions and check availability for every required
   workload, including Ontology preview. Do not enable cross-geo processing as a
   workaround. The F2 used in the foundation test is an observed test size, not a
   sizing or regional-approval claim for the complete workshop.

## Create or assign the capacity

1. In the Azure portal, search for **Microsoft Fabric**, then select **Create Fabric
   Capacity** only if no suitable assigned capacity exists.
1. Choose the actual subscription and isolated resource group. Enter a unique
   capacity name, approved region, approved size and capacity administrator. Review
   the estimate and create it. Do not copy a previous test's tenant-specific names.
1. Wait for deployment success and confirm the capacity is **Active**. Record its
   ARM resource ID and Fabric capacity GUID separately in `config/lab.local.json`.
1. In Fabric, select **Workspaces > New workspace** and create a learner-owned
   workspace. In its capacity/license settings, select the assigned Fabric capacity.
   Labels can vary by portal version. Confirm the effective capacity and region.
1. Record the workspace GUID from its actual URL. Return to Exercise 1 and create
   `caldova_l400` there; do not precomplete curation, replay or ontology work.

## Resume and record readiness

On resume, inspect the recorded capacity and workspace before creating anything.
If deployment or capacity assignment is pending, wait and inspect that operation;
do not submit duplicate deployments. Record the Lakehouse, notebook, Eventhouse,
database, Eventstream, ontology and named ontology-version checkpoint as they are
created. Keep credentials and connection strings out of the record and Git.

Capacity/workspace readiness unlocks the Fabric foundation only. Foundry models,
delegated Fabric IQ connections, procurement sources, channel publication and
source-access denial tests have their own gates in the [runtime guide](Runtime.md).
Leave final residency approval unresolved until actual service data flows are reviewed.

The cleanup owner must record when this learner's capacity can be suspended or
deleted. Do not end an active lab or remove another learner's resources during setup.

References: [capacity prerequisites and creation](https://learn.microsoft.com/en-us/fabric/enterprise/buy-capacity),
[workspace creation and assignment](https://learn.microsoft.com/en-us/fabric/fundamentals/create-workspaces),
[Fabric licensing](https://learn.microsoft.com/en-us/fabric/enterprise/licenses).
