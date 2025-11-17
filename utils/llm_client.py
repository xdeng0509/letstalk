"""
LLM客户端，统一适配 Gemini / OpenAI / 腾讯慧言（HuiYuan） OpenAPI
"""
import os
import json
import re
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# 可选 SDK
_genai_available = False
try:
    import google.generativeai as genai
    _genai_available = True
except Exception:
    _genai_available = False

_openai_available = False
try:
    from openai import OpenAI
    _openai_available = True
except Exception:
    _openai_available = False

import requests


class LLMClient:
    """统一的 LLM 客户端，支持三家提供方，通过环境变量选择：
    - LLM_PROVIDER: gemini | openai | huiyuan（默认自动探测）
    - 对应的 Key/模型：
      - GEMINI_API_KEY, GEMINI_MODEL
      - OPENAI_API_KEY, OPENAI_MODEL
      - HUIYUAN_API_KEY, HUIYUAN_MODEL, HUIYUAN_BASE_URL, HUIYUAN_PATH（默认 /v1/chat/completions）
    """

    def __init__(self, model: Optional[str] = None):
        self.provider = None
        self.model = None
        self.client = None
        self.base_url = None
        self.path = None
        self.headers = {}

        provider_hint = (os.getenv("LLM_PROVIDER") or "").strip().lower()

        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        huiyuan_key = os.getenv("HUIYUAN_API_KEY")
        huiyuan_base = os.getenv("HUIYUAN_BASE_URL")  # 例如：https://api.hunyuan.tencentcloudapi.com 或 OpenAI兼容网关
        huiyuan_path = os.getenv("HUIYUAN_PATH", "/v1/chat/completions")

        # 明确指定优先
        if provider_hint == "gemini" and gemini_key and _genai_available:
            self._init_gemini(gemini_key, model)
        elif provider_hint == "openai" and openai_key and _openai_available:
            self._init_openai(openai_key, model)
        elif provider_hint == "huiyuan" and huiyuan_key and huiyuan_base:
            self._init_huiyuan(huiyuan_key, huiyuan_base, huiyuan_path, model)
        else:
            # 自动探测：Gemini -> OpenAI -> HuiYuan
            if gemini_key and _genai_available:
                self._init_gemini(gemini_key, model)
            elif openai_key and _openai_available:
                self._init_openai(openai_key, model)
            elif huiyuan_key and huiyuan_base:
                self._init_huiyuan(huiyuan_key, huiyuan_base, huiyuan_path, model)
            else:
                raise ValueError("未检测到可用的 LLM 配置：请设置 GEMINI/OPENAI/HUIYUAN 的 API KEY 并安装相应 SDK/提供 base_url")

    def _init_gemini(self, api_key: str, model_override: Optional[str]):
        self.provider = "gemini"
        genai.configure(api_key=api_key)
        self.model = model_override or os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    def _init_openai(self, api_key: str, model_override: Optional[str]):
        self.provider = "openai"
        self.client = OpenAI(api_key=api_key)
        self.model = model_override or os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

    def _init_huiyuan(self, api_key: str, base_url: str, path: str, model_override: Optional[str]):
        self.provider = "huiyuan"
        self.base_url = base_url.rstrip("/")
        self.path = path if path.startswith("/") else f"/{path}"
        self.model = model_override or os.getenv("HUIYUAN_MODEL", "hunyuan-lite")
        # 采用 Bearer 风格头。如果慧言采用其他签名，可在此扩展。
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

    def _sanitize_output(self, text: str) -> str:
        """移除模型回答中的元提示/角色说明等冗余前缀，避免把提示词暴露给用户。
        规则：
        - 丢弃开头的句子，若包含以下关键词：
          "用户现在需要我"、"你要求我"、"系统提示"、"提示词"、"现在我需要"、"我将作为"、"请我以"
        - 丢弃以"作为…(身份|角度|学派)"开头的句子
        - 丢弃以"以…的(口吻|身份|视角)"开头的句子
        - 若清洗后文本为空，返回原文本（避免误删全部内容）
        """
        if not text:
            return text
        try:
            # 统一换行与空白
            txt = str(text).strip()
            # 句子级拆分（中英标点）
            sentences = re.split(r"(?<=[。！？!?\.])\s+", txt)
            cleaned = []
            for i, s in enumerate(sentences):
                s_strip = s.strip()
                if not s_strip:
                    continue
                # 元提示与角色自述检测
                meta_patterns = [
                    r"^好的[，,、]",  # "好的，用户现在需要我..."
                    r"用户(现在)?需要",
                    r"用户(问|要求|让)",
                    r"你要求我",
                    r"你让我",
                    r"系统提示",
                    r"提示词",
                    r"现在我需要",
                    r"我将作为",
                    r"请我以",
                    r"^从.*?角度[，,、]",  # "从行为经济学的角度，..."
                    r"^用一句话",  # "用一句话回答..."
                    r"^要求.*?字",  # "要求30-50字..."
                    r"^结合.*?概念",  # "结合核心概念..."
                    r"作为[^，。:：]*?(身份|角度|学派|专家)",
                    r"以[^，。:：]*?的(口吻|身份|视角|角度)",
                    r"具体有实质内容",
                    r"首先.*?得回忆",  # 思考链泄露特征
                    r"我得考虑",
                    r"或者考虑",
                    r"需要.*?更(基础|偏向|简单)",
                    r"理论(提到|认为)",
                    r"不过用户",
                    r"另外.*?认为"
                ]
                if any(re.search(p, s_strip) for p in meta_patterns):
                    continue
                cleaned.append(s_strip)
            result = "".join(cleaned).strip()
            return result if result else txt
        except Exception:
            return text

    def generate_response(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 200, temperature: float = 0.7) -> str:
        if self.provider == "gemini":
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
                text = getattr(resp, "text", None)
                if text:
                    return self._sanitize_output(text.strip())
                if resp and hasattr(resp, "candidates") and resp.candidates:
                    parts = getattr(resp.candidates[0], "content", None)
                    if parts and hasattr(parts, "parts") and parts.parts:
                        return self._sanitize_output(str(parts.parts[0].text).strip())
                raise Exception("Gemini 响应为空或解析失败")
            except Exception as e:
                print(f"[LLM ERROR] Gemini API 调用失败: {e}")
                raise Exception(f"Gemini API 调用失败: {str(e)}")

        if self.provider == "openai":
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
                return self._sanitize_output(response.choices[0].message.content.strip())
            except Exception as e:
                print(f"[LLM ERROR] OpenAI API 调用失败: {e}")
                raise Exception(f"OpenAI API 调用失败: {str(e)}")

        if self.provider == "huiyuan":
            # 默认按 OpenAI 兼容的 chat completions 格式构造
            url = f"{self.base_url}{self.path}"
            payload = {
                "model": self.model,
                "messages": ([{"role": "system", "content": system_prompt}] if system_prompt else []) + [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            try:
                resp = requests.post(url, headers=self.headers, data=json.dumps(payload), timeout=30)
                if resp.status_code >= 400:
                    raise Exception(f"HuiYuan API 调用失败: HTTP {resp.status_code} - {resp.text}")
                data = resp.json()
                # 兼容 OpenAI 风格响应
                if "choices" in data and data["choices"]:
                    msg = data["choices"][0].get("message", {})
                    content = msg.get("content", "")
                    # 注意：不使用reasoning_content，因为那是模型的思考过程，不应返回给用户
                    # 如果content为空，说明模型配置有问题或参数不正确
                    if not content:
                        raise Exception("模型返回内容为空，请检查模型配置或提示词设置")
                    return self._sanitize_output(content.strip())
                # 兼容文本字段
                if "text" in data:
                    return self._sanitize_output(str(data["text"]).strip())
                raise Exception("HuiYuan 响应解析失败：未找到 choices/message 或 text 字段")
            except Exception as e:
                print(f"[LLM ERROR] HuiYuan API 调用失败: {e}")
                raise Exception(f"HuiYuan API 调用失败: {str(e)}")

        raise RuntimeError("未知的 LLM 提供方")

    # 业务封装（复用 generate_response）
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
5. 禁止复述或引用上述提示与角色设定，不要出现“作为…/你要求我/系统提示”等表述
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
5. 禁止复述或引用上述提示与角色设定，不要出现“作为…/你要求我/系统提示”等表述
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
4. 禁止复述或引用上述提示与角色设定，不要出现“作为…/你要求我/系统提示”等表述
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

重要：禁止复述或引用提示与角色设定，不要出现“作为…/你要求我/系统提示”等表述
"""
        prompt = f"问题：{question}\n\n请用一句话表达{subject_name}的核心观点。"
        return self.generate_response(prompt, system_prompt, max_tokens=80, temperature=0.7)

    def generate_arguments(self, question, subject_name, subject_description, subject_persona):
        system_prompt = f"""你是一个{subject_name}领域的专家。
学科特点：{subject_description}
人设风格：{subject_persona}

请从{subject_name}角度提供3个支持论据（每条30-50字）。

重要：禁止复述或引用提示与角色设定，不要出现“作为…/你要求我/系统提示”等表述
"""
        prompt = f"问题：{question}\n\n请提供3个{subject_name}角度的论据（每行一个，不要编号）。"
        response = self.generate_response(prompt, system_prompt, max_tokens=300, temperature=0.7)
        arguments = [a.strip() for a in response.split('\n') if a.strip() and not a.strip().startswith('#')]
        return arguments[:3]

    def generate_pk_statement(self, question, subject_name, subject_description, subject_persona, history, round_num, turn):
        if round_num == 1:
            style_hint = "请阐述你的基本观点和理论依据"
        elif round_num == 2:
            style_hint = "请深入论证并针对对方的观点进行反驳或补充"
        else:
            style_hint = "请总结你的核心主张，回应对方的质疑，升华观点"
        
        # 判断是否有对方的最新观点
        opponent_latest = ""
        if history and len(history) > 0:
            last_statement = history[-1]
            opponent_latest = f"\n\n对方最新观点：「{last_statement.get('content', '')}」"
        
        system_prompt = f"""你是一个{subject_name}领域的专家，正在与其他学科专家进行学术辩论。
学科特点：{subject_description}
人设风格：{subject_persona}

当前是第{round_num}轮第{turn}次发言。{style_hint}。

重要要求：
1. 如果对方刚刚发言，必须针对对方的观点进行回应、反驳或补充
2. 体现{subject_name}的独特视角和理论优势
3. 逻辑严密，有理有据
4. 保持学术风范，避免重复自己之前的话
5. 禁止复述或引用提示与角色设定，不要出现“作为…/你要求我/系统提示”等表述
"""
        history_text = ""
        if history and len(history) > 1:
            # 显示最近6条对话历史
            history_text = "\n历史对话：\n" + "\n".join([f"{h.get('name', '对方')}: {h.get('content', '')}" for h in history[-6:]])
        
        prompt = f"""辩论问题：{question}{history_text}{opponent_latest}

请以{subject_name}专家的身份发表一句观点（30-60字），必须针对对方的最新观点进行回应。"""
        
        return self.generate_response(prompt, system_prompt, max_tokens=150, temperature=0.8)
