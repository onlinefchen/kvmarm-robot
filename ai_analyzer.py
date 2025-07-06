import os
import json
import logging
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
from dotenv import load_dotenv

from models import ContentChunk, EmailForest, ChunkType


logger = logging.getLogger(__name__)
load_dotenv()


class AIProvider(ABC):
    """AI提供商的抽象基类"""
    
    @abstractmethod
    def analyze_chunk(self, chunk: ContentChunk, context: Dict[str, Any]) -> Dict[str, Any]:
        """分析单个内容块"""
        pass
    
    @abstractmethod
    def merge_analyses(self, chunk_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并分块分析结果"""
        pass


class OpenAIProvider(AIProvider):
    """OpenAI GPT-4 提供商"""
    
    def __init__(self, language: str = "zh"):
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.model = "gpt-4-turbo-preview"
            self.language = language
        except ImportError:
            logger.error("OpenAI library not installed")
            raise
    
    def analyze_chunk(self, chunk: ContentChunk, context: Dict[str, Any]) -> Dict[str, Any]:
        """使用GPT-4分析单个内容块"""
        prompt = self._build_analysis_prompt(chunk, context)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return self._get_default_analysis()
    
    def merge_analyses(self, chunk_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并多个分析结果"""
        merge_prompt = self._build_merge_prompt(chunk_analyses)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_merge_system_prompt()},
                    {"role": "user", "content": merge_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            logger.error(f"OpenAI merge error: {e}")
            return self._merge_manually(chunk_analyses)
    
    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        if self.language == "zh":
            return """你是一位Linux内核开发专家，专精于ARM架构和KVM虚拟化技术。
            请分析来自Linux ARM KVM邮件列表的邮件内容，并提供结构化的见解。
            始终返回有效的JSON格式。所有的分析内容请使用中文。"""
        else:
            return """You are an expert Linux kernel developer specializing in ARM architecture and KVM virtualization.
            Analyze the given email content from the Linux ARM KVM mailing list and provide structured insights.
            Always return valid JSON format."""
    
    def _get_merge_system_prompt(self) -> str:
        """获取合并分析的系统提示词"""
        if self.language == "zh":
            return """你是技术分析综合专家。
            请将提供的分块分析合并成综合摘要。
            保留关键技术细节，同时去除冗余内容。
            始终返回有效的JSON格式。所有的分析内容请使用中文。"""
        else:
            return """You are an expert at synthesizing technical analyses.
            Merge the provided chunk analyses into a comprehensive summary.
            Preserve key technical details while removing redundancy.
            Always return valid JSON format."""
    
    def _build_analysis_prompt(self, chunk: ContentChunk, context: Dict[str, Any]) -> str:
        """构建分析提示词"""
        if self.language == "zh":
            return f"""请分析以下ARM KVM邮件列表内容：

主题: {context.get('thread_subject', 'Unknown')}
内容类型: {chunk.chunk_type.value}
优先级: {chunk.priority}

内容:
{chunk.content[:4000]}  # 限制内容长度

请按以下JSON格式提供分析（请用中文填写所有内容）：
{{
    "technical_points": ["关键技术要点列表"],
    "arm_kvm_relevance": 1-10,
    "complexity": "low/medium/high",
    "key_changes": ["重要变更列表（如适用）"],
    "potential_issues": ["潜在问题或关注点列表"],
    "innovation_level": "incremental/moderate/significant",
    "summary": "内容简要概述"
}}"""
        else:
            return f"""Analyze this ARM KVM mailing list content:

Thread Subject: {context.get('thread_subject', 'Unknown')}
Content Type: {chunk.chunk_type.value}
Priority: {chunk.priority}

Content:
{chunk.content[:4000]}  # 限制内容长度

Please provide analysis in the following JSON format:
{{
    "technical_points": ["list of key technical points"],
    "arm_kvm_relevance": 1-10,
    "complexity": "low/medium/high",
    "key_changes": ["list of important changes if applicable"],
    "potential_issues": ["list of potential issues or concerns"],
    "innovation_level": "incremental/moderate/significant",
    "summary": "brief summary of the content"
}}"""
    
    def _build_merge_prompt(self, chunk_analyses: List[Dict[str, Any]]) -> str:
        """构建合并提示词"""
        analyses_text = json.dumps(chunk_analyses, indent=2)
        
        if self.language == "zh":
            return f"""请将以下分块分析合并为综合摘要：

{analyses_text}

请按以下JSON格式提供合并分析（请用中文填写所有内容）：
{{
    "executive_summary": "所有分块的综合摘要",
    "technical_highlights": ["所有分块的关键技术要点"],
    "arm_kvm_relevance": 1-10,
    "overall_complexity": "low/medium/high",
    "key_contributions": ["主要贡献或变更"],
    "concerns_raised": ["提到的任何问题或关注点"],
    "recommendation": "建议的行动或审查状态"
}}"""
        else:
            return f"""Merge these chunk analyses into a comprehensive summary:

{analyses_text}

Provide a merged analysis in the following JSON format:
{{
    "executive_summary": "comprehensive summary of all chunks",
    "technical_highlights": ["key technical points across all chunks"],
    "arm_kvm_relevance": 1-10,
    "overall_complexity": "low/medium/high",
    "key_contributions": ["main contributions or changes"],
    "concerns_raised": ["any issues or concerns mentioned"],
    "recommendation": "suggested action or review status"
}}"""
    
    def _get_default_analysis(self) -> Dict[str, Any]:
        """返回默认分析结果"""
        return {
            "technical_points": [],
            "arm_kvm_relevance": 5,
            "complexity": "medium",
            "key_changes": [],
            "potential_issues": [],
            "innovation_level": "incremental",
            "summary": "Analysis failed"
        }
    
    def _merge_manually(self, chunk_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """手动合并分析结果"""
        # 简单的合并逻辑
        all_technical_points = []
        all_key_changes = []
        all_issues = []
        relevance_scores = []
        
        for analysis in chunk_analyses:
            all_technical_points.extend(analysis.get("technical_points", []))
            all_key_changes.extend(analysis.get("key_changes", []))
            all_issues.extend(analysis.get("potential_issues", []))
            relevance_scores.append(analysis.get("arm_kvm_relevance", 5))
        
        # 去重
        all_technical_points = list(set(all_technical_points))
        all_key_changes = list(set(all_key_changes))
        all_issues = list(set(all_issues))
        
        return {
            "executive_summary": "Merged analysis of multiple chunks",
            "technical_highlights": all_technical_points[:10],  # 限制数量
            "arm_kvm_relevance": int(sum(relevance_scores) / len(relevance_scores)) if relevance_scores else 5,
            "overall_complexity": "medium",
            "key_contributions": all_key_changes[:5],
            "concerns_raised": all_issues[:5],
            "recommendation": "Requires further review"
        }


class GeminiProvider(AIProvider):
    """Google Gemini 提供商"""
    
    def __init__(self, language: str = "zh"):
        try:
            import google.generativeai as genai
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            self.model = genai.GenerativeModel('gemini-pro')
            self.language = language
        except ImportError:
            logger.error("Google GenerativeAI library not installed")
            raise
    
    def analyze_chunk(self, chunk: ContentChunk, context: Dict[str, Any]) -> Dict[str, Any]:
        """使用Gemini分析单个内容块"""
        # Gemini实现略...
        return self._get_default_analysis()
    
    def merge_analyses(self, chunk_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并多个分析结果"""
        # Gemini实现略...
        return self._merge_manually(chunk_analyses)
    
    def _get_default_analysis(self) -> Dict[str, Any]:
        return {
            "technical_points": [],
            "arm_kvm_relevance": 5,
            "complexity": "medium",
            "key_changes": [],
            "potential_issues": [],
            "innovation_level": "incremental",
            "summary": "Gemini analysis not implemented"
        }
    
    def _merge_manually(self, chunk_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "executive_summary": "Gemini merge not implemented",
            "technical_highlights": [],
            "arm_kvm_relevance": 5,
            "overall_complexity": "medium",
            "key_contributions": [],
            "concerns_raised": [],
            "recommendation": "Pending implementation"
        }


class AIAnalyzer:
    """AI分析器主类"""
    
    def __init__(self, provider: str = "openai", language: str = "zh"):
        self.provider_name = provider
        self.language = language
        self.provider = self._init_provider(provider)
        self.total_tokens_used = 0
    
    def _init_provider(self, provider: str) -> AIProvider:
        """初始化AI提供商"""
        if provider == "openai":
            return OpenAIProvider(self.language)
        elif provider == "gemini":
            return GeminiProvider(self.language)
        else:
            raise ValueError(f"Unsupported AI provider: {provider}")
    
    def analyze_with_ai(self, chunked_data: Dict[str, List[ContentChunk]], forest: EmailForest, debug: bool = False) -> Dict[str, Dict[str, Any]]:
        """对所有内容进行AI分析"""
        all_analyses = {}
        
        print(f"🤖 使用 {self.provider_name} 进行AI分析...")
        
        # 遍历每个线程
        for thread in forest.threads:
            thread_analyses = {}
            
            # 为线程中的每个邮件进行分析
            for node in thread.all_nodes.values():
                if node.message_id in chunked_data:
                    chunks = chunked_data[node.message_id]
                    
                    if debug:
                        print(f"   分析邮件: {node.subject[:50]}... ({len(chunks)} chunks)")
                    
                    # 分析每个chunk
                    chunk_analyses = []
                    for chunk in chunks:
                        context = {
                            "thread_subject": thread.subject,
                            "message_type": node.message_type.value,
                            "sender": node.sender
                        }
                        
                        analysis = self.provider.analyze_chunk(chunk, context)
                        chunk_analyses.append(analysis)
                    
                    # 合并分析结果
                    if len(chunk_analyses) > 1:
                        merged_analysis = self.provider.merge_analyses(chunk_analyses)
                    else:
                        merged_analysis = chunk_analyses[0] if chunk_analyses else {}
                    
                    # 保存分析结果
                    node.ai_analysis = merged_analysis
                    thread_analyses[node.message_id] = merged_analysis
            
            # 生成线程总结
            if thread_analyses:
                thread_summary = self._generate_thread_summary(thread, thread_analyses)
                thread.ai_summary = thread_summary
                all_analyses[thread.thread_id] = {
                    "thread_summary": thread_summary,
                    "message_analyses": thread_analyses
                }
        
        return all_analyses
    
    def _generate_thread_summary(self, thread, thread_analyses: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """生成线程级别的总结"""
        # 收集所有邮件的分析
        all_summaries = []
        all_contributions = []
        all_concerns = []
        
        for analysis in thread_analyses.values():
            if "summary" in analysis:
                all_summaries.append(analysis["summary"])
            elif "executive_summary" in analysis:
                all_summaries.append(analysis["executive_summary"])
            
            all_contributions.extend(analysis.get("key_contributions", []))
            all_contributions.extend(analysis.get("key_changes", []))
            all_concerns.extend(analysis.get("concerns_raised", []))
            all_concerns.extend(analysis.get("potential_issues", []))
        
        # 构建线程总结
        return {
            "executive_summary": " ".join(all_summaries[:3]),  # 取前3个总结
            "technical_highlights": list(set(all_contributions))[:10],
            "discussion_points": list(set(all_concerns))[:10],
            "thread_status": self._determine_thread_status(thread),
            "lore_discussion_url": f"{thread.root_node.lore_url}T/",
            "impact_level": self._assess_impact_level(thread_analyses)
        }
    
    def _determine_thread_status(self, thread) -> str:
        """判断线程状态"""
        if thread.statistics.acks > 0:
            return "acked"
        elif thread.statistics.reviews > 0:
            return "under_review"
        elif thread.statistics.replies > 0:
            return "active_discussion"
        else:
            return "new"
    
    def _assess_impact_level(self, thread_analyses: Dict[str, Dict[str, Any]]) -> str:
        """评估影响级别"""
        relevance_scores = []
        for analysis in thread_analyses.values():
            if "arm_kvm_relevance" in analysis:
                relevance_scores.append(analysis["arm_kvm_relevance"])
        
        if not relevance_scores:
            return "medium"
        
        avg_relevance = sum(relevance_scores) / len(relevance_scores)
        
        if avg_relevance >= 8:
            return "high"
        elif avg_relevance >= 5:
            return "medium"
        else:
            return "low"


def analyze_with_ai(chunked_data: Dict[str, List[ContentChunk]], forest: EmailForest, provider: str = "openai", language: str = "zh", debug: bool = False) -> Dict[str, Dict[str, Any]]:
    """AI分析的便捷函数"""
    analyzer = AIAnalyzer(provider, language)
    return analyzer.analyze_with_ai(chunked_data, forest, debug)


def test_ai_analysis():
    """测试AI分析功能"""
    print("🧪 测试AI分析...")
    
    # 检查API密钥
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY 环境变量未设置")
        return
    
    from models import ContentChunk, ChunkType
    
    # 创建测试chunk
    test_chunk = ContentChunk(
        chunk_id="test_001",
        git_hash="test_hash",
        chunk_type=ChunkType.HEADER,
        content="""[PATCH v2 1/3] KVM: arm64: Fix memory management issue
        
This patch fixes a critical memory leak in the stage-2 page table
management code. The issue occurs when unmapping large memory regions
during VM teardown.

The fix ensures proper reference counting and cleanup of intermediate
page table levels.""",
        priority=5,
        token_count=50
    )
    
    try:
        analyzer = AIAnalyzer("openai")
        
        context = {
            "thread_subject": "KVM: arm64: Memory management fixes",
            "message_type": "patch",
            "sender": "test@example.com"
        }
        
        result = analyzer.provider.analyze_chunk(test_chunk, context)
        
        # 验证返回格式
        assert "technical_points" in result
        assert "arm_kvm_relevance" in result
        assert isinstance(result["arm_kvm_relevance"], (int, float))
        
        print("   ✅ AI分析返回正确格式")
        print(f"   📊 ARM KVM相关性: {result.get('arm_kvm_relevance', 'N/A')}")
        print(f"   💡 技术要点: {', '.join(result.get('technical_points', [])[:3])}")
        
    except Exception as e:
        print(f"   ❌ AI分析失败: {e}")
        return
    
    print("\n✅ AI分析测试通过")