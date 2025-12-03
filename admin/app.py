"""
Hydra Command Center - FastAPI Web Application
"""

import asyncio
import json
import os
import sys
import secrets
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, BackgroundTasks, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import FileSystemLoader
import yaml

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from hydra import HydraEngine
from core.logger import Logger
from core.config_loader import ConfigLoader
from plugins.llm.factory import LLMFactory
from modules.mimicry.content_strategy import MimicryContentStrategy
from plugins.templates.jinja_renderer import JinjaRenderer
from plugins.domain.domain_dispatcher import HydraDomainDispatcher
from modules.seo.traffic_filter import TrafficFilter

# HTTP Basic Authentication
security = HTTPBasic()
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "hydra")


def check_auth(credentials: HTTPBasicCredentials = Depends(security)):
    """验证HTTP Basic认证凭据"""
    is_correct_username = secrets.compare_digest(credentials.username, ADMIN_USER)
    is_correct_password = secrets.compare_digest(credentials.password, ADMIN_PASS)
    
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


app = FastAPI(
    title="Hydra Command Center",
    version="1.0.0",
    dependencies=[Depends(check_auth)]  # 保护所有路由
)

# 模板和静态文件
templates_dir = Path(__file__).parent / "templates"
templates_dir.mkdir(parents=True, exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))

# 全局状态
engine: Optional[HydraEngine] = None
config_path = project_root / "config.yaml"
logger = Logger()
generation_task: Optional[asyncio.Task] = None
last_run_time: Optional[datetime] = None
generation_status = {"running": False, "error": None}


@app.on_event("startup")
async def startup():
    """启动时初始化（非阻塞）"""
    global engine
    try:
        if config_path.exists():
            # 延迟初始化，避免阻塞启动
            engine = HydraEngine(str(config_path))
            # 只做基本初始化，不检查 LLM 连接
            try:
                engine.config = engine.config_loader.load(str(config_path))
                # 配置日志
                log_config = engine.config.get("logging", {})
                engine.logger.setup(
                    log_level=log_config.get("level", "INFO"),
                    log_file=log_config.get("file"),
                    console_output=log_config.get("console", True)
                )
                logger.info("Hydra Engine 基础初始化完成（LLM 将在首次使用时连接）")
            except Exception as e:
                logger.warning(f"部分初始化失败: {e}，将在首次使用时重试")
        else:
            logger.warning(f"配置文件不存在: {config_path}")
    except Exception as e:
        logger.error(f"启动失败: {e}")


async def ensure_engine_initialized():
    """确保引擎完全初始化（延迟初始化）"""
    global engine
    if engine and not hasattr(engine, '_fully_initialized'):
        try:
            if not engine.llm_provider:
                # 完整初始化（但不阻塞）
                # 在后台线程中初始化 LLM，避免阻塞
                import threading
                def init_llm():
                    try:
                        llm_config = engine.config_loader.get_llm_config()
                        engine.llm_provider = LLMFactory.get_provider(llm_config)
                        engine.content_strategy = MimicryContentStrategy(engine.llm_provider)
                        engine.template_renderer = JinjaRenderer(template_dir="templates")
                        engine.domain_dispatcher = HydraDomainDispatcher()
                        landing_page = engine.config.get("seo", {}).get("landing_page", "/")
                        engine.traffic_filter = TrafficFilter(landing_page=landing_page)
                        engine._fully_initialized = True
                    except Exception as e:
                        logger.warning(f"后台初始化失败: {e}")
                
                thread = threading.Thread(target=init_llm, daemon=True)
                thread.start()
        except Exception as e:
            logger.warning(f"延迟初始化失败: {e}")


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """仪表板首页"""
    # 延迟初始化引擎（非阻塞）
    await ensure_engine_initialized()
    
    status = {
        "engine_ready": engine is not None,
        "config_exists": config_path.exists(),
        "last_run": last_run_time.isoformat() if last_run_time else None,
        "generation_running": generation_status["running"],
        "generation_error": generation_status["error"]
    }
    
    # 检查 LLM 健康状态（快速检查，不阻塞）
    llm_health = False
    if engine and engine.llm_provider:
        try:
            # 设置较短的超时时间
            llm_health = await asyncio.wait_for(
                engine.llm_provider.health_check(),
                timeout=2.0
            )
        except (asyncio.TimeoutError, Exception):
            pass
    
    status["llm_health"] = llm_health
    
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "status": status}
    )


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """配置编辑页面"""
    config_data = {}
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"读取配置失败: {e}")
    
    return templates.TemplateResponse(
        "settings.html",
        {"request": request, "config": config_data}
    )


@app.post("/settings/update")
async def update_settings(request: Request):
    """更新配置"""
    try:
        data = await request.json()
        
        # 读取现有配置
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
        else:
            config = {}
        
        # 深度合并配置
        def deep_merge(base: dict, update: dict):
            for key, value in update.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    deep_merge(base[key], value)
                else:
                    base[key] = value
        
        deep_merge(config, data)
        
        # 保存配置
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
        # 重新初始化引擎
        global engine
        if engine:
            engine.config = config
            engine.config_loader.config = config
        
        return JSONResponse({"success": True, "message": "配置已保存"})
        
    except Exception as e:
        logger.error(f"更新配置失败: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.post("/toggle/{feature_path:path}")
async def toggle_feature(feature_path: str, request: Request):
    """切换功能开关"""
    try:
        data = await request.json()
        value = data.get("value", False)
        
        # 读取配置
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
        else:
            config = {}
        
        # 解析路径（如 "cloudflare.enabled"）
        keys = feature_path.split('.')
        target = config
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        
        target[keys[-1]] = value
        
        # 保存配置
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
        return JSONResponse({"success": True, "value": value})
        
    except Exception as e:
        logger.error(f"切换功能失败: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.post("/action/generate")
async def trigger_generation(background_tasks: BackgroundTasks):
    """触发站点生成"""
    global generation_task, generation_status, last_run_time
    
    # 确保引擎已初始化
    await ensure_engine_initialized()
    
    if generation_status["running"]:
        return JSONResponse(
            {"success": False, "message": "生成任务正在运行中"},
            status_code=400
        )
    
    if not engine:
        return JSONResponse(
            {"success": False, "message": "引擎未初始化"},
            status_code=500
        )
    
    async def run_generation():
        global last_run_time, generation_status
        try:
            generation_status["running"] = True
            generation_status["error"] = None
            last_run_time = datetime.now()
            
            await engine.generate_site()
            
            generation_status["running"] = False
            logger.info("站点生成完成")
            
        except Exception as e:
            generation_status["running"] = False
            generation_status["error"] = str(e)
            logger.error(f"生成失败: {e}")
    
    generation_task = asyncio.create_task(run_generation())
    
    return JSONResponse({
        "success": True,
        "message": "生成任务已启动",
        "task_id": id(generation_task)
    })


@app.get("/status")
async def get_status():
    """获取系统状态"""
    llm_health = False
    if engine and engine.llm_provider:
        try:
            llm_health = await engine.llm_provider.health_check()
        except:
            pass
    
    return JSONResponse({
        "engine_ready": engine is not None,
        "generation_running": generation_status["running"],
        "generation_error": generation_status["error"],
        "llm_health": llm_health,
        "last_run": last_run_time.isoformat() if last_run_time else None
    })


@app.get("/logs/tail")
async def tail_logs(lines: int = 50):
    """获取日志尾部"""
    log_file = project_root / "hydra.log"
    
    if not log_file.exists():
        return JSONResponse({"lines": []})
    
    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            all_lines = f.readlines()
            tail_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        return JSONResponse({
            "lines": [line.rstrip() for line in tail_lines],
            "total": len(all_lines)
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request):
    """日志查看页面"""
    return templates.TemplateResponse("logs.html", {"request": request})


@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """WebSocket 日志流"""
    await websocket.accept()
    log_file = project_root / "hydra.log"
    last_position = 0
    
    try:
        while True:
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(last_position)
                    new_lines = f.readlines()
                    last_position = f.tell()
                    
                    if new_lines:
                        await websocket.send_json({
                            "type": "log",
                            "lines": [line.rstrip() for line in new_lines]
                        })
            
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

