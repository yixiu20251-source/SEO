#!/usr/bin/env python3
"""
启动 Hydra Command Center
"""

import uvicorn
import sys
from pathlib import Path

if __name__ == "__main__":
    # 确保在项目根目录运行
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    print("=" * 60)
    print("Hydra Command Center")
    print("=" * 60)
    print(f"Starting server on http://localhost:8000")
    print("Press CTRL+C to stop")
    print("=" * 60)
    
    uvicorn.run(
        "admin.app:app",
        host="127.0.0.1",  # 改为本地，避免绑定问题
        port=8000,
        reload=False,  # 关闭自动重载，加快启动
        log_level="warning"  # 减少日志输出
    )

