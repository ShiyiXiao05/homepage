#!/usr/bin/env bash
# 在线编辑器 blog/admin.html 的 GitHub PAT 管理工具。
#
# token 存放在 macOS 钥匙串（Keychain）里，不再以明文文件留在仓库目录。
# 需要一枚 fine-grained PAT：仅限本仓库、权限 Contents: Read and write。
#
#   ./scripts/admin-token.sh store   # 粘贴/更新 token（输入不回显）
#   ./scripts/admin-token.sh open    # 用钥匙串里的 token 打开编辑器
#   ./scripts/admin-token.sh copy    # 复制 token 到剪贴板（手动粘进编辑器输入框）
#   ./scripts/admin-token.sh show    # 查看钥匙串里是否已存有 token
#   ./scripts/admin-token.sh forget  # 从钥匙串删除
#
# 非交互写入（例如 CI 或自动化）：HOMEPAGE_PAT=xxx ./scripts/admin-token.sh store
set -euo pipefail

SERVICE="${HOMEPAGE_PAT_SERVICE:-shiyixiao-homepage-admin}"
ACCOUNT="${HOMEPAGE_PAT_ACCOUNT:-$USER}"
PAGE="https://shiyixiao05.github.io/homepage/blog/admin.html"

usage() {
  sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'
  exit "${1:-0}"
}

exists() {
  security find-generic-password -s "$SERVICE" -a "$ACCOUNT" >/dev/null 2>&1
}

read_token() {
  if [ -n "${HOMEPAGE_PAT:-}" ]; then
    printf '%s' "$HOMEPAGE_PAT"
    return
  fi
  if [ ! -t 0 ]; then
    # 管道输入：printf '%s' "$PAT" | ./scripts/admin-token.sh store
    cat
    return
  fi
  printf '粘贴 fine-grained PAT（输入不回显，回车确认）：' >&2
  local tok
  read -rs tok
  printf '\n' >&2
  printf '%s' "$tok"
}

case "${1:-}" in
  store)
    tok="$(read_token)"
    if [ -z "$tok" ]; then
      echo "✗ token 为空，已取消" >&2
      exit 1
    fi
    security add-generic-password -U -s "$SERVICE" -a "$ACCOUNT" -w "$tok"
    unset tok
    echo "✓ 已写入钥匙串：service=$SERVICE account=$ACCOUNT"
    echo "  现在可以删除 admin-token.local / admin-link.local 这两个明文文件了。"
    ;;
  open)
    if ! exists; then
      echo "✗ 钥匙串里还没有 token，先跑：$0 store" >&2
      exit 1
    fi
    tok="$(security find-generic-password -s "$SERVICE" -a "$ACCOUNT" -w)"
    # 编辑器页面把 #t=<token> 读进 localStorage 后立刻从地址栏抹掉，token 不会进服务器日志
    open "${PAGE}#t=${tok}"
    unset tok
    ;;
  copy)
    if ! exists; then
      echo "✗ 钥匙串里还没有 token，先跑：$0 store" >&2
      exit 1
    fi
    security find-generic-password -s "$SERVICE" -a "$ACCOUNT" -w | pbcopy
    echo "✓ token 已复制到剪贴板"
    ;;
  show)
    if exists; then
      echo "✓ 钥匙串中已存有 token（service=$SERVICE account=$ACCOUNT）"
    else
      echo "✗ 钥匙串中没有 token；$0 store 可写入"
      exit 1
    fi
    ;;
  forget)
    if exists; then
      security delete-generic-password -s "$SERVICE" -a "$ACCOUNT" >/dev/null
      echo "✓ 已从钥匙串删除"
    else
      echo "· 钥匙串里本来就没有 token"
    fi
    ;;
  ""|-h|--help|help)
    usage 0
    ;;
  *)
    echo "未知子命令：$1" >&2
    usage 2
    ;;
esac
