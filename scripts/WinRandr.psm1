# winrandr PowerShell 模块
# 安装: Import-Module .\scripts\WinRandr.psm1

function Get-WinRandrDisplays {
    <#
    .SYNOPSIS
        获取显示器信息（结构化对象）
    #>
    $raw = winrandr --json | ConvertFrom-Json
    return $raw
}

function Set-WinRandrResolution {
    <#
    .SYNOPSIS
        设置显示器分辨率
    .PARAMETER Output
        显示器名称 (如 DISPLAY1)
    .PARAMETER Mode
        分辨率 (如 1920x1080)
    .PARAMETER Rate
        刷新率 (如 60)
    #>
    param(
        [Parameter(Mandatory)] [string]$Output,
        [Parameter(Mandatory)] [string]$Mode,
        [double]$Rate
    )
    $args = @("--output", $Output, "--mode", $Mode)
    if ($Rate) { $args += "--rate"; $args += "$Rate" }
    & winrandr $args
}

function Set-WinRandrPosition {
    <#
    .SYNOPSIS
        设置显示器位置
    #>
    param(
        [Parameter(Mandatory)] [string]$Output,
        [Parameter(Mandatory)] [string]$Pos
    )
    winrandr --output $Output --pos $Pos
}

function Set-WinRandrPrimary {
    <#
    .SYNOPSIS
        设为主显示器
    #>
    param([Parameter(Mandatory)] [string]$Output)
    winrandr --output $Output --primary
}

function Set-WinRandrBrightness {
    <#
    .SYNOPSIS
        设置亮度
    #>
    param(
        [Parameter(Mandatory)] [string]$Output,
        [Parameter(Mandatory)] [double]$Brightness
    )
    winrandr --output $Output --brightness $Brightness
}

function Save-WinRandrProfile {
    <#
    .SYNOPSIS
        保存显示器布局存档
    #>
    param([Parameter(Mandatory)] [string]$Name)
    winrandr --save-profile $Name
}

function Restore-WinRandrProfile {
    <#
    .SYNOPSIS
        加载显示器布局存档
    #>
    param([Parameter(Mandatory)] [string]$Name)
    winrandr --load-profile $Name
}

Export-ModuleMember -Function Get-WinRandrDisplays, Set-WinRandrResolution,
    Set-WinRandrPosition, Set-WinRandrPrimary, Set-WinRandrBrightness,
    Save-WinRandrProfile, Restore-WinRandrProfile
