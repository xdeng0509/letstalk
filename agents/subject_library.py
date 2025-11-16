"""
学科库管理
"""
import json
import os
import random
from pathlib import Path


class SubjectLibrary:
    """学科库类"""
    
    def __init__(self, config_path=None):
        """
        初始化学科库
        
        Args:
            config_path: 配置文件路径，默认使用项目内的config/subjects.json
        """
        if config_path is None:
            # 获取项目根目录
            current_dir = Path(__file__).parent.parent
            config_path = current_dir / "config" / "subjects.json"
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.hot_subjects = self.config.get("hot_subjects", [])
        self.cold_subjects = self.config.get("cold_subjects", [])
        self.crossover_subjects = self.config.get("crossover_subjects", [])
        
        # 构建学科关键词映射表
        self._build_keyword_mapping()
    
    def _build_keyword_mapping(self):
        """构建学科关键词映射表"""
        self.subject_keywords = {
            "心理学": ["心理", "情绪", "感受", "想法", "性格", "行为", "焦虑", "压力", "快乐", "幸福", "动机", "记忆", "认知", "潜意识"],
            "经济学": ["钱", "价格", "成本", "收益", "投资", "消费", "市场", "经济", "贸易", "财富", "理性", "选择", "资源", "效用"],
            "社会学": ["社会", "群体", "关系", "文化", "习俗", "规范", "阶层", "角色", "互动", "身份", "从众", "流行", "潮流"],
            "生物学": ["基因", "进化", "遗传", "生存", "繁殖", "适应", "本能", "身体", "大脑", "神经", "激素", "生理"],
            "哲学": ["意义", "本质", "存在", "真理", "价值", "道德", "伦理", "自由", "选择", "人生", "世界", "认识"],
            "历史学": ["历史", "过去", "传统", "古代", "演变", "发展", "起源", "变迁", "朝代", "事件", "经验", "教训"],
            "物理学": ["力量", "能量", "运动", "速度", "平衡", "规律", "系统", "秩序", "混乱", "熵", "守恒"],
            "文学": ["故事", "叙事", "情节", "隐喻", "象征", "表达", "艺术", "文字", "作品", "诗", "小说"],
            "传播学": ["信息", "媒体", "传播", "沟通", "舆论", "影响", "受众", "传媒", "网络", "社交"],
            "艺术学": ["美", "审美", "艺术", "创作", "表现", "风格", "色彩", "形式", "设计", "视觉"],
            "数学": ["数字", "计算", "逻辑", "概率", "统计", "模型", "规律", "推理", "证明"],
            "计算机科学": ["算法", "程序", "代码", "数据", "网络", "智能", "系统", "技术", "自动化"],
            "教育学": ["学习", "教育", "知识", "培养", "成长", "能力", "方法", "教学", "课程"],
            "法学": ["法律", "规则", "权利", "义务", "正义", "公平", "责任", "法规", "制度"],
            "医学": ["健康", "疾病", "治疗", "身体", "症状", "医疗", "养生", "保健", "病"],
        }
    
    def get_smart_subjects(self, question, count=3, diversity=0.3):
        """
        基于问题内容智能选择学科（非纯随机）
        
        Args:
            question: 用户问题
            count: 返回的学科数量，默认3个
            diversity: 多样性系数(0-1)，越大越随机，越小越相关。默认0.3
        
        Returns:
            list: 学科列表，按相关性和多样性混合排序
        """
        all_subjects = self.hot_subjects + self.cold_subjects + self.crossover_subjects
        
        # 计算每个学科与问题的相关性分数
        scored_subjects = []
        for subject in all_subjects:
            score = self._calculate_relevance(question, subject)
            scored_subjects.append((subject, score))
        
        # 按分数排序
        scored_subjects.sort(key=lambda x: x[1], reverse=True)
        
        # 混合策略：部分选择高相关度的，部分随机选择
        high_relevance_count = max(1, int(count * (1 - diversity)))
        random_count = count - high_relevance_count
        
        # 选择高相关度的学科
        selected = [s[0] for s in scored_subjects[:high_relevance_count]]
        
        # 从剩余学科中随机选择
        remaining = [s[0] for s in scored_subjects[high_relevance_count:]]
        if remaining and random_count > 0:
            selected.extend(random.sample(remaining, min(random_count, len(remaining))))
        
        # 如果还不够数量，补充高分学科
        if len(selected) < count:
            for subject, score in scored_subjects:
                if subject not in selected:
                    selected.append(subject)
                    if len(selected) >= count:
                        break
        
        # 打乱顺序（保持随机性）
        random.shuffle(selected)
        
        return selected[:count]
    
    def _calculate_relevance(self, question, subject):
        """
        计算学科与问题的相关性分数
        
        Args:
            question: 用户问题
            subject: 学科信息
        
        Returns:
            float: 相关性分数
        """
        score = 0.0
        subject_name = subject["name"]
        
        # 1. 关键词匹配（主要依据）
        if subject_name in self.subject_keywords:
            keywords = self.subject_keywords[subject_name]
            for keyword in keywords:
                if keyword in question:
                    score += 2.0  # 每匹配一个关键词加2分
        
        # 2. 学科名称直接出现
        if subject_name in question:
            score += 5.0
        
        # 3. 学科描述相关性（弱相关）
        description = subject.get("description", "")
        description_keywords = description[:20]  # 取描述的前20个字作为特征
        if any(word in question for word in description_keywords if len(word) > 1):
            score += 1.0
        
        # 4. 添加随机扰动（保持一定随机性）
        score += random.uniform(0, 1.5)
        
        return score
    
    def get_random_subjects(self, count=3, hot_ratio=0.5):
        """
        随机获取学科组合（冷门+热门）
        
        Args:
            count: 返回的学科数量，默认3个
            hot_ratio: 热门学科占比，默认0.5（即一半热门一半冷门）
        
        Returns:
            list: 学科列表，每个学科包含name, icon, description, persona
        """
        hot_count = max(1, int(count * hot_ratio))
        cold_count = count - hot_count
        
        # 从热门学科中随机选择
        selected_hot = random.sample(self.hot_subjects, min(hot_count, len(self.hot_subjects)))
        
        # 从冷门学科中随机选择
        selected_cold = random.sample(self.cold_subjects, min(cold_count, len(self.cold_subjects)))
        
        # 如果数量不够，从跨界学科中补充
        selected = selected_hot + selected_cold
        if len(selected) < count:
            remaining = count - len(selected)
            available_crossover = [s for s in self.crossover_subjects if s not in selected]
            if available_crossover:
                selected.extend(random.sample(available_crossover, min(remaining, len(available_crossover))))
        
        # 打乱顺序
        random.shuffle(selected)
        
        return selected[:count]
    
    def get_subject_by_name(self, name):
        """
        根据名称获取学科信息
        
        Args:
            name: 学科名称
        
        Returns:
            dict: 学科信息，如果不存在返回None
        """
        all_subjects = self.hot_subjects + self.cold_subjects + self.crossover_subjects
        for subject in all_subjects:
            if subject["name"] == name:
                return subject
        return None
    
    def get_all_subjects(self):
        """
        获取所有学科
        
        Returns:
            dict: 包含所有学科的字典
        """
        return {
            "hot": self.hot_subjects,
            "cold": self.cold_subjects,
            "crossover": self.crossover_subjects
        }

