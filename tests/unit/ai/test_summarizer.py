"""
文档摘要生成器测试

测试 Story 1.8 的实现
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.ai.summarizer import (
    DocumentSummarizer,
    SummaryResult,
    SummaryStrategy,
    batch_summarize_documents
)


class TestSummaryResult:
    """摘要结果测试"""

    def test_create_summary_result(self):
        """测试创建摘要结果"""
        result = SummaryResult(
            document_id=1,
            summary="This is a test summary",
            key_points=["Point 1", "Point 2"],
            keywords=["test", "summary"],
            confidence=0.85
        )

        assert result.document_id == 1
        assert result.summary == "This is a test summary"
        assert len(result.key_points) == 2
        assert len(result.keywords) == 2
        assert result.confidence == 0.85

    def test_to_dict(self):
        """测试转换为字典"""
        result = SummaryResult(
            document_id=1,
            summary="Test summary"
        )

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict['document_id'] == 1
        assert result_dict['summary'] == "Test summary"
        assert 'key_points' in result_dict
        assert 'keywords' in result_dict

    def test_to_json(self):
        """测试转换为JSON"""
        result = SummaryResult(
            document_id=1,
            summary="Test"
        )

        json_str = result.to_json()

        assert isinstance(json_str, str)
        assert '"document_id": 1' in json_str
        assert '"summary": "Test"' in json_str


class TestDocumentSummarizer:
    """文档摘要生成器测试"""

    @pytest.fixture
    def summarizer(self):
        """创建摘要生成器实例"""
        return DocumentSummarizer(
            strategy=SummaryStrategy.EXTRACTIVE,
            max_summary_length=300
        )

    def test_init_extractive(self):
        """测试抽取式摘要初始化"""
        summarizer = DocumentSummarizer(strategy=SummaryStrategy.EXTRACTIVE)

        assert summarizer.strategy == SummaryStrategy.EXTRACTIVE
        assert summarizer.model is None
        assert summarizer.tokenizer is None

    @patch('src.ai.summarizer.AutoTokenizer')
    @patch('src.ai.summarizer.AutoModelForSeq2SeqLM')
    def test_init_abstractive(self, mock_model, mock_tokenizer):
        """测试生成式摘要初始化"""
        summarizer = DocumentSummarizer(
            strategy=SummaryStrategy.ABSTRACTIVE,
            model_name="test-model"
        )

        assert summarizer.strategy == SummaryStrategy.ABSTRACTIVE

    def test_extractive_summarize(self, summarizer):
        """测试抽取式摘要"""
        content = """
        人工智能是计算机科学的一个分支。它致力于开发能够模拟人类智能的系统。
        机器学习是人工智能的一个子领域。深度学习是机器学习的一个重要方向。
        神经网络是深度学习的基础。卷积神经网络在图像识别中表现出色。
        自然语言处理是另一个重要的AI领域。它使计算机能够理解和生成人类语言。
        """

        summary = summarizer._extractive_summarize(content)

        assert isinstance(summary, str)
        assert len(summary) > 0
        assert len(summary) <= summarizer.max_summary_length + 3  # +3 for "..."

    def test_summarize_short_content(self, summarizer):
        """测试短内容摘要"""
        content = "这是一段很短的内容。"

        result = summarizer.summarize(1, content)

        assert isinstance(result, SummaryResult)
        assert result.document_id == 1
        assert len(result.summary) > 0

    def test_summarize_with_cache(self, summarizer):
        """测试缓存功能"""
        content = "测试缓存功能。" * 20

        # 第一次摘要
        result1 = summarizer.summarize(1, content)

        # 第二次应该使用缓存
        result2 = summarizer.summarize(2, content)  # 不同ID但内容相同

        # 摘要内容应该相同
        assert result1.summary == result2.summary
        assert result2.document_id == 2  # ID应该更新

    def test_split_sentences(self, summarizer):
        """测试分句功能"""
        text = "这是第一句。这是第二句！这是第三句？这是第四句"

        sentences = summarizer._split_sentences(text)

        assert len(sentences) >= 3
        assert "这是第一句" in sentences[0]

    def test_extract_keywords(self, summarizer):
        """测试关键词提取"""
        content = """
        Python是一种流行的编程语言。Python支持多种编程范式。
        Python有丰富的库和框架。许多开发者喜欢使用Python。
        """

        keywords = summarizer._extract_keywords(content, top_k=5)

        assert isinstance(keywords, list)
        assert len(keywords) <= 5
        # Python应该是高频词 (可能是整个短语或单独的python)
        assert any('python' in kw.lower() for kw in keywords)

    def test_extract_key_points(self, summarizer):
        """测试关键点提取"""
        content = """
        第一个重要的观点是关于AI的发展。
        第二个观点讨论了机器学习的应用。
        第三个观点分析了深度学习的优势。
        第四个观点探讨了NLP的未来。
        """

        key_points = summarizer._extract_key_points(content, max_points=3)

        assert isinstance(key_points, list)
        assert len(key_points) <= 3

    def test_extract_entities(self, summarizer):
        """测试实体识别"""
        content = """
        Microsoft Corporation is a technology company.
        Bill Gates founded Microsoft in Redmond.
        The company operates in many countries.
        """

        entities = summarizer._extract_entities(content)

        assert isinstance(entities, dict)
        assert 'persons' in entities
        assert 'organizations' in entities
        assert 'locations' in entities

    def test_score_sentences(self, summarizer):
        """测试句子评分"""
        sentences = [
            "这是开头的重要句子包含关键词AI。",
            "这是中间的句子。",
            "这是结尾的重要句子包含关键词机器学习。"
        ]
        full_text = " ".join(sentences)

        scores = summarizer._score_sentences(sentences, full_text)

        assert len(scores) == len(sentences)
        assert all(isinstance(score, float) for score in scores.values())
        # 开头句子应该有较高分数
        assert scores[sentences[0]] > 0

    def test_clear_cache(self, summarizer):
        """测试清空缓存"""
        summarizer.summarize(1, "测试内容")
        assert summarizer.get_cache_size() > 0

        summarizer.clear_cache()

        assert summarizer.get_cache_size() == 0

    def test_hash_content(self, summarizer):
        """测试内容哈希"""
        content1 = "测试内容"
        content2 = "测试内容"
        content3 = "不同内容"

        hash1 = summarizer._hash_content(content1)
        hash2 = summarizer._hash_content(content2)
        hash3 = summarizer._hash_content(content3)

        assert hash1 == hash2
        assert hash1 != hash3


class TestBatchSummarize:
    """批量摘要测试"""

    def test_batch_summarize_documents(self):
        """测试批量摘要生成"""
        summarizer = DocumentSummarizer(strategy=SummaryStrategy.EXTRACTIVE)

        documents = [
            {
                'id': 1,
                'content': "这是第一篇文档的内容。" * 10,
                'metadata': {'file_path': '/doc1.txt'}
            },
            {
                'id': 2,
                'content': "这是第二篇文档的内容。" * 10,
                'metadata': {'file_path': '/doc2.txt'}
            },
            {
                'id': 3,
                'content': "这是第三篇文档的内容。" * 10,
                'metadata': {'file_path': '/doc3.txt'}
            }
        ]

        results = batch_summarize_documents(
            summarizer,
            documents,
            save_to_db=False
        )

        assert len(results) == 3
        assert all(isinstance(r, SummaryResult) for r in results)
        assert results[0].document_id == 1
        assert results[1].document_id == 2
        assert results[2].document_id == 3

    def test_batch_summarize_with_db(self):
        """测试批量摘要并保存到数据库"""
        summarizer = DocumentSummarizer(strategy=SummaryStrategy.EXTRACTIVE)
        mock_db = Mock()

        documents = [
            {
                'id': 1,
                'content': "测试文档内容。" * 10
            }
        ]

        results = batch_summarize_documents(
            summarizer,
            documents,
            save_to_db=True,
            db_manager=mock_db
        )

        assert len(results) == 1
        mock_db.save_summary.assert_called_once()


@pytest.mark.integration
class TestSummarizerIntegration:
    """集成测试"""

    def test_real_world_document(self):
        """测试真实文档摘要"""
        summarizer = DocumentSummarizer(
            strategy=SummaryStrategy.EXTRACTIVE,
            max_summary_length=200
        )

        content = """
        人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，
        它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。
        该领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。

        机器学习是人工智能的一个子领域，它使计算机具有学习能力。
        机器学习算法可以从数据中自动分析获得规律，并利用规律对未知数据进行预测。

        深度学习是机器学习的一个分支，它试图模仿人脑的神经网络结构。
        深度学习在图像识别、语音识别、自然语言处理等领域取得了突破性进展。

        自然语言处理（NLP）是人工智能的另一个重要分支。
        它研究如何让计算机理解和生成人类语言，包括文本分类、情感分析、机器翻译等任务。
        """

        result = summarizer.summarize(1, content)

        assert isinstance(result, SummaryResult)
        assert len(result.summary) > 0
        assert len(result.summary) <= 200 + 3
        assert len(result.key_points) > 0
        assert len(result.keywords) > 0

        # 验证关键词
        assert any(keyword in ['人工智能', 'ai', '机器学习', '深度学习'] for keyword in result.keywords)

    @pytest.mark.skip(reason="Requires transformers installation")
    def test_abstractive_summarization(self):
        """测试生成式摘要"""
        summarizer = DocumentSummarizer(
            strategy=SummaryStrategy.ABSTRACTIVE,
            model_name="google/mt5-small"
        )

        content = "这是一个测试文档。" * 50

        result = summarizer.summarize(1, content)

        assert isinstance(result, SummaryResult)
        assert len(result.summary) > 0
