#!/bin/bash
# 修正Git提交作者信息的脚本

echo "🔧 修正最近3个提交的作者信息..."
echo "作者: Chen Feng <connect.fengchen@gmail.com>"
echo ""
echo "⚠️  警告: 这将重写Git历史记录！"
echo "按Ctrl+C取消，或按Enter继续..."
read

# 修正最近3个提交
git rebase -i HEAD~3 --exec 'git commit --amend --author="Chen Feng <connect.fengchen@gmail.com>" --no-edit'

echo ""
echo "✅ 作者信息已修正"
echo ""
echo "📌 接下来需要强制推送到远程仓库："
echo "git push --force-with-lease origin main"
echo ""
echo "⚠️  注意: 强制推送会覆盖远程仓库的历史记录"