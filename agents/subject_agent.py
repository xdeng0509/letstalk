"""
学科Agent，负责从特定学科角度回答问题
"""
from utils.llm_client import LLMClient


class SubjectAgent:
    """学科Agent类"""
    
    def __init__(self, subject_info, llm_client=None):
        """
        初始化学科Agent
        
        Args:
            subject_info: 学科信息字典，包含name, icon, description, persona
            llm_client: LLM客户端，如果为None则创建新实例
        """
        self.subject_info = subject_info
        self.name = subject_info["name"]
        self.icon = subject_info.get("icon", "📚")
        self.description = subject_info["description"]
        self.persona = subject_info["persona"]
        
        # 如果llm_client为None，保持None（演示模式），并记录提示
        # 如果不为None，使用传入的client
        self.llm_client = llm_client
        self.last_used_demo = False
        self.last_error_message = None
        if self.llm_client is None:
            print(f"[LLM DEMO] SubjectAgent initialized without LLM for subject='{self.name}'")
    
    def answer_one_sentence(self, question):
        """
        用一句话回答问题（简单而具体）
        
        Args:
            question: 用户问题
        
        Returns:
            str: 一句话回答
        """
        if self.llm_client is None:
            # 演示模式：返回简单具体的模拟回答
            return self._get_demo_answer(question)
        
        try:
            return self.llm_client.generate_one_sentence_answer(
                question=question,
                subject_name=self.name,
                subject_description=self.description,
                subject_persona=self.persona
            )
        except Exception as e:
            # 记录LLM调用失败日志并回退到演示答案
            print(f"[LLM ERROR] answer_one_sentence failed for subject='{self.name}': {e}")
            return self._get_demo_answer(question)
    
    def _get_demo_answer(self, question):
        """
        生成演示模式的简单具体回答
        
        Args:
            question: 用户问题
        
        Returns:
            str: 简单具体的回答
        """
        # 根据不同学科生成简单而具体的回答
        if "心理学" in self.name:
            return "这可能与多巴胺奖励机制有关，大脑在获得即时满足时会释放多巴胺，形成正反馈循环。"
        elif "经济学" in self.name:
            return "根据边际效用递减原理，随着消费量增加，每增加一单位带来的满足感会逐渐降低。"
        elif "社会学" in self.name:
            return "这反映了社会化过程中的群体认同需求，个体通过从众行为获得归属感和安全感。"
        elif "生物学" in self.name:
            return "从进化角度看，这是人类祖先在生存竞争中形成的适应性行为模式，写入了基因记忆。"
        elif "哲学" in self.name:
            return "从存在主义视角，这体现了人追求意义的本质需求，是自我实现的一种表现形式。"
        elif "历史学" in self.name:
            return "历史上类似现象在19世纪工业革命时期就出现过，当时人们面对技术变革也有相似反应。"
        elif "物理学" in self.name:
            return "这类似于热力学第二定律，系统趋向于从有序走向无序，需要持续能量输入才能维持秩序。"
        elif "文学" in self.name:
            return "就像卡夫卡笔下的异化主题，现代人在复杂环境中常感到自我与世界的疏离。"
        elif "传播学" in self.name:
            return "根据使用与满足理论，人们主动选择媒介内容来满足自己的心理和社交需求。"
        elif "艺术学" in self.name:
            return "这种现象在印象派绘画中有体现——打破传统规则，追求主观感受和即时印象的表达。"
        else:
            return f"从{self.name}的核心概念出发，这个现象可以用具体的理论框架来解释和分析。"
    
    def get_display_name(self):
        """
        获取显示名称（带图标）
        
        Returns:
            str: 显示名称
        """
        return f"{self.icon} {self.name}"
    
    def deep_answer(self, question, context=""):
        """
        生成深度回答（3-5句话）
        
        Args:
            question: 用户问题
            context: 对话上下文
        
        Returns:
            str: 详细回答
        """
        # 标记本次调用是否使用了演示回退
        self.last_used_demo = False
        
        if self.llm_client is None:
            # 演示模式
            print(f"[LLM DEMO] deep_answer using demo for subject='{self.name}'")
            self.last_used_demo = True
            return self._get_demo_deep_answer(question)
        
        try:
            ans = self.llm_client.generate_deep_answer(
                question=question,
                subject_name=self.name,
                subject_description=self.description,
                subject_persona=self.persona,
                context=context
            )
            self.last_used_demo = False
            return ans
        except Exception as e:
            self.last_error_message = str(e)
            print(f"[LLM ERROR] deep_answer failed for subject='{self.name}': {e}")
            self.last_used_demo = True
            return self._get_demo_deep_answer(question)
    
    def _get_demo_deep_answer(self, question):
        """生成演示模式的深度回答"""
        if "心理学" in self.name:
            return """从心理学角度深入分析，这个问题涉及多巴胺奖励回路的机制。当我们获得即时满足时，大脑会释放多巴胺，产生愉悦感。
            
这种正反馈会强化行为模式，让我们倾向于重复这个行为。但长期来看，过度依赖即时满足会降低大脑对奖励的敏感度，需要更强的刺激才能获得同样的快感。

建议通过"延迟满足"训练来提升自控力，这是心理韧性的重要组成部分。"""
        elif "经济学" in self.name:
            return """从经济学视角，这符合"边际效用递减"的经典原理。每增加一单位的消费，带来的额外满足感会逐渐降低。

理性的经济人会在边际成本等于边际收益时做出最优决策。但现实中，人们常受"锚定效应"和"损失厌恶"的影响，做出非理性选择。

因此，建立明确的成本-收益分析框架，能帮助我们做出更理性的决策。"""
        else:
            return f"""从{self.name}的角度深入分析，这个问题有多个层面值得探讨。

首先，我们需要理解其核心机制和内在逻辑。其次，要考虑历史演变和现实背景的影响。

最后，从实践角度看，我们可以采取一些具体的策略来应对这个问题。"""
    
    def generate_suggestions(self, question, answer):
        """
        生成建议问题
        
        Args:
            question: 原问题
            answer: 回答内容
        
        Returns:
            list: 建议问题列表
        """
        if self.llm_client is None:
            # 演示模式
            print(f"[LLM DEMO] generate_suggestions using demo for subject='{self.name}'")
            self.last_used_demo = True
            return [
                f"从{self.name}角度，如何将这个理论应用到实际生活中？",
                f"能否举一个{self.name}领域的具体案例来说明？",
                f"这个观点在{self.name}发展史上有哪些重要争论？"
            ]
        
        try:
            suggestions = self.llm_client.generate_suggestions(
                question=question,
                answer=answer,
                subject_name=self.name
            )
            self.last_used_demo = False
            return suggestions
        except Exception as e:
            print(f"[LLM ERROR] generate_suggestions failed for subject='{self.name}': {e}")
            self.last_used_demo = True
            return [
                f"从{self.name}角度，如何将这个理论应用到实际生活中？",
                f"能否举一个{self.name}领域的具体案例来说明？",
                f"这个观点在{self.name}发展史上有哪些重要争论？"
            ]
    
    def generate_viewpoint(self, question):
        """
        生成PK观点（一句话核心立场）
        
        Args:
            question: 问题
        
        Returns:
            str: 核心观点
        """
        if self.llm_client is None:
            print(f"[LLM DEMO] generate_viewpoint using demo for subject='{self.name}'")
            return self._get_demo_viewpoint(question)
        
        try:
            return self.llm_client.generate_viewpoint(
                question=question,
                subject_name=self.name,
                subject_description=self.description,
                subject_persona=self.persona
            )
        except Exception as e:
            print(f"[LLM ERROR] generate_viewpoint failed for subject='{self.name}': {e}")
            return self._get_demo_viewpoint(question)
    
    def _get_demo_viewpoint(self, question):
        """生成演示模式的PK观点"""
        viewpoints = {
            "心理学": "这本质上是大脑神经机制和认知模式的产物",
            "经济学": "这是理性选择和资源优化配置的结果",
            "社会学": "这反映了社会结构和文化规范对个体的塑造",
            "生物学": "这是进化过程中形成的生存适应策略",
            "哲学": "这涉及存在意义和价值判断的根本问题"
        }
        return viewpoints.get(self.name, f"从{self.name}角度看，这需要系统性分析")
    
    def generate_arguments(self, question):
        """
        生成PK论据（3个要点）
        
        Args:
            question: 问题
        
        Returns:
            list: 论据列表
        """
        if self.llm_client is None:
            print(f"[LLM DEMO] generate_arguments using demo for subject='{self.name}'")
            return self._get_demo_arguments(question)
        
        try:
            return self.llm_client.generate_arguments(
                question=question,
                subject_name=self.name,
                subject_description=self.description,
                subject_persona=self.persona
            )
        except Exception as e:
            print(f"[LLM ERROR] generate_arguments failed for subject='{self.name}': {e}")
            return self._get_demo_arguments(question)
    
    def _get_demo_arguments(self, question):
        """生成演示模式的PK论据"""
        if "心理学" in self.name:
            return [
                "神经科学研究证实，这与前额叶皮层的决策功能直接相关",
                "大量心理实验数据支持这个解释模型",
                "临床案例显示，相关干预措施能有效改善这种状况"
            ]
        elif "经济学" in self.name:
            return [
                "历史数据表明，市场规律在此发挥了关键作用",
                "博弈论模型能完美解释这种行为模式",
                "成本-收益分析框架为此提供了理论支撑"
            ]
        elif "社会学" in self.name:
            return [
                "社会调查数据显示，这是普遍的群体现象",
                "文化人类学研究发现，不同社会有相似模式",
                "社会网络分析揭示了其中的互动机制"
            ]
        else:
            return [
                f"{self.name}的核心理论为此提供了解释框架",
                f"大量实证研究支持这个{self.name}观点",
                f"从{self.name}发展史看，这个现象由来已久"
            ]
    
    def generate_pk_statement(self, question, history, round_num=1, turn=1):
        """
        生成PK对话中的一句发言
        
        Args:
            question: 辩论问题
            history: 历史对话记录
            round_num: 当前轮次
            turn: 当前回合（在本轮中的第几次发言）
        
        Returns:
            str: 一句发言内容（30-60字）
        """
        if self.llm_client is None:
            print(f"[LLM DEMO] generate_pk_statement using demo for subject='{self.name}'")
            return self._get_demo_pk_statement(question, round_num, turn)
        
        try:
            return self.llm_client.generate_pk_statement(
                question=question,
                subject_name=self.name,
                subject_description=self.description,
                subject_persona=self.persona,
                history=history,
                round_num=round_num,
                turn=turn
            )
        except Exception as e:
            print(f"[LLM ERROR] generate_pk_statement failed for subject='{self.name}': {e}")
            return self._get_demo_pk_statement(question, round_num, turn)
    
    def _get_demo_pk_statement(self, question, round_num, turn):
        """生成演示模式的PK发言"""
        
        # 根据学科和回合生成不同的发言
        statements_templates = {
            "心理学": [
                "从认知心理学角度，这涉及大脑的决策机制和奖励系统的相互作用。",
                "心理实验表明，人们在这种情况下会受到认知偏差的影响。",
                "神经科学研究发现，这与前额叶皮层和边缘系统的功能密切相关。",
                "我们需要关注个体差异，不同性格类型的人反应模式完全不同。",
                "临床数据显示，这种行为模式可以通过认知行为疗法得到改善。"
            ],
            "经济学": [
                "从经济学视角，这是典型的理性选择问题，涉及成本收益分析。",
                "市场数据表明，人们会根据边际效用来做出决策。",
                "博弈论模型可以完美解释这种策略性行为。",
                "历史案例显示，制度设计在这个问题上起到关键作用。",
                "从资源配置效率看，这反映了市场机制的内在逻辑。"
            ],
            "社会学": [
                "从社会学角度，这是社会结构和文化规范共同作用的结果。",
                "社会调查数据显示，这种现象具有明显的群体性特征。",
                "我们不能忽视社会化过程对个体行为的深刻影响。",
                "跨文化比较研究发现，不同社会在这方面存在显著差异。",
                "社会网络分析揭示了人际互动在其中扮演的重要角色。"
            ],
            "生物学": [
                "从进化生物学看，这是自然选择长期作用的产物。",
                "基因研究表明，遗传因素在这个问题上有不可忽视的影响。",
                "生理机制显示，激素和神经递质调节着这种行为。",
                "比较动物学研究发现，类似现象在其他物种中也存在。",
                "从适应性角度，这种特征曾经具有生存优势。"
            ],
            "哲学": [
                "从哲学本体论看，这涉及存在与意识的根本关系。",
                "伦理学视角下，我们需要思考价值判断的标准是什么。",
                "认识论告诉我们，我们对这个问题的理解本身就值得反思。",
                "存在主义强调，个体的自由选择和责任才是核心。",
                "从历史唯物主义看，社会存在决定社会意识。"
            ]
        }
        
        # 根据轮次和回合选择不同风格的发言
        if round_num == 1:
            # 第一轮：阐述基本观点
            templates = statements_templates.get(self.name, [
                f"从{self.name}角度分析，这个问题有其独特的解释框架。",
                f"{self.name}研究为此提供了重要的理论支持。",
                f"我们需要用{self.name}的方法论来审视这个现象。",
                f"大量{self.name}实证研究验证了这个观点。",
                f"从{self.name}发展史看，这是一个经典问题。"
            ])
        elif round_num == 2:
            # 第二轮：深入论证和反驳
            templates = [
                f"我必须指出，仅从其他角度看是不够全面的，{self.name}提供了更深层的解释。",
                f"最新的{self.name}研究证据强有力地支持了我的观点。",
                f"让我们回到问题的本质，{self.name}揭示了根本原因。",
                f"虽然其他视角有一定道理，但{self.name}的解释更具说服力。",
                f"实践证明，{self.name}的方法在解决这类问题上最为有效。"
            ]
        else:
            # 第三轮：总结和升华
            templates = [
                f"综合来看，{self.name}视角为这个问题提供了最系统的解决方案。",
                f"我们应该认识到，{self.name}方法论的优势在于其科学性和可验证性。",
                f"从长远发展看，{self.name}的洞察对未来具有重要指导意义。",
                f"让我们用{self.name}的智慧来化解这个难题。",
                f"最终，{self.name}为我们指明了正确的方向。"
            ]
        
        # 根据turn选择合适的模板
        index = (turn - 1) % len(templates)
        return templates[index]

