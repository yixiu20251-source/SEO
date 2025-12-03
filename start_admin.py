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
    
    uvicorn.run(
        "admin.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

