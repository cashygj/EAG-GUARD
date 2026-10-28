<#
.SYNOPSIS
    一键跑完全部实验；随时 Ctrl+C，下次接着跑，不会从头再来。

.DESCRIPTION
    每次运行都写到固定目录，并带 --resume：已完成的 (user_task, injection_task)
    会被跳过；写了一半或带 error 的轨迹会被自动重跑。
    因此中断只会损失"正在跑的那一对"。

.PARAMETER Model
    模型名。默认 qwen-plus-2025-04-28（报告用的快照），不要随手改成滚动别名。

.PARAMETER Scope
    slice = 25 对切片（user_task_0–4 × injection_task_1–5）
    full  = 该域全部对
    both  = 先切片后全域（默认）

.PARAMETER Arms
    要跑的臂，默认 eag,undefended。

.EXAMPLE
    .\run_all.ps1                      # 全部（切片 + 全域，两臂）
    .\run_all.ps1 -Scope slice         # 只跑切片
    .\run_all.ps1 -Domains slack       # 只跑 slack
    .\run_all.ps1 -Status              # 只看进度，不跑
#>
[CmdletBinding()]
param(
    [string]$Model = "qwen-plus-2025-04-28",
    [ValidateSet("slice", "full", "both")][string]$Scope = "both",
    [string[]]$Domains = @("slack", "workspace", "travel", "banking"),
    [string[]]$Arms = @("eag", "undefended"),
    [switch]$Status
)

$ErrorActionPreference = "Stop"

# cmd 透传 "banking,travel" 时会当成一个字符串，这里统一拆开并校验
$Domains = @($Domains | ForEach-Object { $_ -split "," } | Where-Object { $_ })
$Repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $Repo ".venv\Scripts\python.exe"
$Bench = Join-Path $Repo "scripts\run_bench.py"
$LogDir = Join-Path $Repo "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$env:PYTHONPATH = Join-Path $Repo "src"
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 每个域的配对数：user_tasks × injection_tasks
$Totals = @{ slack = 105; travel = 140; banking = 144; workspace = 240 }

function Get-ScopeArgs {
    param([string]$Which)
    if ($Which -eq "slice") {
        return @("--user-tasks", "0-4", "--injection-tasks", "1-5")
    }
    return @("--user-tasks", "all", "--injection-tasks", "all")
}

function Get-Expected {
    param([string]$Which, [string]$Domain)
    if ($Which -eq "slice") { return 25 }
    return $Totals[$Domain]
}

function Get-Done {
    param([string]$Dir)
    if (-not (Test-Path $Dir)) { return 0 }
    return (Get-ChildItem $Dir -Filter *.json -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -ne "summary.json" } | Measure-Object).Count
}

function Get-RunName {
    param([string]$Domain, [string]$Which, [string]$Arm)
    return "${Domain}_${Which}_${Arm}"
}

$Jobs = @()
foreach ($domain in $Domains) {
    foreach ($which in @("slice", "full")) {
        if ($Scope -ne "both" -and $Scope -ne $which) { continue }
        foreach ($arm in $Arms) {
            $Jobs += [pscustomobject]@{
                Domain = $domain
                Which  = $which
                Arm    = $arm
                Name   = (Get-RunName $domain $which $arm)
                Dir    = (Join-Path $Repo ("results\runs\" + (Get-RunName $domain $which $arm)))
                Total  = (Get-Expected $which $domain)
            }
        }
    }
}

function Show-Status {
    param($JobList)
    Write-Host ""
    Write-Host ("{0,-34} {1,8} {2,8}  {3}" -f "运行", "已完成", "总数", "进度") -ForegroundColor Cyan
    $allDone = 0; $allTotal = 0
    foreach ($job in $JobList) {
        $done = Get-Done $job.Dir
        $allDone += [Math]::Min($done, $job.Total)
        $allTotal += $job.Total
        $bar = "#" * [int](20 * $done / [Math]::Max($job.Total, 1))
        Write-Host ("{0,-34} {1,8} {2,8}  {3}" -f $job.Name, $done, $job.Total, $bar)
    }
    Write-Host ("合计 {0}/{1}" -f $allDone, $allTotal) -ForegroundColor Cyan
    Write-Host ""
}

if ($Status) {
    Show-Status $Jobs
    return
}

Show-Status $Jobs
Write-Host "模型：$Model" -ForegroundColor Yellow
Write-Host "中断后再次运行本脚本即可从断点继续（已完成的对不会重跑）。" -ForegroundColor Yellow

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$log = Join-Path $LogDir "run-all-$stamp.log"
"===== run_all start $((Get-Date).ToString('o')) model=$Model scope=$Scope =====" | Out-File $log -Encoding utf8

foreach ($job in $Jobs) {
    $doneBefore = Get-Done $job.Dir
    if ($doneBefore -ge $job.Total) {
        Write-Host ("跳过 {0}（已完成 {1}/{2}）" -f $job.Name, $doneBefore, $job.Total) -ForegroundColor DarkGray
        continue
    }
    Write-Host ("`n===== {0} （已有 {1}/{2}）=====" -f $job.Name, $doneBefore, $job.Total) -ForegroundColor Green
    "--- $($job.Name) start $((Get-Date).ToString('o')) ---" | Out-File $log -Encoding utf8 -Append

    $args = @(
        $Bench,
        "--suite", $job.Domain,
        "--arm", $job.Arm,
        "--model", $Model,
        "--out", $job.Dir,
        "--resume"
    ) + (Get-ScopeArgs $job.Which)
    if ($job.Arm -eq "eag") { $args += "--no-cache" }

    & $Python @args 2>&1 | Tee-Object -FilePath $log -Append
    "--- $($job.Name) exit=$LASTEXITCODE ---" | Out-File $log -Encoding utf8 -Append

    if ($LASTEXITCODE -ne 0) {
        Write-Host ("{0} 非零退出（{1}）。已完成的轨迹保留，重跑本脚本会接着来。" -f $job.Name, $LASTEXITCODE) -ForegroundColor Red
    }
}

Show-Status $Jobs
Write-Host "全部结束。日志：$log" -ForegroundColor Cyan

