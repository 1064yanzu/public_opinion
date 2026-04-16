from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import os
from datetime import datetime

from app.config import settings

router = APIRouter(
    tags=["reports"],
    responses={404: {"description": "Not found"}},
)

REPORTS_DIR = settings.REPORTS_DIR

@router.get("/", response_model=List[Dict[str, Any]])
async def list_reports():
    """
    列出所有生成的报告文件
    """
    if not os.path.exists(REPORTS_DIR):
        return []
        
    try:
        files = []
        for f in os.listdir(REPORTS_DIR):
            if f.endswith('.md') or f.endswith('.txt') or f.endswith('.json'):
                path = os.path.join(REPORTS_DIR, f)
                stats = os.stat(path)
                create_time = datetime.fromtimestamp(stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
                
                # 尝试从文件名解析关键词: report_KEYWORD_TIMESTAMP.txt
                parts = f.replace("report_", "").split("_")
                keyword = parts[0] if len(parts) > 0 else "未知"
                
                files.append({
                    "id": f, # Use filename as ID
                    "filename": f,
                    "keyword": keyword,
                    "create_time": create_time,
                    "download_url": f"/static/reports/{f}", # Assuming static mount or similar
                    "status": "ready" 
                })
        
        # 按时间倒序
        files.sort(key=lambda x: x['create_time'], reverse=True)
        return files
    except Exception as e:
        print(f"Error listing reports: {e}")
        return []
