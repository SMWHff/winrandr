# winrandr Bash 自动补全
# 安装: source scripts/completions.bash
# 或放入 /etc/bash_completion.d/winrandr

_winrandr_completions() {
    local cur prev words cword
    _init_completion -n = || return

    # 需要显示器名的参数
    local rotate_args="normal inverted left right"
    local reflect_args="normal x y xy"
    local orientation_args="normal inverted left right 0 1 2 3"

    # 判断前一个参数类型
    case $prev in
        --output|-o|--left-of|--right-of|--above|--below|--same-as)
            # 从 --listmonitors 输出提取显示器名（无需 Python）
            local displays
            displays=$(winrandr --listmonitors 2>/dev/null | sed -n 's/^ *[0-9]\{1,\}: +[*]*\([^ ]*\) .*/\1/p')
            if [ -n "$displays" ]; then
                COMPREPLY=($(compgen -W "$displays" -- "$cur"))
                return
            fi
            COMPREPLY=($(compgen -W "DISPLAY1 DISPLAY2 DISPLAY3 DISPLAY4" -- "$cur"))
            return
            ;;
        --save-profile|--load-profile|--delete-profile)
            # 从 --list-profiles --json 输出提取存档名
            local profiles
            profiles=$(winrandr --list-profiles --json 2>/dev/null | sed -n 's/.*"name": "\([^"]*\)".*/\1/p')
            if [ -n "$profiles" ]; then
                COMPREPLY=($(compgen -W "$profiles" -- "$cur"))
                return
            fi
            return
            ;;
        --rotate)
            COMPREPLY=($(compgen -W "$rotate_args" -- "$cur"))
            return
            ;;
        --reflect)
            COMPREPLY=($(compgen -W "$reflect_args" -- "$cur"))
            return
            ;;
        --orientation)
            COMPREPLY=($(compgen -W "$orientation_args" -- "$cur"))
            return
            ;;
        --screen)
            COMPREPLY=($(compgen -W "0 1 2" -- "$cur"))
            return
            ;;
        --mode|-m|-s|--size)
            # --mode 提示但不做动态补全（数据量大）
            return
            ;;
        --rate|-r|--refresh|--brightness|--pos|-p|--gamma)
            return
            ;;
    esac

    # 顶层选项
    local opts="
        --help -q --query --current --listmodes --listproviders
        --listmonitors --listactivemonitors --prop --properties
        --json --verbose -v --version --dry-run --dryrun
        --output -o --mode -m -s --size --rate -r --refresh
        --pos -p --rotate --orientation --primary --preferred
        --off --auto --brightness --gamma --reflect
        --left-of --right-of --above --below --same-as
        --identify --noprimary -x -y --screen --nograb --listactivemonitors
        --save-profile --load-profile --list-profiles --delete-profile
    "

    COMPREPLY=($(compgen -W "$opts" -- "$cur"))
}

complete -F _winrandr_completions winrandr winrandr.exe
