"""
AI 助手聊天相关 API 路由
对应原项目的 AI 助手功能
"""
import json
import asyncio
from datetime import datetime
from typing import Optional, List, AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.config import settings

router = APIRouter()


# ===== 请求/响应模型 =====
class ChatMessage(BaseModel):
    """聊天消息"""
    role: str = Field(..., description="角色：user/assistant")
    content: str = Field(..., description="消息内容")


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str = Field(..., description="用户消息")
    history: List[ChatMessage] = Field(default=[], description="历史对话")
    stream: bool = Field(default=False, description="是否流式输出")


class ChatResponse(BaseModel):
    """聊天响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(default="", description="回复内容")
    error: Optional[str] = Field(None, description="错误信息")


class PasswordVerifyRequest(BaseModel):
    """密码验证请求"""
    password: str = Field(..., description="访问密码")


# ===== 会话存储 =====
_chat_sessions = {}  # 简单的内存存储


def get_ai_client():
    """获取 AI 客户端"""
    model_type = settings.AI_MODEL_TYPE.lower()
    
    if model_type == "zhipuai":
        try:
            from zhipuai import ZhipuAI
            client = ZhipuAI(api_key=settings.AI_API_KEY)
            return client, "glm-4-flash"
        except ImportError:
            return None, None
    elif model_type == "openai":
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=settings.AI_API_KEY,
                base_url=settings.AI_BASE_URL or None
            )
            return client, settings.AI_MODEL_ID or "gpt-3.5-turbo"
        except ImportError:
            return None, None
    
    return None, None


def build_system_prompt():
    """构建系统提示词"""
    return """你是一个专业的舆情分析助手，具有以下能力：
1. 分析社交媒体数据中的情感倾向
2. 识别热点话题和趋势
3. 提供舆情应对建议
4. 解答用户关于舆情分析的问题

请用专业、客观的语言回答用户的问题。如果涉及敏感话题，请保持中立立场。
回答要简洁明了，重点突出。"""


@router.post("/verify-password", summary="验证访问密码")
async def verify_password(request: PasswordVerifyRequest):
    """验证访问密码"""
    # 简单的密码验证（实际应该更安全）
    correct_password = settings.SECRET_KEY[:8]  # 使用密钥前8位作为密码
    
    if request.password == correct_password:
        return {"success": True, "message": "验证成功"}
    else:
        return {"success": False, "message": "密码错误"}


@router.post("/chat", response_model=ChatResponse, summary="AI 聊天",
             description="与 AI 助手进行对话")
async def chat(request: ChatRequest, current_user: User = Depends(get_current_user)):
    """
    AI 聊天接口
    
    - **message**: 用户消息
    - **history**: 历史对话（可选）
    - **stream**: 是否流式输出（默认否）
    """
    client, model_name = get_ai_client()
    
    if not client:
        return ChatResponse(
            success=False,
            message="",
            error="AI 服务未配置或不可用，请检查 AI_API_KEY 配置"
        )
    
    try:
        # 构建消息列表
        messages = [{"role": "system", "content": build_system_prompt()}]
        
        # 添加历史消息
        for msg in request.history[-10:]:  # 只保留最近10条
            messages.append({"role": msg.role, "content": msg.content})
        
        # 添加当前消息
        messages.append({"role": "user", "content": request.message})
        
        # 调用 AI
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=2000,
            temperature=0.7,
        )
        
        reply = response.choices[0].message.content
        
        return ChatResponse(
            success=True,
            message=reply,
        )
        
    except Exception as e:
        return ChatResponse(
            success=False,
            message="",
            error=f"AI 请求失败: {str(e)}"
        )


@router.post("/chat-stream", summary="AI 流式聊天",
             description="与 AI 助手进行流式对话")
async def chat_stream(request: ChatRequest, current_user: User = Depends(get_current_user)):
    """
    AI 流式聊天接口
    
    返回 Server-Sent Events (SSE) 格式的流式响应
    """
    client, model_name = get_ai_client()
    
    if not client:
        async def error_generator():
            yield f"data: {json.dumps({'error': 'AI 服务未配置'})}\n\n"
        return StreamingResponse(error_generator(), media_type="text/event-stream")
    
    async def generate() -> AsyncGenerator[str, None]:
        try:
            # 构建消息列表
            messages = [{"role": "system", "content": build_system_prompt()}]
            
            for msg in request.history[-10:]:
                messages.append({"role": msg.role, "content": msg.content})
            
            messages.append({"role": "user", "content": request.message})
            
            # 调用 AI（流式）
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=2000,
                temperature=0.7,
                stream=True,
            )
            
            for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    yield f"data: {json.dumps({'content': content})}\n\n"
            
            yield f"data: {json.dumps({'done': True})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/chat-history", summary="获取聊天历史",
            description="获取当前用户的聊天历史记录")
async def get_chat_history(
    limit: int = Query(50, ge=1, le=200, description="返回数量"),
    current_user: User = Depends(get_current_user)
):
    """获取聊天历史"""
    session_id = f"user_{current_user.id}"
    history = _chat_sessions.get(session_id, [])
    
    return {
        "history": history[-limit:],
        "total": len(history),
    }


@router.post("/clear-chat", summary="清空聊天历史",
             description="清空当前用户的聊天历史记录")
async def clear_chat(current_user: User = Depends(get_current_user)):
    """清空聊天历史"""
    session_id = f"user_{current_user.id}"
    
    if session_id in _chat_sessions:
        del _chat_sessions[session_id]
    
    return {"success": True, "message": "聊天历史已清空"}


@router.post("/analyze-text", summary="分析文本",
             description="使用 AI 分析文本的情感倾向和关键信息")
async def analyze_text(
    text: str = Query(..., description="待分析的文本"),
    current_user: User = Depends(get_current_user)
):
    """
    分析文本
    
    使用 AI 分析文本的：
    - 情感倾向
    - 关键词
    - 主题分类
    """
    client, model_name = get_ai_client()
    
    if not client:
        # 使用 SnowNLP 作为备选
        try:
            from snownlp import SnowNLP
            s = SnowNLP(text)
            score = s.sentiments
            
            if score > 0.6:
                sentiment = "positive"
            elif score < 0.4:
                sentiment = "negative"
            else:
                sentiment = "neutral"
            
            return {
                "success": True,
                "sentiment": sentiment,
                "sentiment_score": round(score, 4),
                "keywords": s.keywords(5),
                "summary": s.summary(3) if len(text) > 100 else [text],
                "method": "snownlp",
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"分析失败: {str(e)}",
            }
    
    try:
        prompt = f"""请分析以下文本，返回 JSON 格式结果：
{{
  "sentiment": "positive/negative/neutral",
  "sentiment_score": 0.0-1.0,
  "keywords": ["关键词1", "关键词2", ...],
  "topics": ["主题1", "主题2", ...],
  "summary": "一句话摘要"
}}

文本：{text}"""
        
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "你是一个专业的文本分析助手，请按要求返回 JSON 格式结果。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.3,
        )
        
        result_text = response.choices[0].message.content
        
        # 尝试解析 JSON
        try:
            # 提取 JSON 部分
            import re
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                result["success"] = True
                result["method"] = "ai"
                return result
        except:
            pass
        
        return {
            "success": True,
            "raw_response": result_text,
            "method": "ai",
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"AI 分析失败: {str(e)}",
        }
