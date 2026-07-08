<#
.SYNOPSIS
    winrandr PowerShell 参数补全

.INSTALLATION
    将本文件放入 PowerShell 模块路径或手动 dot-source：
        PS> . ./scripts/completions.ps1
    或永久生效：
        PS> Add-Content $PROFILE "`n. 'C:\path\to\winrandr\scripts\completions.ps1'"
#>

Register-ArgumentCompleter -Native -CommandName winrandr, winrandr.exe -ScriptBlock {
    param($wordToComplete, $commandAst, $cursorPosition)

    $prev = $null
    $words = $commandAst.CommandElements | ForEach-Object { $_.Extent.Text }
    for ($i = 0; $i -lt $words.Count - 1; $i++) {
        if ($words[$i] -notlike '-*') { continue }
        $prev = $words[$i]
    }

    # 如果上一个参数需要显示器名，补全 DISPLAY1, DISPLAY2...
    if ($prev -in @('--output', '-o', '--left-of', '--right-of', '--above', '--below', '--same-as')) {
        # 尝试从 winrandr 获取显示列表
        $displays = & winrandr --json 2>$null | ConvertFrom-Json 2>$null
        if ($displays) {
            $displays | ForEach-Object {
                $name = $_.name -replace '\\\\\\.\\\\', ''
                if ($name) {
                    [System.Management.Automation.CompletionResult]::new($name, $name, 'ParameterValue', "$($_.friendly_name) $($_.width)x$($_.height)")
                }
            }
            return
        }
        # 回退
        'DISPLAY1', 'DISPLAY2', 'DISPLAY3', 'DISPLAY4' | ForEach-Object {
            [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
        }
        return
    }

    # 存档名补全
    if ($prev -in @('--load-profile', '--delete-profile', '--save-profile')) {
        $profiles = & winrandr --list-profiles --json 2>$null | ConvertFrom-Json 2>$null
        if ($profiles) {
            $profiles | ForEach-Object {
                [System.Management.Automation.CompletionResult]::new($_.name, $_.name, 'ParameterValue', "显示器: $($_.display_count), $($_.created)")
            }
            return
        }
        return
    }

    # 顶层参数补全
    $opts = @(
        [PSCustomObject]@{Option='--help';          Description='显示帮助'}
        [PSCustomObject]@{Option='-q';               Description='查询显示状态（别名 --query）'}
        [PSCustomObject]@{Option='--query';          Description='查询显示状态'}
        [PSCustomObject]@{Option='--current';        Description='查询当前配置'}
        [PSCustomObject]@{Option='--orientation';    Description='旋转方向'; NeedsArg=$true; Args='normal|left|right|inverted'}
        [PSCustomObject]@{Option='-x';               Description='水平镜像翻转'}
        [PSCustomObject]@{Option='-y';               Description='垂直镜像翻转'}
        [PSCustomObject]@{Option='--version';        Description='显示版本号'}
        [PSCustomObject]@{Option='--listmodes';      Description='列出所有可用分辨率'}
        [PSCustomObject]@{Option='--prop';           Description='显示显示器扩展属性'}
        [PSCustomObject]@{Option='--properties';     Description='显示显示器扩展属性（同 --prop）'}
        [PSCustomObject]@{Option='--verbose';        Description='详细日志'}
        [PSCustomObject]@{Option='-v';               Description='显示版本号（同 --version）'}
        [PSCustomObject]@{Option='--output';         Description='选择显示器'; NeedsArg=$true}
        [PSCustomObject]@{Option='-o';               Description='选择显示器（同 --output）'; NeedsArg=$true}
        [PSCustomObject]@{Option='--mode';           Description='设置分辨率'; NeedsArg=$true}
        [PSCustomObject]@{Option='-m';               Description='设置分辨率（同 --mode）'; NeedsArg=$true}
        [PSCustomObject]@{Option='--rate';           Description='设置刷新率'; NeedsArg=$true}
        [PSCustomObject]@{Option='-r';               Description='设置刷新率（同 --rate）'; NeedsArg=$true}
        [PSCustomObject]@{Option='--refresh';        Description='设置刷新率（同 --rate）'; NeedsArg=$true}
        [PSCustomObject]@{Option='--pos';            Description='设置桌面位置'; NeedsArg=$true}
        [PSCustomObject]@{Option='-p';               Description='设置桌面位置（同 --pos）'; NeedsArg=$true}
        [PSCustomObject]@{Option='--rotate';         Description='旋转方向'; NeedsArg=$true; Args='normal|left|right|inverted'}
        [PSCustomObject]@{Option='--primary';        Description='设为主显示器'}
        [PSCustomObject]@{Option='--preferred';      Description='首选分辨率'}
        [PSCustomObject]@{Option='--off';            Description='关闭显示器'}
        [PSCustomObject]@{Option='--brightness';     Description='设置亮度'; NeedsArg=$true}
        [PSCustomObject]@{Option='--gamma';          Description='伽马校正 R:G:B'; NeedsArg=$true}
        [PSCustomObject]@{Option='--reflect';        Description='镜像翻转'; NeedsArg=$true; Args='x y xy'}
        [PSCustomObject]@{Option='--left-of';        Description='放在左侧'; NeedsArg=$true}
        [PSCustomObject]@{Option='--right-of';       Description='放在右侧'; NeedsArg=$true}
        [PSCustomObject]@{Option='--above';          Description='放在上方'; NeedsArg=$true}
        [PSCustomObject]@{Option='--below';          Description='放在下方'; NeedsArg=$true}
        [PSCustomObject]@{Option='--same-as';        Description='镜像（同位置）'; NeedsArg=$true}
        [PSCustomObject]@{Option='--json';           Description='JSON 输出'}
        [PSCustomObject]@{Option='--auto';           Description='启用显示器（首选分辨率）'}
        [PSCustomObject]@{Option='--dry-run';        Description='模拟操作，不实际更改'}
        [PSCustomObject]@{Option='--dryrun';         Description='模拟操作（同 --dry-run）'}
        [PSCustomObject]@{Option='--identify';       Description='闪屏识别显示器'}
        [PSCustomObject]@{Option='--noprimary';     Description='清除所有主显示器标记'}
        [PSCustomObject]@{Option='--save-profile';  Description='保存当前配置为存档'; NeedsArg=$true}
        [PSCustomObject]@{Option='--load-profile';  Description='加载指定存档'; NeedsArg=$true}
        [PSCustomObject]@{Option='--list-profiles'; Description='列出所有存档'}
        [PSCustomObject]@{Option='--delete-profile';Description='删除指定存档'; NeedsArg=$true}
        [PSCustomObject]@{Option='--listproviders';  Description='列出 GPU 适配器'}
        [PSCustomObject]@{Option='--listmonitors';  Description='列出带编号的显示器'}
        [PSCustomObject]@{Option='--listactivemonitors'; Description='列出活动显示器（同 --listmonitors）'}
    )

    # 过滤：只返回尚未使用的参数 + 匹配当前输入
    $used = $words | Where-Object { $_ -like '-*' } | ForEach-Object { $_.Split('=')[0] }
    $opts | Where-Object {
        $_.Option -notin $used -and $_.Option -like "$wordToComplete*"
    } | ForEach-Object {
        $completionText = $_.Option
        if ($_.Args) {
            # 参数值可枚举的直接补全第一个值
            $completionText = "$($_.Option) $($_.Args.Split('|')[0])"
        }
        [System.Management.Automation.CompletionResult]::new(
            $completionText,
            $_.Option,
            'ParameterName',
            $_.Description
        )
    }
}
