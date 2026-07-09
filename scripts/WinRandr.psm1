# winrandr PowerShell 模块
# 安装: Import-Module .\scripts\WinRandr.psm1
# 要求: winrandr.exe 在 $env:PATH 中，或通过 python -m winrandr 可用

$script:WinRandrCmd = if (Get-Command winrandr -ErrorAction SilentlyContinue) {
    "winrandr"
} else {
    "uv run -m winrandr"
}

function _InvokeWinRandr {
    <#
    .SYNOPSIS
        内部函数：调用 winrandr 并检查退出码
    #>
    param([string[]]$Arguments)
    $output = & $script:WinRandrCmd @Arguments 2>&1
    if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) {
        Write-Error "winrandr 失败 (退出码 $LASTEXITCODE): $output"
        return $null
    }
    return $output
}

function Get-WinRandrDisplays {
    <#
    .SYNOPSIS
        获取显示器信息（结构化对象）
    .EXAMPLE
        Get-WinRandrDisplays
        Get-WinRandrDisplays | Format-Table Name, Width, Height, RefreshRate
    #>
    $raw = _InvokeWinRandr @("--json")
    if (-not $raw) { return @() }
    return $raw | Out-String | ConvertFrom-Json
}

function Set-WinRandrResolution {
    <#
    .SYNOPSIS
        设置显示器分辨率
    .PARAMETER Output
        显示器名称（如 DISPLAY1）
    .PARAMETER Mode
        分辨率（如 1920x1080）
    .PARAMETER Rate
        刷新率（如 60）
    .EXAMPLE
        Set-WinRandrResolution -Output DISPLAY1 -Mode 1920x1080 -Rate 60
    #>
    param(
        [Parameter(Mandatory)] [string]$Output,
        [Parameter(Mandatory)] [string]$Mode,
        [double]$Rate
    )
    $args = @("--output", $Output, "--mode", $Mode)
    if ($Rate) { $args += "--rate"; $args += "$Rate" }
    return _InvokeWinRandr $args
}

function Set-WinRandrPosition {
    <#
    .SYNOPSIS
        设置显示器桌面位置
    .PARAMETER Output
        显示器名称（如 DISPLAY1）
    .PARAMETER X
        X 坐标
    .PARAMETER Y
        Y 坐标
    .EXAMPLE
        Set-WinRandrPosition -Output DISPLAY1 -X 1920 -Y 0
    #>
    param(
        [Parameter(Mandatory)] [string]$Output,
        [Parameter(Mandatory)] [int]$X,
        [Parameter(Mandatory)] [int]$Y
    )
    return _InvokeWinRandr @("--output", $Output, "--pos", "${X}x${Y}")
}

function Set-WinRandrPrimary {
    <#
    .SYNOPSIS
        将指定显示器设为主显示器
    .PARAMETER Output
        显示器名称（如 DISPLAY1）
    .EXAMPLE
        Set-WinRandrPrimary -Output DISPLAY1
    #>
    param([Parameter(Mandatory)] [string]$Output)
    return _InvokeWinRandr @("--output", $Output, "--primary")
}

function Set-WinRandrBrightness {
    <#
    .SYNOPSIS
        设置显示器亮度（通过伽马校正）
    .PARAMETER Output
        显示器名称（如 DISPLAY1）
    .PARAMETER Brightness
        亮度值（0.1–2.0，1.0 为正常）
    .EXAMPLE
        Set-WinRandrBrightness -Output DISPLAY1 -Brightness 0.8
    #>
    param(
        [Parameter(Mandatory)] [string]$Output,
        [Parameter(Mandatory)] [double]$Brightness
    )
    return _InvokeWinRandr @("--output", $Output, "--brightness", "$Brightness")
}

function Set-WinRandrGamma {
    <#
    .SYNOPSIS
        设置显示器伽马校正值（三通道独立）
    .PARAMETER Output
        显示器名称（如 DISPLAY1）
    .PARAMETER Red
        红色通道伽马值
    .PARAMETER Green
        绿色通道伽马值
    .PARAMETER Blue
        蓝色通道伽马值
    .EXAMPLE
        Set-WinRandrGamma -Output DISPLAY1 -Red 1.0 -Green 0.8 -Blue 0.9
    #>
    param(
        [Parameter(Mandatory)] [string]$Output,
        [Parameter(Mandatory)] [double]$Red,
        [Parameter(Mandatory)] [double]$Green,
        [Parameter(Mandatory)] [double]$Blue
    )
    return _InvokeWinRandr @("--output", $Output, "--gamma", "${Red}:${Green}:${Blue}")
}

function Set-WinRandrRotation {
    <#
    .SYNOPSIS
        设置显示器旋转角度
    .PARAMETER Output
        显示器名称（如 DISPLAY1）
    .PARAMETER Degree
        旋转角度（0、90、180、270）
    .EXAMPLE
        Set-WinRandrRotation -Output DISPLAY1 -Degree 90
    #>
    param(
        [Parameter(Mandatory)] [string]$Output,
        [Parameter(Mandatory)] [ValidateSet(0, 90, 180, 270)] [int]$Degree
    )
    $rotateMap = @{0 = "normal"; 90 = "left"; 180 = "inverted"; 270 = "right"}
    return _InvokeWinRandr @("--output", $Output, "--rotate", $rotateMap[$Degree])
}

function Set-WinRandrOff {
    <#
    .SYNOPSIS
        关闭（禁用）指定显示器
    .PARAMETER Output
        显示器名称（如 DISPLAY1）
    .EXAMPLE
        Set-WinRandrOff -Output DISPLAY2
    #>
    param([Parameter(Mandatory)] [string]$Output)
    return _InvokeWinRandr @("--output", $Output, "--off")
}

function Set-WinRandrAuto {
    <#
    .SYNOPSIS
        启用显示器并使用首选分辨率（等价于 xrandr --auto）
    .PARAMETER Output
        显示器名称（如 DISPLAY1）
    .EXAMPLE
        Set-WinRandrAuto -Output DISPLAY1
    #>
    param([Parameter(Mandatory)] [string]$Output)
    return _InvokeWinRandr @("--output", $Output, "--auto")
}

function Set-WinRandrRelative {
    <#
    .SYNOPSIS
        相对定位（类似 xrandr --left-of / --right-of / --above / --below / --same-as）
    .PARAMETER Output
        要移动的显示器名称
    .PARAMETER Reference
        参考显示器名称
    .PARAMETER Position
        相对位置关系
    .EXAMPLE
        Set-WinRandrRelative -Output DISPLAY2 -Reference DISPLAY1 -Position right-of
    #>
    param(
        [Parameter(Mandatory)] [string]$Output,
        [Parameter(Mandatory)] [string]$Reference,
        [Parameter(Mandatory)] [ValidateSet("left-of", "right-of", "above", "below", "same-as")]
        [string]$Position
    )
    return _InvokeWinRandr @("--output", $Output, "--$Position", $Reference)
}

function Set-WinRandrReflect {
    <#
    .SYNOPSIS
        设置显示器镜像翻转
    .PARAMETER Output
        显示器名称（如 DISPLAY1）
    .PARAMETER ReflectMode
        镜像模式（normal、x、y、xy；仅 xy 受支持，x/y 会提示无标准 API）
    .EXAMPLE
        Set-WinRandrReflect -Output DISPLAY1 -ReflectMode xy
    #>
    param(
        [Parameter(Mandatory)] [string]$Output,
        [Parameter(Mandatory)] [ValidateSet("normal", "x", "y", "xy")] [string]$ReflectMode
    )
    return _InvokeWinRandr @("--output", $Output, "--reflect", $ReflectMode)
}

function Set-WinRandrPreferred {
    <#
    .SYNOPSIS
        将显示器设为首选分辨率（注册表存储）
    .PARAMETER Output
        显示器名称（如 DISPLAY1）
    .EXAMPLE
        Set-WinRandrPreferred -Output DISPLAY1
    #>
    param([Parameter(Mandatory)] [string]$Output)
    return _InvokeWinRandr @("--output", $Output, "--preferred")
}

function Clear-WinRandrPrimary {
    <#
    .SYNOPSIS
        清除所有显示器的主显示器标记
    .EXAMPLE
        Clear-WinRandrPrimary
    #>
    return _InvokeWinRandr @("--noprimary")
}

function Invoke-WinRandrIdentify {
    <#
    .SYNOPSIS
        通过闪烁屏幕识别指定显示器
    .PARAMETER Output
        显示器名称（如 DISPLAY1）
    .EXAMPLE
        Invoke-WinRandrIdentify -Output DISPLAY1
    #>
    param([Parameter(Mandatory)] [string]$Output)
    return _InvokeWinRandr @("--identify", "--output", $Output)
}

function Save-WinRandrProfile {
    <#
    .SYNOPSIS
        保存当前显示器布局为存档
    .PARAMETER Name
        存档名称
    .EXAMPLE
        Save-WinRandrProfile -Name "docked"
    #>
    param([Parameter(Mandatory)] [string]$Name)
    return _InvokeWinRandr @("--save-profile", $Name)
}

function Restore-WinRandrProfile {
    <#
    .SYNOPSIS
        加载显示器布局存档
    .PARAMETER Name
        存档名称
    .EXAMPLE
        Restore-WinRandrProfile -Name "docked"
    #>
    param([Parameter(Mandatory)] [string]$Name)
    return _InvokeWinRandr @("--load-profile", $Name)
}

function Get-WinRandrProfile {
    <#
    .SYNOPSIS
        列出所有已保存的显示器布局存档
    .EXAMPLE
        Get-WinRandrProfile
        Get-WinRandrProfile | Format-Table Name, DisplayCount, Created
    #>
    $raw = _InvokeWinRandr @("--list-profiles", "--json")
    if (-not $raw) { return @() }
    return $raw | Out-String | ConvertFrom-Json
}

function Remove-WinRandrProfile {
    <#
    .SYNOPSIS
        删除指定显示器布局存档
    .PARAMETER Name
        存档名称
    .EXAMPLE
        Remove-WinRandrProfile -Name "docked"
    #>
    param([Parameter(Mandatory)] [string]$Name)
    return _InvokeWinRandr @("--delete-profile", $Name)
}

Export-ModuleMember -Function @(
    "Get-WinRandrDisplays",
    "Set-WinRandrResolution",
    "Set-WinRandrPosition",
    "Set-WinRandrPrimary",
    "Set-WinRandrBrightness",
    "Set-WinRandrGamma",
    "Set-WinRandrRotation",
    "Set-WinRandrReflect",
    "Set-WinRandrPreferred",
    "Clear-WinRandrPrimary",
    "Invoke-WinRandrIdentify",
    "Set-WinRandrOff",
    "Set-WinRandrAuto",
    "Set-WinRandrRelative",
    "Get-WinRandrProfile",
    "Save-WinRandrProfile",
    "Restore-WinRandrProfile",
    "Remove-WinRandrProfile"
)
