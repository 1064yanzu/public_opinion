"""Case library routes - Sentiment crisis case management"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User
from ..models.case import Case
from ..core.deps import get_current_active_user
from ..schemas.case import CaseCreate, CaseUpdate, CaseRead, CaseSummary
from ..utils.activity_logger import log_activity

router = APIRouter()


@router.get("/", response_model=List[CaseSummary])
def list_cases(
    category: str = None,
    severity: str = None,
    keyword: str = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取案例列表
    
    可选过滤条件：
    - category: 分类（政治、经济、社会、文化、突发事件）
    - severity: 严重程度（low, medium, high, critical）
    - keyword: 关键词搜索
    """
    query = db.query(Case)
    
    if category:
        query = query.filter(Case.category == category)
    if severity:
        query = query.filter(Case.severity == severity)
    if keyword:
        query = query.filter(
            (Case.title.contains(keyword)) |
            (Case.description.contains(keyword)) |
            (Case.content.contains(keyword))
        )
    
    cases = query.order_by(Case.created_at.desc()).offset(skip).limit(limit).all()
    return cases


@router.get("/{case_id}", response_model=CaseRead)
def get_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取案例详情"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案例不存在")
    return case


@router.post("/", response_model=CaseRead)
def create_case(
    case_in: CaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """创建新案例（需要管理员权限）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    case = Case(
        title=case_in.title,
        category=case_in.category,
        description=case_in.description,
        content=case_in.content,
        date=case_in.date,
        severity=case_in.severity,
        response_strategy=case_in.response_strategy,
        lessons_learned=case_in.lessons_learned,
        keywords=case_in.keywords,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    
    log_activity(db, current_user, "create_case", resource="case", resource_id=case.id)
    return case


@router.put("/{case_id}", response_model=CaseRead)
def update_case(
    case_id: int,
    case_in: CaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新案例（需要管理员权限）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案例不存在")
    
    update_data = case_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(case, key, value)
    
    db.commit()
    db.refresh(case)
    
    log_activity(db, current_user, "update_case", resource="case", resource_id=case.id)
    return case


@router.delete("/{case_id}")
def delete_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除案例（需要管理员权限）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案例不存在")
    
    db.delete(case)
    db.commit()
    
    log_activity(db, current_user, "delete_case", resource="case", resource_id=case_id)
    return {"message": "案例已删除"}


@router.get("/categories/list")
def get_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取所有案例分类"""
    categories = db.query(Case.category).distinct().all()
    return [c[0] for c in categories]


@router.get("/search/similar")
def search_similar_cases(
    keyword: str = Query(..., min_length=1),
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """搜索相似案例（用于智能推荐应对策略）"""
    cases = db.query(Case).filter(
        (Case.title.contains(keyword)) |
        (Case.description.contains(keyword)) |
        (Case.keywords.contains(keyword))
    ).limit(limit).all()
    
    return [
        {
            "id": case.id,
            "title": case.title,
            "category": case.category,
            "response_strategy": case.response_strategy[:200] + "..." if len(case.response_strategy) > 200 else case.response_strategy
        }
        for case in cases
    ]
