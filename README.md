# Azure Local (HCI) Review Checklist

A comprehensive architectural and operational review checklist for **Azure Local** (formerly Azure Stack HCI), designed and structured to align with the official Microsoft [Azure Review Checklists](https://github.com/Azure/review-checklists/blob/main/spreadsheet/README.md) framework and the **Azure Well-Architected Framework (WAF)**.

---

## Overview

Azure Local represents Microsoft's unified infrastructure platform connecting on-premises and edge hardware to Azure Arc. Designing and operating an enterprise-grade Azure Local deployment requires rigorous attention across physical hardware, Storage Spaces Direct (S2D), Network ATC intents, RDMA/QoS, security baselines, and Azure Arc management.

This checklist provides **84 in-depth best-practice checks** across 9 architectural pillars:

| # | Category | Key Focus Areas |
|---|---|---|
| 1 | **Hardware and Architecture** | Certified catalog nodes (Premier/Integrated), CPU/RAM symmetry, dedicated OS boot drives (BOSS/SATADOM), TPM 2.0, Secure Boot, VBS/HVCI, out-of-band BMC isolation, Cloud Witness, N+1 capacity sizing. |
| 2 | **Storage and S2D** | Direct-attached NVMe/SSD, drive symmetry, 3-way mirroring, nested resiliency (2-node), delimited volume allocation, CSV in-memory caching, ReFS 64KB, reserve capacity planning, DiskSpd/VMFleet baselining. |
| 3 | **Networking and Network ATC** | Network ATC intent deployment, redundant 25GbE+ adapters, RDMA (RoCEv2/iWARP), Priority Flow Control (PFC Priority 3) & ETS, Jumbo Frames (MTU 9014/9216), isolated storage subnets without default gateways, Network HUD. |
| 4 | **Hybrid Management and Azure Arc** | Azure Arc Resource Bridge (ARB), Custom Locations, Logical Networks & static IP pools, Azure Arc VM management (ARM/Bicep/Terraform), firewall outbound whitelisting (no SSL inspection), 30-day cloud sync validation. |
| 5 | **Security and Governance** | Azure Local Security Baseline (300+ controls), Windows Defender Application Control (WDAC) enforced mode, BitLocker on CSVs & OS, Credential Guard, SMB encryption & signing, GPO inheritance blocking, Windows LAPS & JEA. |
| 6 | **Operations and Lifecycle Management** | Azure Local Lifecycle Manager (LCM) / Azure Update Manager full-stack one-click updates, Cluster-Aware Updating (CAU) live migration, Environment Checker, Azure Local Insights (AMA + Log Analytics), Health Service alerting. |
| 7 | **Workloads and Edge Services** | AKS enabled by Azure Arc (CSI storage classes, container CNI, GitOps/Flux v2), Azure Virtual Desktop (AVD) for Azure Local multi-session, SQL Server CSV separation (Data, Log, TempDB), Arc-enabled Data Services. |
| 8 | **Backup and Disaster Recovery** | Application-consistent VM backups (MABS/DPM/Veeam), Azure Site Recovery (ASR), multi-site Stretch Clustering with Storage Replica (sub-5ms RTT, dedicated replication network, 3rd-site Cloud Witness), disaster recovery runbooks. |
| 9 | **Cost Optimization and Licensing** | Azure Hybrid Benefit (AHB) for Windows Server Datacenter (waiving host service fees and unlimited guest licenses), Azure tags for cost allocation, VM right-sizing, ReFS data deduplication and compression on archive volumes. |

---

## Repository Structure

```
Az_Local_Review_Scripts/
├── checklists/
│   ├── azure_local_hci_checklist.en.json   # Primary official JSON checklist (WAF-aligned)
│   └── hci_checklist.en.json              # Compatible drop-in for official Excel macro
├── spreadsheet/
│   ├── Azure_Local_HCI_Review_Checklist.xlsx # Pre-populated macro-free Excel workbook
│   ├── review_checklist.xlsm               # Macro-enabled workbook template (Import feature)
│   ├── review_checklist_empty.xlsx         # Base spreadsheet template
│   └── README.md                           # Detailed spreadsheet user guide
├── scripts/
│   ├── generate_spreadsheet.py            # Standalone zero-dependency Excel generator
│   ├── build_checklist.py                 # Checklist builder & compiler
│   ├── verify_checklist.py                # Official review-checklists schema validator
│   ├── Invoke-AzLocalReview.ps1           # Automated PowerShell 7 assessment script
│   └── AzLocal_ARG_Queries.kql            # Azure Resource Graph assessment queries
└── README.md                              # This guide
```

---

## How to Use

### 1. Excel Spreadsheet Review

You can conduct reviews directly in Microsoft Excel:

1. Open [`spreadsheet/Azure_Local_HCI_Review_Checklist.xlsx`](./spreadsheet/Azure_Local_HCI_Review_Checklist.xlsx).
2. Go row by row and set the **Status** (Column F) using the dropdown list:
   - `Not verified`: Check has not been evaluated yet.
   - `Open`: Action item required.
   - `Fulfilled`: Requirement is fully satisfied and tested.
   - `Not required`: Understood, but exempted by current architecture.
   - `N/A`: Not applicable to this environment.
3. Write review findings and justification in the **Comments** field (Column G).
4. Click **More info** (Column H) to jump directly to official Microsoft technical documentation.
5. The live dashboard banner on Row 5 computes fulfillment progress automatically.

For more details on Excel usage, see [spreadsheet/README.md](./spreadsheet/README.md).

---

### 2. Automated Assessment via PowerShell

Use the included PowerShell script to audit an Azure Local cluster or query Azure Resource Graph:

```powershell
# Evaluate an active on-premises Azure Local cluster:
pwsh ./scripts/Invoke-AzLocalReview.ps1 -ClusterName "AzLocalCluster01"

# Evaluate Azure subscription resources via Azure Resource Graph:
pwsh ./scripts/Invoke-AzLocalReview.ps1 -AssessCloud

# Output an assessment report to JSON:
pwsh ./scripts/Invoke-AzLocalReview.ps1 -ClusterName "AzLocalCluster01" -OutputReportPath "./report.json"
```

---

### 3. Azure Resource Graph (ARG) Queries

For cloud-side inventory, compliance, and sync auditing, execute the pre-written KQL queries in [`scripts/AzLocal_ARG_Queries.kql`](./scripts/AzLocal_ARG_Queries.kql) inside **Azure Resource Graph Explorer** or Azure CLI:

* **Cluster Status & 30-Day Cloud Sync**: Audits `microsoft.azurestackhci/clusters`.
* **Arc Resource Bridge Appliance Status**: Audits `microsoft.resourceconnector/appliances`.
* **Custom Locations & Arc VM Inventory**: Audits `microsoft.extendedlocation/customlocations` and `microsoft.azurestackhci/virtualmachineinstances`.
* **Lifecycle Manager Update Compliance**: Audits `microsoft.azurestackhci/updateruns`.
* **Arc Host Extensions (AMA, Defender)**: Audits `microsoft.hybridcompute/machines/extensions`.

---

### 4. Checklist Validation

The JSON definition is 100% compliant with the official `Azure/review-checklists` specification:

```bash
python3 ./scripts/verify_checklist.py --input-file ./checklists/azure_local_hci_checklist.en.json --verbose
```
*Current status:* **84 items verified, 0 errors, 0 warnings.**

---

## Contributing and Customization

To add or modify recommendations:
1. Update items in [`scripts/build_checklist.py`](./scripts/build_checklist.py).
2. Run `python3 scripts/build_checklist.py` to compile the JSON definitions.
3. Run `python3 scripts/verify_checklist.py --input-file checklists/azure_local_hci_checklist.en.json` to ensure schema compliance.
4. Run `python3 scripts/generate_spreadsheet.py` to update the Excel workbook.
# Azure_review_checklist
