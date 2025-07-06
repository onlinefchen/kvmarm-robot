import os
import subprocess
import logging
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime
import git


logger = logging.getLogger(__name__)


class RepositoryManager:
    def __init__(self, base_path: str = "kvmarm"):
        self.base_path = Path(base_path)
        self.repo_path = self.base_path / "git" / "0.git"
        self.repo_url = "https://lore.kernel.org/kvmarm/0"
        
    def ensure_repository_updated(self) -> Path:
        """确保仓库存在并更新到最新状态"""
        if self.repo_path.exists() and self._is_git_repository(self.repo_path):
            print("✅ 仓库已存在，执行更新...")
            self._update_repository()
        else:
            print("📥 下载仓库...")
            self._clone_repository()
        
        return self.repo_path
    
    def _is_git_repository(self, path: Path) -> bool:
        """检查是否为有效的git仓库"""
        try:
            repo = git.Repo(path)
            return True
        except:
            return False
    
    def _clone_repository(self):
        """克隆邮件列表仓库"""
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        cmd = [
            "git", "clone", "--mirror",
            self.repo_url,
            str(self.repo_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to clone repository: {result.stderr}")
        
        logger.info(f"Repository cloned to {self.repo_path}")
    
    def _update_repository(self):
        """更新现有仓库"""
        cmd = ["git", "remote", "update"]
        
        result = subprocess.run(
            cmd, 
            cwd=str(self.repo_path),
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to update repository: {result.stderr}")
        
        logger.info("Repository updated successfully")
    
    def get_commits_in_range(
        self,
        since: datetime,
        until: datetime,
        branch: str = "master"
    ) -> List[git.Commit]:
        """获取指定时间范围内的commits"""
        repo = git.Repo(self.repo_path)
        
        commits = []
        for commit in repo.iter_commits(branch):
            commit_date = datetime.fromtimestamp(commit.committed_date)
            
            if commit_date < since:
                break  # 由于commits是按时间倒序的，可以提前终止
            
            if since <= commit_date <= until:
                commits.append(commit)
        
        return commits
    
    def get_recent_commits(self, limit: int = 100, branch: str = "master") -> List[git.Commit]:
        """获取最近的N个commits"""
        repo = git.Repo(self.repo_path)
        
        commits = []
        for i, commit in enumerate(repo.iter_commits(branch)):
            if i >= limit:
                break
            commits.append(commit)
        
        return commits
    
    def get_commit_content(self, commit_hash: str) -> str:
        """获取commit的完整内容"""
        repo = git.Repo(self.repo_path)
        
        try:
            commit = repo.commit(commit_hash)
            # 获取commit的原始邮件内容
            return commit.message
        except:
            logger.error(f"Failed to get content for commit {commit_hash}")
            return ""


def run_command(cmd: str, cwd: Optional[str] = None) -> subprocess.CompletedProcess:
    """执行shell命令的辅助函数"""
    return subprocess.run(
        cmd.split(),
        capture_output=True,
        text=True,
        cwd=cwd
    )


def test_repository_management():
    """测试仓库管理功能"""
    print("🧪 测试仓库管理...")
    
    manager = RepositoryManager()
    
    # 测试仓库克隆/更新
    repo_path = manager.ensure_repository_updated()
    
    assert repo_path.exists()
    assert manager._is_git_repository(repo_path)
    
    # 测试获取最近的commits
    recent_commits = manager.get_recent_commits(limit=5)
    print(f"   获取到 {len(recent_commits)} 个最近的commits")
    
    for commit in recent_commits[:3]:
        print(f"   📧 {commit.hexsha[:8]} - {commit.summary[:50]}...")
    
    print("✅ 仓库管理测试通过")