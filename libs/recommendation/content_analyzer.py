"""日记内容分析模块 — 关键词提取、话题聚类、情感分析"""

import re
from collections import Counter
from libs.database import db_manager


class ContentAnalyzer:
    """分析日记内容，提取关键词和话题"""

    # 常见停用词
    STOP_WORDS = set([
        "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一",
        "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着",
        "没有", "看", "好", "自己", "这", "他", "她", "它", "们", "那", "些",
        "这个", "那个", "什么", "怎么", "怎么样", "因为", "所以", "但是",
        "可以", "能", "觉得", "知道", "想", "做", "来", "还", "让", "给",
        "被", "把", "从", "对", "过", "与", "关于", "或者", "如果", "虽然",
        "然后", "已经", "正在", "将", "可能", "应该", "一定", "比较",
        "今天", "昨天", "明天", "今天", "早上", "晚上", "下午", "上午",
        "真的", "挺", "太", "非常", "特别", "一点", "有点", "很多",
        "哈哈", "嗯", "啊", "哦", "吧", "呢", "吗", "呀",
    ])

    def __init__(self):
        # 尝试加载 jieba
        try:
            import jieba
            self.jieba = jieba
            self._use_jieba = True
        except ImportError:
            self._use_jieba = False

    def analyze_entry(self, entry_id: int, content: str, category: str = ""):
        """分析一篇日记的内容"""
        keywords = self.extract_keywords(content)
        categorized = self._categorize_keywords(keywords)
        db_manager.save_keywords(keywords[:10], entry_id, category)

    def extract_keywords(self, text: str, top_n: int = 20) -> list[str]:
        """提取关键词"""
        if self._use_jieba:
            return self._extract_jieba(text, top_n)
        else:
            return self._extract_simple(text, top_n)

    def _extract_jieba(self, text: str, top_n: int) -> list[str]:
        """使用 jieba 分词提取关键词"""
        import jieba.analyse
        keywords = jieba.analyse.extract_tags(text, topK=top_n, withWeight=False)
        return [kw for kw in keywords if kw not in self.STOP_WORDS and len(kw) >= 2]

    def _extract_simple(self, text: str, top_n: int) -> list[str]:
        """简单分词提取关键词（不依赖 jieba）"""
        # 移除标点符号
        cleaned = re.sub(r'[^一-鿿\w]', ' ', text)

        # 简单 2-gram 提取
        words = []
        chars = list(cleaned.replace(" ", ""))

        # 取双字词
        for i in range(len(chars) - 1):
            bigram = chars[i] + chars[i + 1]
            if bigram not in self.STOP_WORDS and re.match(r'[一-鿿]{2}', bigram):
                words.append(bigram)

        # 也取单个中文字
        for c in chars:
            if re.match(r'[一-鿿]', c) and c not in self.STOP_WORDS:
                words.append(c)

        counter = Counter(words)
        return [w for w, _ in counter.most_common(top_n)]

    def _categorize_keywords(self, keywords: list[str]) -> str:
        """简单分类关键词"""
        person_words = {"爸爸", "妈妈", "朋友", "同事", "老板", "老师", "同学", "家人"}
        place_words = {"公司", "家", "学校", "商场", "公园", "餐厅", "医院", "超市"}
        emotion_words = {"开心", "难过", "焦虑", "兴奋", "放松", "担心", "高兴", "生气"}

        counts = {"人物": 0, "地点": 0, "情感": 0}
        for kw in keywords:
            if kw in person_words:
                counts["人物"] += 1
            elif kw in place_words:
                counts["地点"] += 1
            elif kw in emotion_words:
                counts["情感"] += 1

        if max(counts.values()) == 0:
            return "其他"
        return max(counts, key=counts.get)

    def get_topic_clusters(self, days: int = 90) -> list[dict]:
        """获取话题聚类"""
        top_keywords = db_manager.get_top_keywords(days, limit=30)

        if not top_keywords:
            return []

        # 简单的共现分析
        clusters = []
        for kw_data in top_keywords[:10]:
            clusters.append({
                "topic": kw_data["keyword"],
                "frequency": kw_data["freq"],
                "related_entries": self._find_entries_by_keyword(kw_data["keyword"], days),
            })

        return clusters

    def _find_entries_by_keyword(self, keyword: str, days: int) -> list[int]:
        """查找包含某关键词的日记 ID"""
        conn = db_manager.get_connection()
        try:
            rows = conn.execute(
                "SELECT DISTINCT entry_id FROM keyword_tracking "
                "WHERE keyword=? AND tracked_date >= date('now', ?)",
                (keyword, f"-{days} days")
            ).fetchall()
            return [r["entry_id"] for r in rows]
        finally:
            conn.close()

    def find_similar_entries(self, entry_id: int, limit: int = 3) -> list[dict]:
        """查找与某篇日记话题相似的日记"""
        current_keywords = set(db_manager.get_keywords_by_entry(entry_id))
        if not current_keywords:
            return []

        # 找到共享关键词的日记
        all_keywords = {}
        for kw in current_keywords:
            entries = self._find_entries_by_keyword(kw, 365)
            for eid in entries:
                if eid != entry_id:
                    all_keywords[eid] = all_keywords.get(eid, 0) + 1

        # 按相似度排序
        sorted_entries = sorted(all_keywords.items(), key=lambda x: x[1], reverse=True)
        similar = []
        for eid, score in sorted_entries[:limit]:
            entry = db_manager.get_entry(eid)
            if entry:
                entry["similarity_score"] = score
                similar.append(entry)

        return similar

    def get_review_worthy(self, days_ago: int = 365) -> list[dict]:
        """找到值得回顾的日记"""
        from datetime import date, timedelta
        target_date = (date.today() - timedelta(days=days_ago)).isoformat()

        entries = db_manager.get_entries_by_date(target_date)
        if not entries:
            return []

        # 筛选值得回顾的（字数多或情绪强烈的）
        worthy = []
        for entry in entries:
            score = 0
            # 字数分
            wc = entry.get("word_count", 0)
            if wc > 500: score += 3
            elif wc > 200: score += 2
            elif wc > 50: score += 1

            # 情绪强烈分
            if entry.get("mood") in ["excited", "sad", "anxious"]:
                score += 2

            if score >= 2:
                entry["review_score"] = score
                worthy.append(entry)

        return sorted(worthy, key=lambda x: x.get("review_score", 0), reverse=True)
