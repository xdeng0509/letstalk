"""
Let's Talk - Web应用后端
使用Flask提供API服务
"""
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from agents.subject_library import SubjectLibrary
from agents.subject_agent import SubjectAgent
from utils.llm_client import LLMClient
import traceback
import random

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 初始化学科库
subject_library = SubjectLibrary()

# 启动参数/环境：强制仅用LLM（禁止演示）
import os, sys
LLM_ONLY = os.getenv('LLM_ONLY', 'false').lower() in ('1','true','yes')
if '--llm-only' in sys.argv:
    LLM_ONLY = True

# 初始化LLM客户端（支持LLM-only模式）
try:
    llm_client = LLMClient()
    demo_mode = False
    llm_available = True
except Exception as e:
    print(f"⚠️  无法连接LLM API: {str(e)}")
    if LLM_ONLY:
        # 强制仅用LLM时，直接退出，不允许演示模式
        print("❌ LLM_ONLY=true，LLM不可用，服务退出。")
        sys.exit(1)
    print("LLM不可用，但用户可以选择使用演示模式")
    llm_client = None
    demo_mode = True
    llm_available = False

# 用户选择的模式（可通过API切换；LLM-only下强制为llm）
user_mode = 'llm' if LLM_ONLY else 'demo'  # 默认demo，LLM_ONLY强制llm

@app.route('/')
def landing():
    """产品介绍首页"""
    return render_template('landing.html')

@app.route('/chat')
def chat():
    """对话入口页"""
    return render_template('index.html')


@app.route('/api/ask', methods=['POST'])
def ask_question():
    """
    处理用户提问，返回学科盲盒开局的回答
    
    Request Body:
        {
            "question": "用户的问题",
            "subject_count": 3  // 可选，默认3个学科
        }
    
    Response:
        {
            "success": true,
            "question": "用户的问题",
            "subjects": [
                {
                    "name": "学科名称",
                    "icon": "学科图标",
                    "answer": "一句话回答",
                    "description": "学科描述"
                }
            ],
            "demo_mode": false
        }
    """
    try:
        data = request.json
        question = data.get('question', '').strip()
        subject_count = data.get('subject_count', 3)
        
        if not question:
            return jsonify({
                'success': False,
                'error': '问题不能为空'
            }), 400
        
        results = []

        # LLM模式下：用大模型选择最相关的Top-N学科
        if user_mode == 'llm':
            from copy import deepcopy
            # 聚合全量学科候选
            all_groups = subject_library.get_all_subjects()
            all_subjects = all_groups['hot'] + all_groups['cold'] + all_groups['crossover']
            # 构造选择提示
            selector_prompt = (
                "你是一个内容路由器。根据用户问题，从下面学科列表中选出最相关的" + str(subject_count) + "个学科名称（中文）。\n" +
                "用户问题：" + question + "\n\n" +
                "学科列表：\n" + "\n".join([f"- {s['name']}：{s['description'][:60]}" for s in all_subjects]) + "\n\n" +
                "只输出学科名称，每行一个，不要编号，不要解释。"
            )
            try:
                current_llm = LLMClient()
                selection_text = current_llm.generate_response(selector_prompt, system_prompt=None, max_tokens=200, temperature=0.2)
                selected_names = [x.strip() for x in selection_text.split('\n') if x.strip()]
                # 映射为对象并去重
                name_to_subject = {s['name']: s for s in all_subjects}
                selected_infos = [name_to_subject[n] for n in selected_names if n in name_to_subject]
                # 回退：不足则补足
                if len(selected_infos) < subject_count:
                    fallback = subject_library.get_smart_subjects(question, count=subject_count, diversity=0.3)
                    # 合并并去重
                    seen = set([s['name'] for s in selected_infos])
                    for s in fallback:
                        if s['name'] not in seen:
                            selected_infos.append(s)
                            seen.add(s['name'])
                            if len(selected_infos) >= subject_count:
                                break
                subjects = selected_infos[:subject_count]
            except Exception as e:
                print(f"[LLM ERROR] subject selection failed: {e}")
                if LLM_ONLY:
                    return jsonify({
                        'success': False,
                        'error': f'LLM学科路由失败：{str(e)}',
                        'llm_only': True
                    }), 503
                subjects = subject_library.get_smart_subjects(question, count=subject_count, diversity=0.3)
        else:
            # 演示模式：使用既有的智能选择
            subjects = subject_library.get_smart_subjects(question, count=subject_count, diversity=0.3)
        
        # 为每个学科生成贴合且简短的一句话回答
        for subject_info in subjects:
            current_llm = LLMClient() if user_mode == 'llm' else None
            agent = SubjectAgent(subject_info, current_llm)
            answer = agent.answer_one_sentence(question)
            # LLM_ONLY：如果该学科回答回退演示，则整体报错，避免混入demo
            if LLM_ONLY and getattr(agent, 'last_used_demo', False):
                return jsonify({
                    'success': False,
                    'error': 'LLM调用失败，盲盒回答已禁止演示模式',
                    'llm_only': True
                }), 503
            results.append({
                'name': subject_info['name'],
                'icon': subject_info['icon'],
                'answer': answer,
                'description': subject_info['description'],
                'display_name': agent.get_display_name(),
                'schools': subject_info.get('schools', []),
                'used_demo': getattr(agent, 'last_used_demo', False)
            })
        
        return jsonify({
            'success': True,
            'question': question,
            'subjects': results,
            'demo_mode': user_mode == 'demo',
            'llm_provider': ('gemini' if isinstance(llm_client, LLMClient) and getattr(llm_client, 'provider', None) == 'gemini' else ('openai' if isinstance(llm_client, LLMClient) and getattr(llm_client, 'provider', None) == 'openai' else ('demo' if user_mode!='llm' else 'unknown')))
        })
    
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/subjects', methods=['GET'])
def get_all_subjects():
    """
    获取所有学科信息
    
    Response:
        {
            "success": true,
            "subjects": {
                "hot": [...],
                "cold": [...],
                "crossover": [...]
            }
        }
    """
    try:
        all_subjects = subject_library.get_all_subjects()
        return jsonify({
            'success': True,
            'subjects': all_subjects
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/status', methods=['GET'])
def get_status():
    """
    获取系统状态
    
    Response:
        {
            "success": true,
            "demo_mode": false,
            "llm_available": true,
            "current_mode": "demo",
            "subject_count": 20
        }
    """
    all_subjects = subject_library.get_all_subjects()
    total_count = (
        len(all_subjects['hot']) + 
        len(all_subjects['cold']) + 
        len(all_subjects['crossover'])
    )
    
    return jsonify({
        'success': True,
        'demo_mode': demo_mode,
        'llm_available': llm_available,
        'current_mode': user_mode,
        'llm_only': LLM_ONLY,
        'subject_count': total_count
    })


@app.route('/api/set-mode', methods=['POST'])
def set_mode():
    """
    设置运行模式
    
    Request Body:
        {
            "mode": "demo" or "llm"
        }
    
    Response:
        {
            "success": true,
            "mode": "demo",
            "message": "已切换到演示模式"
        }
    """
    global user_mode
    
    try:
        data = request.json
        mode = data.get('mode', 'demo').lower()
        
        if mode not in ['demo', 'llm']:
            return jsonify({
                'success': False,
                'error': '无效的模式，请选择 demo 或 llm'
            }), 400
        
        # LLM-only 模式下禁止切换到 demo
        if LLM_ONLY and mode == 'demo':
            return jsonify({
                'success': False,
                'error': 'LLM_ONLY 模式下禁止演示模式'
            }), 400
        
        if mode == 'llm' and not llm_available:
            return jsonify({
                'success': False,
                'error': 'LLM服务不可用，请检查API配置'
            }), 400
        
        user_mode = mode
        
        message = '已切换到LLM模式' if mode == 'llm' else '已切换到演示模式'
        
        return jsonify({
            'success': True,
            'mode': user_mode,
            'message': message,
            'llm_only': LLM_ONLY
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/deep-chat', methods=['POST'])
def deep_chat():
    """
    深入单聊：与单个学科进行深度对话
    
    Request Body:
        {
            "question": "用户的问题",
            "subject_name": "学科名称",
            "context": "之前的对话上下文（可选）"
        }
    
    Response:
        {
            "success": true,
            "subject": "学科名称",
            "answer": "详细回答（3-5句话）",
            "suggestions": ["建议问题1", "建议问题2", "建议问题3"],
            "schools": [...]  // 该学科的派别列表
        }
    """
    try:
        data = request.json
        question = data.get('question', '').strip()
        subject_name = data.get('subject_name', '').strip()
        context = data.get('context', '')
        
        if not question or not subject_name:
            return jsonify({
                'success': False,
                'error': '问题和学科名称不能为空'
            }), 400
        
        # 获取学科信息
        subject_info = subject_library.get_subject_by_name(subject_name)
        if not subject_info:
            return jsonify({
                'success': False,
                'error': f'未找到学科：{subject_name}'
            }), 404
        
        # 创建“每次单聊专用”的 LLM 客户端（真实模型对话），并按需要覆盖 persona
        from copy import deepcopy
        subject_info_override = deepcopy(subject_info)
        representative = data.get('representative')  # 前端派系单聊会传入代表人物姓名
        if representative:
            # 用代表人物风格覆盖 persona，保持身份一致性
            subject_info_override['persona'] = f"以{representative}的口吻与写作风格回答，保持其理论立场与术语习惯。"
        
        current_llm = LLMClient() if (user_mode == 'llm') else None
        agent = SubjectAgent(subject_info_override, current_llm)
        answer = agent.deep_answer(question, context)
        
        # 生成建议问题（使用同一个 agent 保持风格一致）
        suggestions = agent.generate_suggestions(question, answer)
        
        # 获取学科派别
        schools = subject_info.get('schools', [])
        
        # 运行路径信息：提供方与是否回退演示
        llm_provider = agent.llm_client.provider if agent.llm_client else 'demo'
        used_demo = agent.last_used_demo
        
        # LLM_ONLY 强制：若本次回退了演示，则直接返回错误
        if LLM_ONLY and used_demo:
            print(f"[LLM ONLY ENFORCE] deep_chat failed, provider={llm_provider}, subject={subject_name}, error={agent.last_error_message}")
            return jsonify({
                'success': False,
                'error': agent.last_error_message or 'LLM调用失败，已禁止演示模式',
                'llm_provider': llm_provider,
                'used_demo': True
            }), 503
        
        return jsonify({
            'success': True,
            'subject': subject_name,
            'icon': subject_info['icon'],
            'answer': answer,
            'suggestions': suggestions,
            'schools': schools,  # 返回派别信息
            'demo_mode': user_mode == 'demo',
            'llm_provider': llm_provider,
            'used_demo': used_demo
        })
    
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/deep-chat-init', methods=['POST'])
def deep_chat_init():
    """
    初始化深入单聊：获取该学科的建议问题
    
    Request Body:
        {
            "subject_name": "学科名称",
            "question": "原始问题（用于生成相关建议）"
        }
    
    Response:
        {
            "success": true,
            "subject": "学科名称",
            "suggestions": ["建议问题1", "建议问题2", "建议问题3"]
        }
    """
    try:
        data = request.json
        subject_name = data.get('subject_name', '').strip()
        question = data.get('question', '').strip()
        
        if not subject_name:
            return jsonify({
                'success': False,
                'error': '学科名称不能为空'
            }), 400
        
        # 获取学科信息
        subject_info = subject_library.get_subject_by_name(subject_name)
        if not subject_info:
            return jsonify({
                'success': False,
                'error': f'未找到学科：{subject_name}'
            }), 404
        
        # 创建Agent并生成建议问题
        current_llm = llm_client if user_mode == 'llm' else None
        agent = SubjectAgent(subject_info, current_llm)
        suggestions = agent.generate_suggestions(question, '') if question else agent.generate_suggestions('', '')
        
        # 获取派系信息
        schools = subject_info.get('schools', [])
        
        return jsonify({
            'success': True,
            'subject': subject_name,
            'suggestions': suggestions,
            'schools': schools,
            'demo_mode': user_mode == 'demo'
        })
    
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/school-pk', methods=['POST'])
def school_pk():
    """
    学科内派别PK：同一学科内两个不同派别的观点对决
    
    Request Body:
        {
            "question": "用户的问题",
            "subject_name": "学科名称",
            "school1": "派别1名称",
            "school2": "派别2名称",
            "round": 1,  // 当前轮次，默认1
            "history": []  // 历史对话记录
        }
    
    Response:
        {
            "success": true,
            "question": "问题",
            "statements": [
                {"speaker": "school1", "content": "发言内容"},
                {"speaker": "school2", "content": "发言内容"},
                ...
            ],
            "round": 1,
            "has_more": true,
            "fun_fact": "冷知识彩蛋"
        }
    """
    try:
        data = request.json
        question = data.get('question', '').strip()
        subject_name = data.get('subject_name', '').strip()
        school1_name = data.get('school1', '').strip()
        school2_name = data.get('school2', '').strip()
        current_round = data.get('round', 1)
        history = data.get('history', [])
        max_statements = data.get('max_statements', 10)  # 新增：一轮最多的发言数
        user_input = data.get('user_input', None)  # 新增：用户输入
        
        if not question or not subject_name or not school1_name or not school2_name:
            return jsonify({
                'success': False,
                'error': '问题、学科和两个派别名称不能为空'
            }), 400
        
        if school1_name == school2_name:
            return jsonify({
                'success': False,
                'error': '请选择两个不同的派别进行PK'
            }), 400
        
        # 获取学科信息
        subject_info = subject_library.get_subject_by_name(subject_name)
        if not subject_info:
            return jsonify({
                'success': False,
                'error': f'未找到学科：{subject_name}'
            }), 404
        
        # 获取派别信息
        schools = subject_info.get('schools', [])
        school1_info = next((s for s in schools if s['name'] == school1_name), None)
        school2_info = next((s for s in schools if s['name'] == school2_name), None)
        
        if not school1_info or not school2_info:
            return jsonify({
                'success': False,
                'error': '未找到指定的派别'
            }), 404
        
        # 生成本轮的对话（根据 max_statements 参数）
        statements = []
        statements_per_round = max_statements
        
        # 如果有用户输入，加入历史记录
        if user_input:
            history.append({
                'speaker': 'user',
                'name': '用户',
                'icon': '👤',
                'content': user_input
            })
        
        current_llm = llm_client if user_mode == 'llm' else None
        
        for i in range(statements_per_round):
            if i % 2 == 0:
                # school1 发言
                content = _generate_school_statement(
                    question, school1_info, subject_info, 
                    history, current_round, i//2 + 1, current_llm
                )
                statements.append({
                    'speaker': 'school1',
                    'name': school1_name,
                    'icon': school1_info['icon'],
                    'content': content
                })
            else:
                # school2 发言
                content = _generate_school_statement(
                    question, school2_info, subject_info, 
                    history, current_round, i//2 + 1, current_llm
                )
                statements.append({
                    'speaker': 'school2',
                    'name': school2_name,
                    'icon': school2_info['icon'],
                    'content': content
                })
        
        # 判断是否还有更多轮次（最多3轮，共30句）
        max_rounds = 3
        has_more = current_round < max_rounds
        
        response_data = {
            'success': True,
            'question': question,
            'subject_name': subject_name,
            'statements': statements,
            'round': current_round,
            'has_more': has_more,
            'school1': {
                'name': school1_name,
                'icon': school1_info['icon']
            },
            'school2': {
                'name': school2_name,
                'icon': school2_info['icon']
            },
            'demo_mode': user_mode == 'demo'
        }
        
        # 如果是最后一轮，添加冷知识彩蛋
        if not has_more:
            response_data['fun_fact'] = f"💡 有趣的是，{school1_name}和{school2_name}虽然观点不同，但都丰富了{subject_name}的理论体系！跨派别思维是深度理解的关键！"
        
        return jsonify(response_data)
    
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def _generate_school_statement(question, school_info, subject_info, history, round_num, turn, llm_client):
    """生成派别的PK发言"""
    if llm_client is None:
        # 演示模式
        return _get_demo_school_statement(school_info, round_num, turn)
    
    try:
        # 构建派别专属的prompt
        system_prompt = f"""你是{subject_info['name']}领域中{school_info['name']}学派的代表。

学派特点：{school_info['description']}
代表人物：{school_info['representative']}
核心观点：{school_info['viewpoint']}

你正在与{subject_info['name']}的其他学派进行学术辩论。当前是第{round_num}轮第{turn}次发言。

要求：
1. 一句话（30-60字），体现{school_info['name']}的独特立场
2. 观点鲜明，符合该学派的理论特色
3. 可以适当回应对方观点
4. 保持学术风范，避免人身攻击
"""
        
        history_text = ""
        if history:
            history_text = "\n历史对话：\n" + "\n".join([f"{h['name']}: {h['content']}" for h in history[-6:]])
        
        prompt = f"辩论问题：{question}\n{history_text}\n\n请以{school_info['name']}学派的立场发表一句观点（30-60字）。"
        
        response = llm_client.generate_response(prompt, system_prompt, max_tokens=120, temperature=0.8)
        return response
    
    except Exception as e:
        return _get_demo_school_statement(school_info, round_num, turn)


def _get_demo_school_statement(school_info, round_num, turn):
    """生成演示模式的派别发言"""
    templates = [
        f"从{school_info['name']}角度，{school_info['viewpoint']}。",
        f"{school_info['representative']}早已指出，我们应该{school_info['description']}。",
        f"我必须强调，{school_info['name']}的核心在于对这个问题的深刻理解。",
        f"根据{school_info['name']}的理论框架，这个现象可以得到更好的解释。",
        f"让我们回到{school_info['description']}，这才是问题的关键所在。"
    ]
    return templates[(round_num - 1) * 5 + turn - 1] if ((round_num - 1) * 5 + turn - 1) < len(templates) else templates[0]


@app.route('/api/pk', methods=['POST'])
def subject_pk():
    """
    学科PK：两个学科轮流对话辩论
    
    Request Body:
        {
            "question": "用户的问题",
            "subject1": "学科1名称",
            "subject2": "学科2名称",
            "round": 1,  // 当前轮次，默认1
            "history": []  // 历史对话记录
        }
    
    Response:
        {
            "success": true,
            "question": "问题",
            "statements": [
                {"speaker": "subject1", "content": "发言内容"},
                {"speaker": "subject2", "content": "发言内容"},
                ...
            ],
            "round": 1,
            "has_more": true,  // 是否还有更多轮次
            "fun_fact": "冷知识彩蛋"  // 最后一轮才返回
        }
    """
    try:
        data = request.json
        question = data.get('question', '').strip()
        subject1_name = data.get('subject1', '').strip()
        subject2_name = data.get('subject2', '').strip()
        current_round = data.get('round', 1)
        history = data.get('history', [])
        
        if not question or not subject1_name or not subject2_name:
            return jsonify({
                'success': False,
                'error': '问题和两个学科名称不能为空'
            }), 400
        
        if subject1_name == subject2_name:
            return jsonify({
                'success': False,
                'error': '请选择两个不同的学科进行PK'
            }), 400
        
        # 获取两个学科信息
        subject1_info = subject_library.get_subject_by_name(subject1_name)
        subject2_info = subject_library.get_subject_by_name(subject2_name)
        
        if not subject1_info or not subject2_info:
            return jsonify({
                'success': False,
                'error': '未找到指定的学科'
            }), 404
        
        # 创建两个Agent
        current_llm = llm_client if user_mode == 'llm' else None
        agent1 = SubjectAgent(subject1_info, current_llm)
        agent2 = SubjectAgent(subject2_info, current_llm)
        
        # 生成本轮的对话（根据 max_statements 参数）
        statements = []
        statements_per_round = max_statements
        
        for i in range(statements_per_round):
            if i % 2 == 0:
                # subject1 发言
                content = agent1.generate_pk_statement(question, history, round_num=current_round, turn=i//2 + 1)
                statements.append({
                    'speaker': 'subject1',
                    'name': subject1_name,
                    'icon': subject1_info['icon'],
                    'content': content
                })
            else:
                # subject2 发言
                content = agent2.generate_pk_statement(question, history, round_num=current_round, turn=i//2 + 1)
                statements.append({
                    'speaker': 'subject2',
                    'name': subject2_name,
                    'icon': subject2_info['icon'],
                    'content': content
                })
        
        # 判断是否还有更多轮次（最多3轮，共30句）
        max_rounds = 3
        has_more = current_round < max_rounds
        
        response_data = {
            'success': True,
            'question': question,
            'statements': statements,
            'round': current_round,
            'has_more': has_more,
            'subject1': {
                'name': subject1_name,
                'icon': subject1_info['icon']
            },
            'subject2': {
                'name': subject2_name,
                'icon': subject2_info['icon']
            },
            'demo_mode': user_mode == 'demo'
        }
        
        # 如果是最后一轮，添加冷知识彩蛋
        if not has_more:
            response_data['fun_fact'] = _generate_fun_fact(subject1_name, subject2_name, question)
        
        return jsonify(response_data)
    
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def _generate_fun_fact(subject1, subject2, question):
    """生成跨学科冷知识彩蛋"""
    fun_facts = [
        f"💡 有趣的是，{subject1}和{subject2}在历史上曾经是同一门学科的分支！",
        f"💡 研究发现，同时从{subject1}和{subject2}角度思考问题的人，创造力提高了37%！",
        f"💡 许多诺贝尔奖得主都同时精通{subject1}和{subject2}，跨学科思维是创新的关键！",
        f"💡 在古希腊，{subject1}和{subject2}被认为是理解世界的两个互补视角。",
        f"💡 最新研究表明，{subject1}和{subject2}的结合催生了许多前沿领域的突破！"
    ]
    return random.choice(fun_facts)


if __name__ == '__main__':
    print("🎁 Let's Talk - 多学科视角Agent")
    print("=" * 50)
    if demo_mode:
        print("⚠️  演示模式：使用模拟回答")
    else:
        print("✅ LLM模式：使用真实API")
    print("=" * 50)
    print("\n🌐 访问地址: http://localhost:5002")
    print("\n按 Ctrl+C 停止服务\n")
    
    app.run(debug=True, host='0.0.0.0', port=5002)

