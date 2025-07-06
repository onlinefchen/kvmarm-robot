#!/bin/bash
# GitHub MCP 工具安装和配置脚本

echo "🚀 设置 GitHub MCP 工具..."

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装。请先安装 Docker："
    echo "   macOS: brew install --cask docker"
    echo "   Ubuntu: sudo apt-get install docker.io"
    echo "   或访问 https://docs.docker.com/get-docker/"
    exit 1
fi

echo "✅ Docker 已安装"

# 检查是否有 GitHub Personal Access Token
if [ -z "$GITHUB_TOKEN" ]; then
    echo "⚠️  请设置 GITHUB_TOKEN 环境变量"
    echo "   1. 访问 https://github.com/settings/tokens"
    echo "   2. 创建新的 Personal Access Token"
    echo "   3. 选择必要的权限（repo, actions, issues, pull_requests）"
    echo "   4. 运行: export GITHUB_TOKEN=your_token_here"
    echo ""
    echo "或者在 .env 文件中添加："
    echo "GITHUB_TOKEN=your_token_here"
    exit 1
fi

echo "✅ GitHub Token 已配置"

# 拉取 GitHub MCP Server
echo "📥 拉取 GitHub MCP Server Docker 镜像..."
docker pull ghcr.io/github/github-mcp-server:latest

if [ $? -eq 0 ]; then
    echo "✅ GitHub MCP Server 镜像下载成功"
else
    echo "❌ GitHub MCP Server 镜像下载失败"
    exit 1
fi

# 测试 GitHub MCP Server
echo "🧪 测试 GitHub MCP Server..."
docker run -i --rm \
    -e GITHUB_PERSONAL_ACCESS_TOKEN="$GITHUB_TOKEN" \
    -e GITHUB_TOOLSETS="repos,issues,pull_requests,actions" \
    ghcr.io/github/github-mcp-server --version

echo ""
echo "🎉 GitHub MCP 工具安装完成！"
echo ""
echo "📋 使用方法："
echo "1. 基本用法："
echo "   docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN=\"\$GITHUB_TOKEN\" ghcr.io/github/github-mcp-server"
echo ""
echo "2. 启用特定工具集："
echo "   docker run -i --rm \\"
echo "     -e GITHUB_PERSONAL_ACCESS_TOKEN=\"\$GITHUB_TOKEN\" \\"
echo "     -e GITHUB_TOOLSETS=\"repos,issues,pull_requests,actions\" \\"
echo "     ghcr.io/github/github-mcp-server"
echo ""
echo "3. 只读模式："
echo "   docker run -i --rm \\"
echo "     -e GITHUB_PERSONAL_ACCESS_TOKEN=\"\$GITHUB_TOKEN\" \\"
echo "     -e GITHUB_READ_ONLY=true \\"
echo "     ghcr.io/github/github-mcp-server"
echo ""
echo "🔗 项目仓库: https://github.com/onlinefchen/kvmarm-robot"