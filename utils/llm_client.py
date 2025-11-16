"""
LLM客户端，用于调用大语言模型API（优先使用 Gemini，其次回退 OpenAI）
"""
import os
from dotenv import load_dotenv

load_dotenv()

# 尝试加载 Gemini SDK
_genai_available = False
try:
    import google.generativeai as genai
    _genai_available = True
except Exception:
    _genai_available = False

# 尝试加载 OpenAI SDK
_openai_available = False
try:
    from openai import OpenAI
    _openai_available = True
except Exception:
    _openai_available = False


class LLMClient:
    """统一的 LLM 客户端，自动选择 Gemini 或 OpenAI"""

    def __init__(self, model: str | None = None):
        """
        初始化 LLM 客户端。
        选择策略：
        - 如果配置了 GEMINI_API_KEY 且 Gemini SDK 可用：使用 Gemini（默认模型 gemini-1.5-flash）
        - 否则，如果配置了 OPENAI_API_KEY 且 OpenAI SDK 可用：使用 OpenAI（默认模型 gpt-3.5-turbo）
        - 否则抛错，由上层进入演示模式
        """
        self.provider = None
        self.model = None

        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")

        if gemini_key and _genai_available:
            self.provider = "gemini"
            genai.configure(api_key=gemini_key)
            self.model = model or os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        elif openai_key and _openai_available:
            self.provider = "openai"
            self.client = OpenAI(api_key=openai_key)
            self.model = model or os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        else:
            raise ValueError("未检测到可用的 LLM 配置：请设置 GEMINI_API_KEY 或 OPENAI_API_KEY 并安装相应 SDK")

    def generate_response(self, prompt: str, system_prompt: str | None = None, max_tokens: int = 200, temperature: float = 0.7) -> str:
        """
        生成通用文本回复（封装两家接口差异）。
        - Gemini：使用 GenerativeModel.generate_content，将 system_prompt 与用户 prompt 合并为单次请求（保持简洁稳定）
        - OpenAI：使用 chat.completions.create，传入 system 与 user 两条消息
        """
        if self.provider == "gemini":
            # 将系统提示与用户问题组合；Gemini 也支持 system_instruction，但简单合并更兼容
            full_prompt = prompt if not system_prompt else f"{system_prompt}\n\n{prompt}"
            try:
                model = genai.GenerativeModel(self.model)
                resp = model.generate_content(
                    full_prompt,
                    generation_config={
                        "temperature": temperature,
                        "max_output_tokens": max_tokens,
                    },
                )
                # 从 candidates 中取首条文本
                text = getattr(resp, "text", None)
                if text:
                    return text.strip()
                # 兼容部分响应结构
                if resp and hasattr(resp, "candidates") and resp.candidates:
                    parts = getattr(resp.candidates[0], "content", None)
                    if parts and hasattr(parts, "parts") and parts.parts:
                        return str(parts.parts[0].text).strip()
                raise Exception("Gemini 响应为空或解析失败")
            except Exception as e:
                print(f"[LLM ERROR] Gemini API 调用失败: {e}")
                raise Exception(f"Gemini API 调用失败: {str(e)}")

        elif self.provider == "openai":
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                print(f"[LLM ERROR] OpenAI API 调用失败: {e}")
                raise Exception(f"OpenAI API 调用失败: {str(e)}")

        else:
            raise RuntimeError("未知的 LLM 提供方")

    # 下面的业务方法均复用 generate_response，逻辑保持不变

    def generate_one_sentence_answer(self, question, subject_name, subject_description, subject_persona):
        system_prompt = f"""你是一个{subject_name}领域的专家。
学科特点：{subject_description}
人设风格：{subject_persona}

请用一句话（30-50字）从{subject_name}角度回答用户的问题。

重要要求：
1. 必须给出简单而具体的回答，避免抽象空泛
2. 使用该学科的核心概念、理论或具体案例
3. 回答要有实质内容，不要只是描述问题
4. 符合该学科的特点和人设风格
"""
        prompt = f"问题：{question}\n\n请从{subject_name}角度用一句话给出简单而具体的回答。"
        return self.generate_response(prompt, system_prompt, max_tokens=150, temperature=0.7)

    def generate_deep_answer(self, question, subject_name, subject_description, subject_persona, context=""):
        system_prompt = f"""你是一个{subject_name}领域的专家。
学科特点：{subject_description}
人设风格：{subject_persona}

请从{subject_name}角度给出详细的回答（3-5句话，100-200字）。

要求：
1. 深入分析，提供具体的理论、概念或案例
2. 逻辑清晰，层次分明
3. 实用性强，能给用户带来启发
4. 符合学科特点和人设风格
"""
        if context:
            prompt = f"背景：{context}\n\n问题：{question}\n\n请从{subject_name}角度给出深入分析。"
        else:
            prompt = f"问题：{question}\n\n请从{subject_name}角度给出深入分析。"
        return self.generate_response(prompt, system_prompt, max_tokens=400, temperature=0.7)

    def generate_suggestions(self, question, answer, subject_name):
        system_prompt = f"""你是一个{subject_name}领域的专家。
请基于用户的问题和你的回答，生成3个相关的后续问题。

要求：
1. 问题要有深度，能引导用户深入思考
2. 与{subject_name}学科密切相关
3. 每个问题一行，不要编号
"""
        prompt = f"原问题：{question}\n\n我的回答：{answer}\n\n请生成3个相关的后续问题（每行一个，不要编号）。"
        response = self.generate_response(prompt, system_prompt, max_tokens=200, temperature=0.8)
        suggestions = [s.strip() for s in response.split('\n') if s.strip() and not s.strip().startswith('#')]
        return suggestions[:3]

    def generate_viewpoint(self, question, subject_name, subject_description, subject_persona):
        system_prompt = f"""你是一个{subject_name}领域的专家。
学科特点：{subject_description}
人设风格：{subject_persona}

请用一句话（20-30字）表达{subject_name}对这个问题的核心观点。
"""
        prompt = f"问题：{question}\n\n请用一句话表达{subject_name}的核心观点。"
        return self.generate_response(prompt, system_prompt, max_tokens=80, temperature=0.7)

    def generate_arguments(self, question, subject_name, subject_description, subject_persona):
        system_prompt = f"""你是一个{subject_name}领域的专家。
学科特点：{subject_description}
人设风格：{subject_persona}

请从{subject_name}角度提供3个支持论据（每条30-50字）。
"""
        prompt = f"问题：{question}\n\n请提供3个{subject_name}角度的论据（每行一个，不要编号）。"
        response = self.generate_response(prompt, system_prompt, max_tokens=300, temperature=0.7)
        arguments = [a.strip() for a in response.split('\n') if a.strip() and not a.strip().startswith('#')]
        return arguments[:3]

    def generate_pk_statement(self, question, subject_name, subject_description, subject_persona, history, round_num, turn):
        if round_num == 1:
            style_hint = "请阐述你的基本观点和理论依据"
        elif round_num == 2:
            style_hint = "请深入论证并适当回应对方观点"
        else:
            style_hint = "请总结你的核心主张并升华观点"
        system_prompt = f"""你是一个{subject_name}领域的专家，正在与其他学科专家进行学术辩论。
学科特点：{subject_description}
人设风格：{subject_persona}

当前是第{round_num}轮第{turn}次发言。{style_hint}。
"""
        history_text = ""
        if history:
            history_text = "\n历史对话：\n" + "\n".join([f"{h['name']}: {h['content']}" for h in history[-6:]])
        prompt = f"辩论问题：{question}\n{history_text}\n\n请以{subject_name}专家的身份发表一句观点（30-60字）。"
        return self.generate_response(prompt, system_prompt, max_tokens=120, temperature=0.8)
