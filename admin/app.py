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
from modules.seo.template_obfuscator import TemplateObfuscator

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

# 批量任务队列
batch_queue: list = []
batch_queue_lock = asyncio.Lock()


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


@app.get("/api/stats")
async def get_statistics():
    """获取统计数据"""
    await ensure_engine_initialized()
    
    stats = {
        "total_articles": 0,
        "total_sites": 0,
        "active_sites": 0,
        "today_generated": 0,
        "queue_pending": 0,
        "queue_done": 0
    }
    
    try:
        if engine and engine.config:
            # 统计站点数
            topology = engine.config.get("topology", [])
            stats["total_sites"] = len(topology)
            
            # 统计文章数
            output_path = Path(engine.config.get("output", {}).get("path", "dist"))
            if output_path.exists():
                html_files = list(output_path.rglob("*.html"))
                stats["total_articles"] = len(html_files)
                
                # 统计活跃站点（有文件的站点）
                for site in topology:
                    site_path = output_path / site.get("hostname", "")
                    if site_path.exists() and list(site_path.rglob("*.html")):
                        stats["active_sites"] += 1
            
            # 统计队列
            async with batch_queue_lock:
                stats["queue_pending"] = len([t for t in batch_queue if t["status"] == "pending"])
                stats["queue_done"] = len([t for t in batch_queue if t["status"] == "done"])
            
            # 今日生成（简化：统计最近24小时的任务）
            async with batch_queue_lock:
                now = datetime.now()
                today_tasks = [
                    t for t in batch_queue
                    if t.get("created_at") and 
                    (now - datetime.fromisoformat(t["created_at"])).total_seconds() < 86400
                ]
                stats["today_generated"] = len([t for t in today_tasks if t["status"] == "done"])
    
    except Exception as e:
        logger.error(f"获取统计数据失败: {e}")
    
    return JSONResponse(stats)


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


@app.get("/sites", response_class=HTMLResponse)
async def sites_page(request: Request):
    """站点管理页面"""
    await ensure_engine_initialized()
    
    # 获取站点列表
    sites = []
    if engine and engine.config:
        topology = engine.config.get("topology", [])
        for idx, site in enumerate(topology):
            sites.append({
                "id": idx,
                "hostname": site.get("hostname", ""),
                "role": site.get("role", ""),
                "niche": site.get("mask_context", ""),
                "persona": site.get("persona", ""),
                "status": "Active"  # 可以从文件系统检查
            })
    
    return templates.TemplateResponse("sites.html", {"request": request, "sites": sites})


@app.get("/api/sites")
async def get_sites():
    """获取站点列表 API"""
    await ensure_engine_initialized()
    
    sites = []
    if engine and engine.config:
        topology = engine.config.get("topology", [])
        for idx, site in enumerate(topology):
            # 统计文章数（从输出目录检查）
            output_path = Path(engine.config.get("output", {}).get("path", "dist"))
            site_path = output_path / site.get("hostname", "")
            article_count = 0
            if site_path.exists():
                article_count = len(list(site_path.rglob("*.html")))
            
            sites.append({
                "id": idx,
                "hostname": site.get("hostname", ""),
                "niche": site.get("mask_context", ""),
                "role": site.get("role", ""),
                "persona": site.get("persona", ""),
                "articles": article_count,
                "status": "Active" if site_path.exists() else "Building"
            })
    
    return JSONResponse({"sites": sites})


@app.post("/api/sites")
async def add_site(request: Request):
    """添加新站点"""
    try:
        data = await request.json()
        
        if not engine or not engine.config:
            return JSONResponse({"success": False, "error": "引擎未初始化"}, status_code=500)
        
        # 读取配置
        config = engine.config
        
        # 添加新站点到拓扑
        if "topology" not in config:
            config["topology"] = []
        
        new_site = {
            "hostname": data.get("hostname", ""),
            "role": data.get("role", "ContentPage"),
            "strategy": data.get("strategy", "SEO Strategy"),
            "mask_context": data.get("mask_context", config.get("default_mask_context", "Technology")),
            "persona": data.get("persona", config.get("default_persona", "Expert"))
        }
        
        config["topology"].append(new_site)
        
        # 保存配置
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
        engine.config = config
        
        return JSONResponse({"success": True, "message": "站点已添加"})
    except Exception as e:
        logger.error(f"添加站点失败: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.get("/api/sites/{site_id}")
async def get_site(site_id: int):
    """获取单个站点信息"""
    await ensure_engine_initialized()
    
    if not engine or not engine.config:
        return JSONResponse({"success": False, "error": "引擎未初始化"}, status_code=500)
    
    topology = engine.config.get("topology", [])
    if site_id < 0 or site_id >= len(topology):
        return JSONResponse({"success": False, "error": "站点不存在"}, status_code=404)
    
    site = topology[site_id]
    return JSONResponse({"success": True, "site": site})


@app.put("/api/sites/{site_id}")
async def update_site(site_id: int, request: Request):
    """更新站点信息"""
    try:
        data = await request.json()
        
        if not engine or not engine.config:
            return JSONResponse({"success": False, "error": "引擎未初始化"}, status_code=500)
        
        config = engine.config
        topology = config.get("topology", [])
        
        if site_id < 0 or site_id >= len(topology):
            return JSONResponse({"success": False, "error": "站点不存在"}, status_code=404)
        
        # 更新站点配置
        if "hostname" in data:
            topology[site_id]["hostname"] = data["hostname"]
        if "role" in data:
            topology[site_id]["role"] = data["role"]
        if "mask_context" in data:
            topology[site_id]["mask_context"] = data["mask_context"]
        if "persona" in data:
            topology[site_id]["persona"] = data["persona"]
        if "strategy" in data:
            topology[site_id]["strategy"] = data["strategy"]
        
        # 保存配置
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
        engine.config = config
        
        return JSONResponse({"success": True, "message": "站点已更新"})
    except Exception as e:
        logger.error(f"更新站点失败: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.delete("/api/sites/{site_id}")
async def delete_site(site_id: int):
    """删除站点"""
    try:
        if not engine or not engine.config:
            return JSONResponse({"success": False, "error": "引擎未初始化"}, status_code=500)
        
        config = engine.config
        topology = config.get("topology", [])
        
        if site_id < 0 or site_id >= len(topology):
            return JSONResponse({"success": False, "error": "站点不存在"}, status_code=404)
        
        # 删除站点
        deleted_site = topology.pop(site_id)
        
        # 保存配置
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
        engine.config = config
        
        logger.info(f"站点已删除: {deleted_site.get('hostname', '')}")
        return JSONResponse({"success": True, "message": "站点已删除"})
    except Exception as e:
        logger.error(f"删除站点失败: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.get("/generator", response_class=HTMLResponse)
async def generator_page(request: Request):
    """批量生成工厂页面"""
    await ensure_engine_initialized()
    
    # 获取站点列表供选择
    sites = []
    if engine and engine.config:
        topology = engine.config.get("topology", [])
        for idx, site in enumerate(topology):
            sites.append({
                "id": idx,
                "hostname": site.get("hostname", ""),
                "niche": site.get("mask_context", "")
            })
    
    return templates.TemplateResponse("generator.html", {"request": request, "sites": sites})


@app.post("/api/generator/batch")
async def add_batch_tasks(request: Request):
    """添加批量生成任务到队列"""
    try:
        data = await request.json()
        keywords = data.get("keywords", [])
        site_id = data.get("site_id")
        tone = data.get("tone", "Professional")
        
        if not keywords:
            return JSONResponse({"success": False, "error": "关键词列表为空"}, status_code=400)
        
        async with batch_queue_lock:
            new_tasks = []
            base_id = len(batch_queue) if batch_queue else 0
            for idx, keyword in enumerate(keywords):
                if keyword.strip():
                    task = {
                        "id": base_id + idx + 1,
                        "keyword": keyword.strip(),
                        "site_id": site_id,
                        "tone": tone,
                        "status": "pending",
                        "created_at": datetime.now().isoformat(),
                        "result": None
                    }
                    new_tasks.append(task)
            
            batch_queue.extend(new_tasks)
        
        return JSONResponse({
            "success": True,
            "message": f"已添加 {len(new_tasks)} 个任务到队列",
            "tasks": new_tasks
        })
    except Exception as e:
        logger.error(f"添加批量任务失败: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.get("/api/generator/queue")
async def get_batch_queue():
    """获取批量任务队列状态"""
    async with batch_queue_lock:
        return JSONResponse({
            "queue": batch_queue,
            "total": len(batch_queue),
            "pending": len([t for t in batch_queue if t["status"] == "pending"]),
            "processing": len([t for t in batch_queue if t["status"] == "processing"]),
            "done": len([t for t in batch_queue if t["status"] == "done"]),
            "error": len([t for t in batch_queue if t["status"] == "error"])
        })


@app.post("/api/generator/queue/clear")
async def clear_completed_tasks():
    """清空已完成的任务"""
    try:
        async with batch_queue_lock:
            # 只保留 pending 和 processing 状态的任务
            global batch_queue
            batch_queue = [t for t in batch_queue if t["status"] in ["pending", "processing"]]
        
        return JSONResponse({
            "success": True,
            "message": f"已清空已完成任务，剩余 {len(batch_queue)} 个任务"
        })
    except Exception as e:
        logger.error(f"清空任务失败: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.post("/api/generator/single")
async def generate_single_content(request: Request):
    """单篇内容生成"""
    try:
        data = await request.json()
        topic = data.get("topic", "")
        keywords = data.get("keywords", "")
        site_id = data.get("site_id")
        
        if not topic:
            return JSONResponse({"success": False, "error": "文章标题不能为空"}, status_code=400)
        
        await ensure_engine_initialized()
        
        if not engine:
            return JSONResponse({"success": False, "error": "引擎未初始化"}, status_code=500)
        
        # 获取站点配置
        topology = engine.config.get("topology", [])
        if site_id is None or site_id < 0 or site_id >= len(topology):
            return JSONResponse({"success": False, "error": "站点不存在"}, status_code=400)
        
        site_config = topology[site_id]
        
        # 生成内容
        page_data = await engine.generate_content(
            keyword=topic,
            hostname=site_config.get("hostname", ""),
            mask_context=site_config.get("mask_context"),
            persona=site_config.get("persona")
        )
        
        # 生成URL（基于hostname和keyword）
        hostname = site_config.get("hostname", "")
        # 使用topic作为URL路径的基础
        url_slug = topic.replace(' ', '-').lower()
        # 移除特殊字符
        url_slug = ''.join(c for c in url_slug if c.isalnum() or c == '-')
        url_path = f"/{url_slug}.html"
        page_data["url"] = url_path
        
        # 生成相关链接（简化：使用空列表，因为单篇生成不需要复杂的链接网络）
        related_links = []
        
        # 渲染页面
        html = await engine.render_page(page_data, related_links=related_links)
        
        # 保存页面
        engine.save_page(html, hostname, url_path)
        
        return JSONResponse({
            "success": True,
            "message": "内容生成成功",
            "data": {
                "title": page_data.get("title"),
                "content": page_data.get("content", "")[:500] + "...",  # 预览前500字符
                "url": page_data.get("url", f"https://{site_config.get('hostname')}/"),
                "keywords": keywords
            }
        })
    except Exception as e:
        logger.error(f"单篇生成失败: {e}", exc_info=True)
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.post("/api/generator/start")
async def start_batch_generation(background_tasks: BackgroundTasks):
    """启动批量生成"""
    global generation_status
    
    if generation_status["running"]:
        return JSONResponse({"success": False, "message": "已有生成任务在运行"}, status_code=400)
    
    await ensure_engine_initialized()
    
    if not engine:
        return JSONResponse({"success": False, "message": "引擎未初始化"}, status_code=500)
    
    async def process_batch_queue():
        global generation_status, batch_queue
        try:
            generation_status["running"] = True
            generation_status["error"] = None
            
            async with batch_queue_lock:
                pending_tasks = [t for t in batch_queue if t["status"] == "pending"]
            
            for task in pending_tasks:
                try:
                    # 更新状态为处理中
                    async with batch_queue_lock:
                        task["status"] = "processing"
                    
                    # 获取站点配置
                    topology = engine.config.get("topology", [])
                    if task["site_id"] is not None and task["site_id"] < len(topology):
                        site_config = topology[task["site_id"]]
                        
                        # 生成内容
                        page_data = await engine.generate_content(
                            keyword=task["keyword"],
                            hostname=site_config.get("hostname", ""),
                            mask_context=site_config.get("mask_context"),
                            persona=site_config.get("persona")
                        )
                        
                        # 渲染并保存页面
                        related_links = []
                        html = await engine.render_page(page_data, related_links=related_links)
                        engine.save_page(html, site_config.get("hostname"), "/")
                        
                        # 更新任务结果
                        async with batch_queue_lock:
                            task["status"] = "done"
                            task["result"] = {
                                "title": page_data.get("title"),
                                "url": page_data.get("url", f"https://{site_config.get('hostname')}/")
                            }
                    else:
                        async with batch_queue_lock:
                            task["status"] = "error"
                            task["error"] = "站点配置不存在"
                    
                except Exception as e:
                    logger.error(f"处理任务失败 {task['id']}: {e}")
                    async with batch_queue_lock:
                        task["status"] = "error"
                        task["error"] = str(e)
            
            generation_status["running"] = False
            logger.info("批量生成完成")
            
        except Exception as e:
            generation_status["running"] = False
            generation_status["error"] = str(e)
            logger.error(f"批量生成失败: {e}")
    
    asyncio.create_task(process_batch_queue())
    
    return JSONResponse({
        "success": True,
        "message": "批量生成已启动"
    })


@app.get("/templates", response_class=HTMLResponse)
async def templates_page(request: Request):
    """模板管理页面"""
    return templates.TemplateResponse("templates.html", {"request": request})


@app.post("/api/templates/generate")
async def generate_template_variant(request: Request):
    """生成新的模板变体"""
    try:
        data = await request.json()
        base_html = data.get("base_html", "")
        
        if not base_html:
            return JSONResponse({"success": False, "error": "基础 HTML 不能为空"}, status_code=400)
        
        obfuscator = TemplateObfuscator()
        variant = obfuscator.generate_template_variant(base_html)
        
        return JSONResponse({
            "success": True,
            "variant": variant
        })
    except Exception as e:
        logger.error(f"生成模板变体失败: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.post("/api/templates/compare")
async def compare_templates(request: Request):
    """比较两个模板的相似度"""
    try:
        data = await request.json()
        html1 = data.get("html1", "")
        html2 = data.get("html2", "")
        
        if not html1 or not html2:
            return JSONResponse({"success": False, "error": "HTML 内容不能为空"}, status_code=400)
        
        obfuscator = TemplateObfuscator()
        comparison = obfuscator.compare_templates(html1, html2)
        
        return JSONResponse({
            "success": True,
            "comparison": comparison
        })
    except Exception as e:
        logger.error(f"比较模板失败: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


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

