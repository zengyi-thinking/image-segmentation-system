# 图像分割系统项目结构

## 📁 项目目录结构

```
image-segmentation-system/
├── 📄 main.py                    # 主程序入口
├── 📄 quick_start.py             # 快速启动脚本
├── 📄 requirements.txt           # 依赖包列表
├── 📄 README.md                  # 项目说明文档
├── 📄 PROJECT_SUMMARY.md         # 项目总结
├── 📄 IMPROVEMENT_SUMMARY.md     # 改进总结
├── 📄 PROJECT_STRUCTURE.md       # 项目结构说明（本文件）
│
├── 📂 core/                      # 核心算法模块
│   ├── 📄 __init__.py
│   ├── 📄 mst_segmentation.py    # MST分割算法
│   ├── 📄 edge_weights.py        # 边权重计算
│   └── 📄 graph_builder.py       # 图构建器
│
├── 📂 data_structures/           # 数据结构模块
│   ├── 📄 __init__.py
│   ├── 📄 union_find.py          # 并查集实现
│   ├── 📄 pixel_graph.py         # 像素图数据结构
│   └── 📄 segmentation_result.py # 分割结果数据结构
│
├── 📂 gui/                       # 图形用户界面
│   ├── 📄 __init__.py
│   ├── 📄 enhanced_main_window.py      # 增强版主窗口（主要GUI）
│   ├── 📄 main_window.py               # 原版主窗口（备用）
│   ├── 📄 enhanced_image_display.py    # 增强版图像显示组件
│   ├── 📄 control_panel.py             # 控制面板
│   ├── 📄 theme_manager.py             # 主题管理器
│   └── 📄 style_manager.py             # 样式管理器
│
├── 📂 utils/                     # 工具模块
│   ├── 📄 __init__.py
│   ├── 📄 image_io.py            # 图像输入输出
│   ├── 📄 visualization.py       # 可视化工具
│   └── 📄 image_diagnostics.py   # 图像诊断工具
│
├── 📂 evaluation/                # 评估模块
│   ├── 📄 __init__.py
│   ├── 📄 metrics.py             # 评估指标
│   └── 📄 performance_analyzer.py # 性能分析器
│
├── 📂 tests/                     # 测试模块
│   ├── 📄 __init__.py
│   ├── 📄 test_cleanup_verification.py  # 清理后验证测试
│   ├── 📄 fix_callback_error.py         # 回调错误修复脚本
│   ├── 📄 fix_image_loading_error.py    # 图像加载错误修复脚本
│   ├── 📄 simple_test.py                # 简单测试
│   ├── 📄 test_comprehensive_improvements.py
│   ├── 📄 test_gui_fix.py
│   ├── 📄 test_image_loading.py
│   ├── 📄 test_image_loading_fix.py
│   ├── 📄 test_improved_system.py
│   ├── 📄 test_system.py
│   └── 📂 test_enhanced/               # 增强功能测试
│
├── 📂 config/                    # 配置文件
│   └── 📄 theme_config.json      # 主题配置
│
├── 📂 docs/                      # 文档
│   ├── 📄 system_design.md       # 系统设计文档
│   └── 📄 user_manual.md         # 用户手册
│
├── 📂 examples/                  # 示例文件
│   ├── 📄 README.md
│   ├── 📄 demo_image.png
│   └── 📄 test_image.png
│
└── 📂 venv/                      # 虚拟环境（可选）
```

## 🎯 核心模块说明

### 1. **主程序入口**
- `main.py`: 主程序入口，支持GUI和命令行模式
- `quick_start.py`: 快速启动脚本，简化启动流程

### 2. **核心算法 (core/)**
- `mst_segmentation.py`: 最小生成树图像分割算法的核心实现
- `edge_weights.py`: 边权重计算，支持多种权重策略
- `graph_builder.py`: 图构建器，将图像转换为图结构

### 3. **数据结构 (data_structures/)**
- `union_find.py`: 高效的并查集实现，支持路径压缩和按秩合并
- `pixel_graph.py`: 像素图数据结构，管理像素间的连接关系
- `segmentation_result.py`: 分割结果封装，包含统计信息和可视化方法

### 4. **图形界面 (gui/)**
- `enhanced_main_window.py`: 主要GUI界面，功能完整且美观
- `main_window.py`: 备用GUI界面，确保兼容性
- `enhanced_image_display.py`: 高级图像显示组件，支持缩放、拖拽等
- `control_panel.py`: 参数控制面板
- `theme_manager.py`: 主题管理，支持多种视觉主题
- `style_manager.py`: 样式管理，统一界面风格

### 5. **工具模块 (utils/)**
- `image_io.py`: 图像输入输出，支持多种格式和错误处理
- `visualization.py`: 分割结果可视化工具
- `image_diagnostics.py`: 图像质量诊断和分析

### 6. **评估模块 (evaluation/)**
- `metrics.py`: 分割质量评估指标
- `performance_analyzer.py`: 性能分析和基准测试

### 7. **测试模块 (tests/)**
- 包含所有测试脚本、诊断工具和修复脚本
- 分离测试代码与生产代码，保持项目整洁

## 🚀 使用方式

### 启动GUI应用
```bash
python main.py --gui
# 或
python quick_start.py
```

### 命令行使用
```bash
python main.py --input image.jpg --output result.png --threshold 0.5
```

### 运行测试
```bash
python tests/test_cleanup_verification.py
```

## 📊 项目特点

- ✅ **模块化设计**: 清晰的模块分离，易于维护和扩展
- ✅ **完整的GUI**: 美观且功能完整的图形界面
- ✅ **多格式支持**: 支持多种图像格式的输入输出
- ✅ **错误处理**: 完善的错误处理和用户反馈
- ✅ **性能优化**: 高效的算法实现和内存管理
- ✅ **测试覆盖**: 全面的测试脚本和验证工具
- ✅ **文档完整**: 详细的文档和使用说明
