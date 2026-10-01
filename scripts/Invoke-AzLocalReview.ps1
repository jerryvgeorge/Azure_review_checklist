<#
.SYNOPSIS
    Automated Review and Assessment Script for Azure Local (HCI).

.DESCRIPTION
    Evaluates an Azure Local (Azure Stack HCI) deployment against the recommendations
    defined in the Azure Local HCI Review Checklist (WAF-aligned).
    Supports assessing on-premises cluster nodes and/or cloud Azure Resource Graph inventory.

.PARAMETER ChecklistPath
    Path to the azure_local_hci_checklist.en.json file. Defaults to relative path.

.PARAMETER ClusterName
    Name or FQDN of the Azure Local cluster to inspect via PowerShell remoting.

.PARAMETER AssessCloud
    Switch to run Azure Resource Graph queries against current Azure subscription context.

.PARAMETER OutputReportPath
    Optional output JSON file path for assessment results.

.EXAMPLE
    pwsh ./scripts/Invoke-AzLocalReview.ps1 -ChecklistPath ./checklists/azure_local_hci_checklist.en.json

.EXAMPLE
    pwsh ./scripts/Invoke-AzLocalReview.ps1 -ClusterName "AzLocalCluster01" -AssessCloud
#>

[CmdletBinding()]
param (
    [Parameter(Mandatory = $false)]
    [string]$ChecklistPath = "$PSScriptRoot/../checklists/azure_local_hci_checklist.en.json",

    [Parameter(Mandatory = $false)]
    [string]$ClusterName,

    [Parameter(Mandatory = $false)]
    [switch]$AssessCloud,

    [Parameter(Mandatory = $false)]
    [string]$OutputReportPath
)

$ErrorActionPreference = "Continue"

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "          Azure Local (HCI) Review & Assessment Tool                  " -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Timestamp : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "Checklist : $ChecklistPath"

# 1. Load Checklist
if (-not (Test-Path $ChecklistPath)) {
    Write-Error "Checklist file not found at: $ChecklistPath"
    exit 1
}

try {
    $checklistRaw = Get-Content -Path $ChecklistPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $items = $checklistRaw.items
    Write-Host "Loaded $($items.Count) review checklist items across $($checklistRaw.categories.Count) categories.`n" -ForegroundColor Green
}
catch {
    Write-Error "Failed to parse JSON checklist: $_"
    exit 1
}

$results = [System.Collections.Generic.List[PSObject]]::new()

# 2. On-Premises Cluster Checks (If ClusterName is specified or running locally on a cluster node)
if ($ClusterName -or (Get-Command Get-Cluster -ErrorAction SilentlyContinue)) {
    Write-Host "[*] Evaluating Cluster Configuration..." -ForegroundColor Yellow
    
    $targetCluster = if ($ClusterName) { $ClusterName } else { (Get-Cluster).Name }
    Write-Host "Target Cluster: $targetCluster"
    
    # Check Quorum
    try {
        $quorum = if ($ClusterName) { Get-ClusterQuorum -Cluster $ClusterName } else { Get-ClusterQuorum }
        $hasWitness = ($quorum.QuorumType -match "Witness" -or $quorum.QuorumResource -ne $null)
        
        $results.Add([PSCustomObject]@{
            Id       = "01.01.07"
            Check    = "Cluster Quorum Witness Configuration"
            Category = "Hardware and Architecture"
            Status   = if ($hasWitness) { "Fulfilled" } else { "Open" }
            Severity = "High"
            Details  = "Quorum Type: $($quorum.QuorumType), Witness: $($quorum.QuorumResource.Name)"
        })
    }
    catch {
        Write-Warning "Could not query Cluster Quorum: $_"
    }

    # Check S2D Storage Pool and Disks
    try {
        $pools = if ($ClusterName) { Get-StoragePool -CimSession $ClusterName | Where-Object IsPrimordial -eq $false } else { Get-StoragePool | Where-Object IsPrimordial -eq $false }
        foreach ($pool in $pools) {
            $unallocatedGB = [math]::Round($pool.Size - $pool.AllocatedSize, 2) / 1GB
            $results.Add([PSCustomObject]@{
                Id       = "02.01.05"
                Check    = "Storage Pool Reserve Capacity"
                Category = "Storage and S2D"
                Status   = if ($unallocatedGB -gt 500) { "Fulfilled" } else { "Open" }
                Severity = "High"
                Details  = "Pool '$($pool.FriendlyName)': Total $([math]::Round($pool.Size / 1TB, 2)) TB, Unallocated $([math]::Round($unallocatedGB, 2)) GB"
            })
        }
    }
    catch {
        Write-Warning "Could not query Storage Pools: $_"
    }

    # Check Network ATC
    try {
        $intents = if ($ClusterName) { Invoke-Command -ComputerName $ClusterName -ScriptBlock { Get-NetIntent -ErrorAction SilentlyContinue } } else { Get-NetIntent -ErrorAction SilentlyContinue }
        $hasIntents = ($null -ne $intents -and $intents.Count -gt 0)
        $results.Add([PSCustomObject]@{
            Id       = "03.01.01"
            Check    = "Network ATC Intent Management"
            Category = "Networking and Network ATC"
            Status   = if ($hasIntents) { "Fulfilled" } else { "Open" }
            Severity = "High"
            Details  = if ($hasIntents) { "Configured Intents: $(($intents.IntentName) -join ', ')" } else { "No Network ATC intents detected." }
        })
    }
    catch {
        Write-Warning "Could not query Network ATC: $_"
    }

    # Check Health Faults
    try {
        $faults = if ($ClusterName) { Invoke-Command -ComputerName $ClusterName -ScriptBlock { Get-HealthFault -ErrorAction SilentlyContinue } } else { Get-HealthFault -ErrorAction SilentlyContinue }
        $faultCount = if ($faults) { $faults.Count } else { 0 }
        $results.Add([PSCustomObject]@{
            Id       = "06.01.06"
            Check    = "Cluster Health Service Faults"
            Category = "Operations and Lifecycle Management"
            Status   = if ($faultCount -eq 0) { "Fulfilled" } else { "Open" }
            Severity = "Medium"
            Details  = "Active Health Faults: $faultCount"
        })
    }
    catch {
        Write-Warning "Could not query Health Faults: $_"
    }
}

# 3. Cloud / Azure Resource Graph Checks
if ($AssessCloud) {
    Write-Host "[*] Evaluating Cloud & Azure Resource Graph Context..." -ForegroundColor Yellow
    if (Get-Command az -ErrorAction SilentlyContinue) {
        try {
            $clustersJson = az graph query -q "resources | where type =~ 'microsoft.azurestackhci/clusters' | project id, name, resourceGroup, properties.status, properties.lastSyncTimestamp" -o json | ConvertFrom-Json
            if ($clustersJson.data) {
                foreach ($c in $clustersJson.data) {
                    $results.Add([PSCustomObject]@{
                        Id       = "04.01.08"
                        Check    = "Azure Local Cloud Sync (30 Days)"
                        Category = "Hybrid Management and Azure Arc"
                        Status   = if ($c.'properties.status' -eq "Connected") { "Fulfilled" } else { "Open" }
                        Severity = "High"
                        Details  = "Cluster '$($c.name)' in RG '$($c.resourceGroup)', Status: $($c.'properties.status'), Last Sync: $($c.'properties.lastSyncTimestamp')"
                    })
                }
            }
        }
        catch {
            Write-Warning "Azure CLI graph query failed: $_"
        }
    }
    else {
        Write-Warning "Azure CLI ('az') not found. Skipping automated cloud queries."
    }
}

# 4. Display Results Summary
Write-Host "`n======================================================================" -ForegroundColor Cyan
Write-Host "                       Assessment Summary                             " -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

if ($results.Count -gt 0) {
    $results | Format-Table -Property Id, Severity, Status, Check, Details -AutoSize
    
    $fulfilledCount = ($results | Where-Object Status -eq "Fulfilled").Count
    $openCount = ($results | Where-Object Status -eq "Open").Count
    Write-Host "`nSummary: $fulfilledCount Checks Fulfilled, $openCount Open Action Items." -ForegroundColor Cyan
}
else {
    Write-Host "No active cluster session specified. You can run automated checks against your cluster with:"
    Write-Host "  pwsh ./scripts/Invoke-AzLocalReview.ps1 -ClusterName <ClusterFQDN>" -ForegroundColor Yellow
    Write-Host "Or evaluate your Azure subscription via:"
    Write-Host "  pwsh ./scripts/Invoke-AzLocalReview.ps1 -AssessCloud" -ForegroundColor Yellow
}

# 5. Export Report if requested
if ($OutputReportPath) {
    $report = [PSCustomObject]@{
        Timestamp    = (Get-Date).ToString("o")
        Checklist    = $checklistRaw.metadata.name
        Evaluated    = $results.Count
        Results      = $results
    }
    $report | ConvertTo-Json -Depth 5 | Set-Content -Path $OutputReportPath -Encoding UTF8
    Write-Host "`nAssessment report written to: $OutputReportPath" -ForegroundColor Green
}
