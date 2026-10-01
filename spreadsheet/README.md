# Using the Azure Local (HCI) Review Spreadsheet

This spreadsheet provides an interactive, Well-Architected Framework (WAF)-aligned review tool for **Azure Local** (formerly Azure Stack HCI), modeled after the official [Azure Review Checklists](https://github.com/Azure/review-checklists/blob/main/spreadsheet/README.md) project.

---

## Quick Start: Using the Review Spreadsheet

### Option 1: Standalone Macro-Free Spreadsheet (Recommended for Mac & Corporate Desktops)
If you are working on **Office for Mac**, **Office 365 Web**, or in an environment where VBA macros are restricted for security reasons:

1. Open [`Azure_Local_HCI_Review_Checklist.xlsx`](./Azure_Local_HCI_Review_Checklist.xlsx) directly in Microsoft Excel.
2. All **84 Azure Local review checks** across all 9 architectural categories are pre-loaded and ready for evaluation.
3. Use the **Data Validation dropdowns** in the **Status** column (Column F) to mark each item:
   - **Not verified**: Check has not been reviewed yet.
   - **Open**: An action item or remediation is required.
   - **Fulfilled**: Recommendation is implemented and verified.
   - **Not required**: Recommendation understood, but not needed for this deployment.
   - **N/A**: Not applicable for this specific architecture.
4. Record implementation notes, justification for exceptions, or remediation tickets in the **Comment** column (Column G).
5. Click the **More info** link (Column H) on any row to open the official Microsoft Learn documentation for that topic.
6. The KPI dashboard banner at the top of the worksheet (Row 5) automatically tracks your review progress:
   - **Total Checks**
   - **Fulfilled Items**
   - **Open Action Items**
   - **Not Verified Items**

---

### Option 2: Macro-Enabled Spreadsheet (`review_checklist.xlsm`)
If you have Microsoft Excel on Windows with macros enabled:

1. Open [`review_checklist.xlsm`](./review_checklist.xlsm).
2. Select **Azure Stack HCI** / **Azure Local** in the technology dropdown and **English** for language.
3. Click the button **Import latest checklist**.
4. To import the latest local JSON file:
   - Run the macro `import_checklist_fromfile` and select [`../checklists/azure_local_hci_checklist.en.json`](../checklists/azure_local_hci_checklist.en.json).
5. Use the built-in VBA features to import Azure Resource Graph query results directly into the spreadsheet.

---

## Review Recommendations: Best Practices

* **Proceed in Chunks**:
  - Review one pillar/area at a time (e.g., start with **Hardware and Architecture**, then **Storage and S2D**, followed by **Networking and Network ATC**).
  - Alternatively, filter by **Severity = High** first to ensure critical baseline controls (such as Quorum Witness, RDMA, Security Baseline, BitLocker, and Arc Resource Bridge) are satisfied before reviewing Medium and Low items.
* **Design Compromises**:
  - Architecture reviews are not a box-ticking exercise, but a series of informed engineering trade-offs.
  - If a recommendation is waived (e.g., switchless storage instead of switched due to 2-node cluster size), document the technical rationale in the **Comment** column and set the status to **Not required** or **N/A**.
* **Automate Verification**:
  - Check Column J (**Graph Query**) to see if automated verification is available via Azure Resource Graph.
  - You can run the queries in [`../scripts/AzLocal_ARG_Queries.kql`](../scripts/AzLocal_ARG_Queries.kql) to validate cloud sync, Arc Resource Bridge health, and extensions.

---

## Re-generating the Spreadsheet

If you customize or add new review items in [`../checklists/azure_local_hci_checklist.en.json`](../checklists/azure_local_hci_checklist.en.json), re-generate the Excel spreadsheet at any time by running:

```bash
python3 ../scripts/generate_spreadsheet.py
```
This script uses standard Python libraries (no external packages required) to update the Excel template.
