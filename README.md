# 纳米光子学传感检测数据可视化分析系统

本项目是一个面向 SPR / LSPR / Raman / 荧光等实验场景的桌面软件平台，提供从光谱采集、预处理、分析、批量流程到数据库归档与治理的一体化工作流。应用基于 **PyQt5** 与 **pyqtgraph** 构建，既支持连接真实光谱仪硬件，也支持使用内置 Mock API 进行离线演示、联调和教学。

软件当前已经不是单一“采谱工具”，而是包含以下几类能力：

- 多模式实时测量界面
- Raman / SERS 专项分析
- 动力学、灵敏度、校准、亲和力和检测性能分析
- 批量孔板采集与批量分析
- 数据库归档、浏览、导出与治理
- LSPR AI 工作台：单谱预测、谱线对比、数字孪生、多模型比较和批量预测
- LSPR 仿真与结果导出
- 结构化迁移、验证与治理脚本

---

## 目录导航

- [1. 软件定位](#1-软件定位)
- [2. 主要功能](#2-主要功能)
- [3. 软件界面与工作流](#3-软件界面与工作流)
- [4. 快速开始](#4-快速开始)
- [5. 配置说明](#5-配置说明)
- [6. 数据库与数据结构](#6-数据库与数据结构)
- [7. 常用脚本](#7-常用脚本)
- [8. 测试与持续集成](#8-测试与持续集成)
- [9. 项目结构](#9-项目结构)
- [10. 已知限制与使用建议](#10-已知限制与使用建议)

---

## 1. 软件定位

本软件适用于以下典型场景：

- 纳米光子学实验中的实时光谱采集与观察
- SPR / LSPR 共振峰跟踪、位移分析与参数拟合
- Raman 光谱预处理、峰识别、数据库匹配与 SERS 评估
- 批量板或多孔位实验的自动化采集和归档
- 教学演示、算法联调、数据库结构验证和治理

核心设计目标：

- 既能接真实硬件，也能在没有硬件时完整演示主要流程
- 既支持单次测量，也支持批量任务与数据归档
- 将“算法分析结果”和“实验上下文元数据”一起存档，便于追溯

---

## 2. 主要功能

### 2.1 启动器与模式选择

启动程序后会先进入欢迎页，可选择：

- `Real Hardware`：连接真实光谱仪
- `Mock API`：使用内置模拟光谱仪

欢迎页当前提供 6 个入口模式：

- `Absorbance`
- `Transmission`
- `Reflectance`
- `Raman`
- `Fluorescence`
- `Color`

### 2.2 实时测量与基础采集

测量页支持以下通用能力：

- 实时开始 / 停止采集
- 采集暗背景与参考光谱
- 设置积分时间
- 设置平均扫描次数
- 多图联动显示：原始信号、背景、参考、结果光谱
- 单图弹出独立窗口查看
- 当前结果光谱保存和全部光谱批量保存

### 2.3 预处理与谱线处理

内置常用预处理能力：

- 无平滑
- Savitzky-Golay 平滑
- Moving Average 平滑
- Median Filter 平滑
- ALS 基线校正
- 统一分析波段裁剪

Raman 模式额外支持：

- 荧光背景扣除
- 瑞利散射去除
- SNV 等归一化方式
- 波长 / 波数显示切换

### 2.4 峰分析与谱线分析

内置峰分析算法与工具：

- 全峰搜索
- 主共振峰搜索
- FWHM 计算
- 质心计算
- 高斯拟合
- 抛物插值
- 阈值法寻峰
- 拉曼峰计算与匹配

适用于 SPR / LSPR 主峰追踪，也适用于 Raman 峰位分析。

### 2.5 动力学与性能分析

程序菜单中已集成多类专项分析：

- `Sensitivity Calculation`
- `Calibration Curve`
- `Affinity Analysis (KD)`
- `k_obs Linearization`
- `Detection Performance (LOB/LOD/LOQ)`
- `Import Data Analysis`
- `Real-time Data Analysis`
- `Δλ Visualization`

对应能力包括：

- 峰位随时间变化跟踪
- 漂移校正
- 拟合动力学曲线
- 亲和力参数估计
- 灵敏度和检测限评估
- 噪声分析和结果可视化

### 2.6 Raman / SERS 专项能力

Raman 模式下除了基础采谱与预处理，还提供：

- 激发波长设置
- 激光功率设置
- 激光开关控制
- Raman 数据库检索
- 根据峰位匹配数据库物质
- SERS enhancement factor 计算

适合做拉曼峰识别、数据库辅助判读和 SERS 结果评估。

### 2.7 批量采集与批量分析

程序内置批量流程入口：

- `Batch Acquisition Setup`
- `Batch Data Analysis`
- `Generate Analysis Report`

批量流程支持：

- 孔板 / 位置布局配置
- 每孔位多点采集
- 背景 / 参考 / 信号逐步引导
- 采集过程中的实时预览
- 峰值表更新
- 结果自动写入数据库
- 完成后直接进入批量分析

### 2.8 数据库浏览器与归档

程序可将实验与光谱写入 SQLite 数据库，并提供数据库浏览器：

- 按项目、实验名、日期、类型、状态、操作人筛选
- 异步查询，减少 UI 阻塞
- 查看实验详情
- 查看光谱集合
- 查看批次概览
- 导出选中实验
- 删除选中实验
- 将数据库中的光谱直接载入分析窗口

### 2.9 LSPR 仿真与导出

内置 LSPR 传感器仿真模块，支持：

- 传感器响应模型设置
- 浓度扫描
- 参数扫描
- 灵敏度曲线
- 统计结果输出
- 导出 CSV / JSON / Excel / PNG

### 2.10 国际化与主题设置

程序支持以下界面级设置：

- 中英文切换
- 浅色 / 深色主题切换
- 默认数据库路径设置
- 默认文件读写路径设置
- Mock API 配置

### 2.11 LSPR AI 工作台

分析菜单中的 `LSPR AI Workbench...` 已集成 `DeepLearning/LSPR_Spectra_Master` 的推理能力，当前支持：

- 单谱浓度预测与报告文本
- 输入谱、生成谱、对齐谱的可视化对比
- 数字孪生浓度滑块与物理指标查看
- 多模型比较
- 文件夹 / 多列表文件的批量预测
- 结果归档到数据库，并在数据库浏览器的 `AI Runs` 标签页中回看

工作台当前支持以下入口：

- 分析菜单直接打开
- 测量页 `Send to LSPR AI Workbench`
- 数据库浏览器 `Open in LSPR AI Workbench`
- 数据库浏览器 `AI Runs` 标签页中重新打开已归档结果

---

## 3. 软件界面与工作流

推荐按以下顺序理解软件：

### 3.1 单次测量工作流

1. 启动程序并选择 `Real Hardware` 或 `Mock API`
2. 在欢迎页选择一个工作模式
3. 进入测量页后设置积分时间、平滑、基线和分析范围
4. 开始实时采集
5. 采集背景 / 参考
6. 查看结果图并执行峰分析、动力学分析或导出
7. 需要归档时将实验与光谱写入数据库

### 3.2 批量流程工作流

1. 打开 `Batch Acquisition Setup`
2. 配置孔位布局、输出目录和采集参数
3. 按提示执行背景 / 参考 / 信号采集或导入
4. 观察实时预览和峰值更新
5. 批量任务完成后选择是否进入 `Batch Data Analysis`

### 3.3 数据管理工作流

1. 配置数据库路径
2. 运行测量或导入外部文件
3. 在数据库浏览器中筛选实验
4. 查看实验详情、光谱集合和批次信息
5. 导出数据或重新载入分析窗口

---

## 4. 快速开始

### 4.1 环境准备

建议使用 Python 3.10+。

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

如需运行测试：

```bash
pytest tests
```

### 4.2 启动应用

```bash
python main.py
```

可选：生成一个用于数据库浏览器演示的示例数据库：

```bash
python scripts/generate_demo_database.py --output data/demo_database.db --force
```

### 4.3 启动后建议首先检查

- 是否能够成功进入欢迎页
- 是否能在 `Mock API` 模式下正常采集
- 数据库路径是否可写
- 是否能打开数据库浏览器
- 是否能从分析菜单打开 `LSPR AI Workbench...`

---

## 5. 配置说明

默认配置目录：

- `~/.nanosense/config.json`

默认数据库路径：

- `~/.nanosense/nanosense_data.db`

配置项当前至少包含：

- 默认保存路径
- 默认读取路径
- 分析波段范围
- UI 主题
- 数据库路径
- Mock API 配置

Mock API 当前支持的模式：

- `dynamic`
- `static`
- `noisy_baseline`

LSPR AI 工作台相关配置当前至少包括：

- `lspr_master_root`
- `lspr_backend_mode`
- `lspr_subprocess_python`
- `lspr_subprocess_timeout_seconds`
- `lspr_default_inference_model`
- `lspr_default_artifact_dir`
- `lspr_batch_export_dir`

如果使用真实硬件：

- 需要确保厂商 DLL 可被加载
- `drivers/` 目录需可访问
- 系统环境变量 `PATH` 中也可加入驱动路径

---

## 6. 数据库与数据结构

数据库采用 SQLite，除兼容旧结构外，已引入更清晰的结构化模型。

核心关系可概括为：

`projects -> experiments -> spectrum_sets / spectrum_data -> analysis_runs / analysis_metrics`

### 6.1 核心实体

- `projects`：项目
- `experiments`：实验
- `batch_runs`：批量任务
- `batch_run_items`：批量任务中的孔位或位置项
- `spectrum_sets`：一次保存事件对应的光谱集合
- `spectrum_data`：实际谱线数据
- `instrument_states`：仪器状态快照
- `processing_snapshots`：处理参数快照
- `analysis_runs`：分析运行记录
- `analysis_metrics`：分析输出指标

### 6.2 数据库浏览器相关文档

- `docs/ui/database_explorer_demo.md`
- `docs/database_structure.md`

### 6.3 迁移与治理文档

- `docs/migrations/phase1/0001_data_migration_plan.md`
- `docs/operations/legacy_tables.md`
- `docs/operations/migration_governance_schedule.md`
- `docs/validation/validate_migration_roadmap.md`

---

## 7. 常用脚本

### 7.1 数据生成与导入

| 脚本 | 功能 | 示例 |
| ---- | ---- | ---- |
| `scripts/generate_demo_database.py` | 生成演示数据库，便于展示数据库浏览器、批次和光谱集合 | `python scripts/generate_demo_database.py --output data/demo_database.db --force` |
| `scripts/import_spectra.py` | 将 Excel / CSV / TXT 光谱导入数据库，并附带实验、仪器和处理元数据 | `python scripts/import_spectra.py sample.csv --project Demo --experiment Exp01` |

### 7.2 数据库迁移与验证

| 脚本 | 功能 | 示例 |
| ---- | ---- | ---- |
| `scripts/migrate_db.py` | 执行数据库迁移 | `python scripts/migrate_db.py --db data.db` |
| `scripts/validate_migration.py` | 检查迁移结果是否达标 | `python scripts/validate_migration.py --db data.db --max-latency 600 --strict` |
| `scripts/run_validation_report.py` | 汇总验证结果并生成报告 | `python scripts/run_validation_report.py` |
| `scripts/plot_validation_trends.py` | 绘制验证历史趋势图 | `python scripts/plot_validation_trends.py` |

### 7.3 快照治理与运维

| 脚本 | 功能 | 示例 |
| ---- | ---- | ---- |
| `scripts/report_snapshots.py` | 统计仪器 / 处理快照的重复情况并输出报表 | `python scripts/report_snapshots.py --db data.db` |
| `scripts/cleanup_snapshots.py` | 按时间和引用情况清理快照 | `python scripts/cleanup_snapshots.py --db data.db --age-days 90` |
| `scripts/run_snapshot_governance.py` | 一键执行快照治理相关报告和清理流程 | `python scripts/run_snapshot_governance.py --db data.db --cleanup-dry-run` |
| `scripts/legacy_freeze.py` | Legacy 表冻结审核、备份和回填 | `python scripts/legacy_freeze.py --db data.db --freeze-after 2025-10-01 --backfill-missing` |

更多参数请使用：

```bash
python <script> --help
```

---

## 8. 测试与持续集成

### 8.1 单元测试

```bash
pytest tests
```

当前仓库已覆盖的测试重点包括：

- 数据库批量相关逻辑
- 数据访问层
- Legacy freeze 脚本
- 峰分析算法
- 迁移验证逻辑

### 8.2 GitHub Actions

当前工作流目录：

- `.github/workflows/validation.yml`
- `.github/workflows/governance.yml`

主要用途：

- 自动运行迁移验证
- 自动生成治理 / 验证报告
- 为数据库治理相关改动提供回归保护

---

## 9. 项目结构

```text
.
├── nanosense/
│   ├── algorithms/          # 光谱分析、动力学、LSPR、预处理、Raman 数据库等算法
│   ├── core/                # 控制器、采集流程、数据库管理、迁移、处理器
│   ├── gui/                 # 主窗口、测量页、数据库浏览器、批量流程、各类分析对话框
│   ├── ml/                  # CNN 预测相关逻辑
│   ├── tools/               # LSPR 仿真导出等工具
│   ├── translations/        # Qt 翻译文件
│   └── utils/               # 配置、文件读写、报表和绘图工具
├── scripts/                 # 导入、迁移、验证、治理、演示脚本
├── tests/                   # 单元测试
├── docs/                    # 数据库、迁移、UI、治理和验证文档
├── drivers/                 # 真实硬件驱动依赖
├── data/                    # 示例数据库或本地数据
├── main.py                  # GUI 主入口
├── main_acquisition_loop.py # 简化采集循环示例
├── mock_spectrometer_api.py # 可配置模拟光谱仪
├── requirements.txt         # 运行依赖
└── README.md                # 当前文档
```

---

## 10. 已知限制与使用建议

### 10.1 硬件相关

- 真实硬件模式依赖厂商驱动和本机环境，部署前应先在目标机器验证
- 某些激光、激发波长和功率接口在不同 API 中可能只是预留能力

### 10.2 算法相关

- Raman 数据库匹配结果适合作为辅助判读，不应替代人工确认
- `LSPR AI Workbench` 默认推荐使用 `backend_mode=auto`；在当前工作站环境下，`auto` 往往会实际回退到 `subprocess`，这属于预期行为而不是故障
- 从数据库浏览器重新打开 `AI Runs` 依赖归档时保存的输入谱与比较元数据；旧版历史分析记录若缺少这些字段，可能只能查看指标而无法完整恢复图形

### 10.3 文档与数据库相关

- 仓库中的数据库与治理文档相对完整，GUI 功能说明此前偏少，本 README 已按当前代码重新梳理
- `docs/reports/` 常作为生成产物目录使用，本地可按需清理或归档

---

如需进一步了解数据库浏览器演示方式，建议先看：

- `docs/ui/database_explorer_demo.md`
- `docs/lspr_ai_workbench/lspr-ai-workbench-user-guide.md`

如需理解当前数据库结构，建议看：

- `docs/database_structure.md`

如需我继续补充，我可以下一步再帮你写一份更“用户手册化”的文档，比如：

- 安装部署指南
- 操作手册
- 批量采集 SOP
- 数据库结构说明书
