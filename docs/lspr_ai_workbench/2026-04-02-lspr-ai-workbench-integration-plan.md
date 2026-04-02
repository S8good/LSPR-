# LSPR AI 工作台实施计划

> **面向代理执行者：** 必须使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans` 按任务逐项实现。步骤使用复选框 `- [ ]` 进行追踪。

**目标：** 将 `DeepLearning/LSPR_Spectra_Master` 作为完整的 `LSPR AI Workbench` 集成到主桌面软件中，覆盖单谱浓度预测、谱线对比、数字孪生可视化、多模型比较、批量预测和数据库归档。

**架构：** 保持主软件作为统一的 UI 和数据库宿主。将 `LSPR_Spectra_Master` 中稳定的推理能力和数字孪生能力通过 `nanosense` 内部的“协议层 + 执行后端抽象 + 服务层”暴露出来，再在主 GUI 中构建一个专门的多标签页工作台窗口。所有 AI 分析结果通过现有数据库结构归档，成为采集、导入和人工分析流程的一部分，同时让同进程调用与子进程桥接在 GUI 层完全透明。

**技术栈：** PyQt5、pyqtgraph、matplotlib、numpy、pandas、基于现有 `DatabaseManager` 的 sqlite3，以及来自 `DeepLearning/LSPR_Spectra_Master` 的 PyTorch 模型。

---

## 范围

本计划的目标是“产品化的研究工作台集成”，不是脚本启动器，也不是把训练平台整仓并入主软件。

本轮纳入：

- 单条光谱浓度预测
- 输入谱 / 重采样谱 / 生成谱 / 对齐谱的可视化对比
- 数字孪生浓度滑块与物理特征面板
- 多模型比较
- 文件夹或多列表文件的批量预测
- 导出与数据库归档
- 从分析菜单、测量页、数据库浏览器进入工作台

本轮明确不做：

- 训练流程
- 论文绘图脚本
- `LSPR_Spectra_Master/scripts` 下的实验运行器
- 直接嵌入 `LSPR_Spectra_Master` 现有独立 GUI

---

## 文件结构

### 主软件侧需要修改的文件

- 修改：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/gui/menu_bar.py`
  - 增加 `LSPR AI Workbench...` 菜单项，并清理与已删除旧 CNN 原型入口有关的遗留命名。
- 修改：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/gui/main_window.py`
  - 连接菜单入口，启动工作台，接收测量页和数据库浏览器传来的光谱，并维护窗口引用。
- 修改：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/gui/settings_dialog.py`
  - 增加 `LSPR_Spectra_Master` 根目录、模型默认项、制品路径和环境模式等设置项。
- 修改：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/utils/config_manager.py`
  - 为 LSPR AI 工作台增加持久化默认配置。
- 修改：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/core/database_manager.py`
  - 增加 AI 分析结果和相关附件的存储辅助方法。
- 修改：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/core/data_access.py`
  - 向数据库浏览器暴露 LSPR AI 归档结果。
- 修改：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/gui/database_explorer.py`
  - 增加从归档结果或光谱集合直接进入工作台的入口。
- 修改：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/README.md`
  - 补充工作台说明，删除过时的深度学习旧描述。

### 主软件侧需要新建的文件

- 新建：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/ml/lspr_backend_protocol.py`
  - 定义 JSON 兼容的请求 / 响应协议和后端接口约束。
- 新建：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/ml/lspr_backend_factory.py`
  - 根据配置选择 `inprocess`、`subprocess` 或 `auto` 模式。
- 新建：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/ml/lspr_master_bridge.py`
  - 对 `LSPR_Spectra_Master` 的导入、模型加载、路径解析和环境诊断做兼容封装。
- 新建：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/ml/lspr_inprocess_backend.py`
  - 同进程执行后端。
- 新建：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/ml/lspr_subprocess_backend.py`
  - 子进程执行后端，负责 JSON 序列化、超时控制、错误转换和 runner 调用。
- 新建：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/ml/lspr_ai_service.py`
  - 向 GUI 暴露稳定的应用级接口，输出规范化结果结构。
- 新建：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/gui/lspr_ai_workbench.py`
  - 工作台主窗口，多标签页容器。
- 新建：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/gui/lspr_single_prediction_widget.py`
  - 单谱导入、预测和摘要显示。
- 新建：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/gui/lspr_spectrum_comparison_widget.py`
  - 输入谱和生成谱的多曲线对比可视化。
- 新建：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/gui/lspr_digital_twin_widget.py`
  - 数字孪生标签页，包括浓度滑块、物理特征和物理 / AI 光谱图。
- 新建：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/gui/lspr_model_comparison_widget.py`
  - 多模型结果比较。
- 新建：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/gui/lspr_batch_prediction_dialog.py`
  - 批量导入、结果表格、导出与归档。
- 新建：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/gui/lspr_result_summary_widget.py`
  - 复用的结果摘要面板。
- 新建：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/tests/test_lspr_ai_service.py`
  - 服务层测试。
- 新建：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/tests/test_lspr_master_bridge.py`
  - 桥接层和路径解析测试。
- 新建：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/tests/test_lspr_ai_workbench_plan_smoke.py`
  - 菜单、配置和基本工作台连通性的冒烟测试。

### `LSPR_Spectra_Master` 侧需要重点查看或适配的文件

- 查看 / 可能修改：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/DeepLearning/LSPR_Spectra_Master/src/core/ai_engine.py`
  - 优先保持其可导入和稳定，不要复制核心推理逻辑。
- 查看 / 可能修改：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/DeepLearning/LSPR_Spectra_Master/src/core/digital_twin_service.py`
  - 复用其图形上下文和物理特征生成逻辑。
- 新建 / 可能修改：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/DeepLearning/LSPR_Spectra_Master/scripts/lspr_bridge_runner.py`
  - 提供最小子进程 runner，至少支持 `health` 和 `predict_single` 命令。
- 查看 / 可能修改：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/DeepLearning/LSPR_Spectra_Master/models/pretrained/*`
  - 统一模型制品发现逻辑和缺失报错。

---

## 数据模型补充

AI 结果应作为结构化分析运行归档，不建议单独发明一套平行存储结构。

建议映射如下：

- `analysis_runs.analysis_type = 'lspr_ai_prediction'`
- `analysis_runs.input_context`
  - 模型 ID
  - 工作台来源标签页
  - 原始文件路径或实验关联信息
  - 重采样 / 归一化元数据
- `analysis_metrics`
  - `predicted_concentration_ng_ml`
  - `report_mode`
  - `reported_text`
  - `uloq_ng_ml`
  - `super_quant_bin`
  - `peak_wavelength_nm`
  - `delta_lambda_nm`
  - `peak_intensity`
  - `intensity_scale`
  - `intensity_offset`
- `analysis_artifacts`
  - 对比图导出
  - 生成谱序列化结果
  - 对齐谱序列化结果
  - 批量预测 CSV / Excel

除非现有 `analysis_runs` 结构明显不够，否则不要新建顶层表。

---

## 用户体验要求

### 工作台入口

- 分析菜单可以在无预载光谱的情况下直接打开工作台。
- 测量页可以把当前结果谱送入工作台。
- 数据库浏览器可以把已存光谱送入工作台。
- 批量预测结果表中的任意一行都可以切换到详细分析。

### 工作台至少包含以下标签页

- `Single Spectrum`
- `Spectrum Comparison`
- `Digital Twin`
- `Model Comparison`
- `Batch Prediction`

### 最低可接受的可视化输出

不能只做“给一个浓度数字”的版本。至少必须显示：

- 输入谱
- 重采样后的输入谱（若不同）
- AI 生成谱
- 对齐后的生成谱
- 可选的物理模型谱
- 峰位 / 红移 / 振幅等关键指标

---

## 任务 1：建立协议层、桥接层和双后端执行骨架

**文件：**
- 新建：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/ml/lspr_backend_protocol.py`
- 新建：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/ml/lspr_backend_factory.py`
- 新建：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/ml/lspr_master_bridge.py`
- 新建：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/ml/lspr_inprocess_backend.py`
- 新建：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/ml/lspr_subprocess_backend.py`
- 新建：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/ml/lspr_ai_service.py`
- 新建：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/tests/test_lspr_master_bridge.py`
- 新建：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/tests/test_lspr_ai_service.py`
- 新建：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/DeepLearning/LSPR_Spectra_Master/scripts/lspr_bridge_runner.py`

- [ ] 先定义统一协议，所有请求和响应都必须是 JSON 兼容结构：
  - `PredictSingleRequest`
  - `BuildComparisonRequest`
  - `BuildDigitalTwinRequest`
  - `BatchPredictRequest`
  - `PredictionResponse`
  - `ComparisonResponse`
  - `DigitalTwinResponse`
  - `BatchPredictionResponse`
  - `ErrorResponse`

- [ ] 定义统一后端接口，例如 `LSPRBackend`，至少包含：
  - `health_check()`
  - `predict_single(...)`
  - `build_comparison(...)`
  - `build_digital_twin(...)`
  - `predict_batch(...)`

- [ ] 定义桥接层职责：
  - 解析 `LSPR_Spectra_Master` 根目录
  - 校验必要模块和模型制品是否存在
  - 承担环境诊断与可用性检查
  - 不让服务层和 GUI 层关心同进程 / 子进程差异

- [ ] 定义服务层返回结构：
  - `LSPRPredictionResult`
  - `LSPRSpectrumComparisonResult`
  - `LSPRDigitalTwinResult`
  - `LSPRBatchPredictionRow`

- [ ] 先写失败测试，覆盖：
  - 根路径缺失
  - 模型文件缺失
  - `backend_mode=auto` 时可根据健康检查选择后端
  - 子进程后端最小 `health` 命令可以返回结构化结果
  - 合法预测结果包含浓度和报告字段
  - 光谱对比结果包含波长轴、输入谱、生成谱、对齐谱

- [ ] 运行目标测试并确认其先失败：

```bash
pytest tests/test_lspr_master_bridge.py tests/test_lspr_ai_service.py -q
```

- [ ] 先实现协议层和工厂层，再实现最小桥接层能力，让路径解析和错误提示先成立。

- [ ] 同时实现两个执行后端：
  - `InProcessLSPRBackend`
  - `SubprocessLSPRBackend`

- [ ] 为子进程方案提供最小 runner 骨架：
  - 支持 `health`
  - 支持 `predict_single`
  - 输入输出走 JSON
  - 包含超时、stderr 收集和结构化错误返回

- [ ] 让服务层只依赖后端接口，不直接依赖具体执行方式。

- [ ] 基于后端接口实现服务方法：
  - `predict_single_spectrum`
  - `build_spectrum_comparison`
  - `build_digital_twin_context`
  - `predict_batch`

- [ ] 再次运行测试并保持通过：

```bash
pytest tests/test_lspr_master_bridge.py tests/test_lspr_ai_service.py -q
```

- [ ] 提交：

```bash
git add nanosense/ml/lspr_backend_protocol.py nanosense/ml/lspr_backend_factory.py nanosense/ml/lspr_master_bridge.py nanosense/ml/lspr_inprocess_backend.py nanosense/ml/lspr_subprocess_backend.py nanosense/ml/lspr_ai_service.py tests/test_lspr_master_bridge.py tests/test_lspr_ai_service.py ../DeepLearning/LSPR_Spectra_Master/scripts/lspr_bridge_runner.py
git commit -m "feat: add LSPR protocol and dual-backend execution layer"
```

---

## 任务 2：增加配置与设置支持

**文件：**
- 修改：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/utils/config_manager.py`
- 修改：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/gui/settings_dialog.py`
- 新建：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/tests/test_lspr_ai_workbench_plan_smoke.py`

- [ ] 增加默认配置项：
  - `lspr_master_root`
  - `lspr_default_model_mode`
  - `lspr_default_artifact_dir`
  - `lspr_enable_digital_twin_overlay`
  - `lspr_batch_export_dir`

- [ ] 先写失败测试，验证这些默认项存在且稳定。

- [ ] 运行测试并确认失败：

```bash
pytest tests/test_lspr_ai_workbench_plan_smoke.py -q
```

- [ ] 在设置对话框中新增 `LSPR AI` 区块：
  - 根目录选择
  - 默认模型选择
  - 导出目录选择
  - 数字孪生叠加开关

- [ ] 通过现有配置读写机制持久化这些设置。

- [ ] 再次运行测试：

```bash
pytest tests/test_lspr_ai_workbench_plan_smoke.py -q
```

- [ ] 提交：

```bash
git add nanosense/utils/config_manager.py nanosense/gui/settings_dialog.py tests/test_lspr_ai_workbench_plan_smoke.py
git commit -m "feat: add LSPR AI workbench settings"
```

---

## 任务 3：实现单谱预测与谱线对比标签页

**文件：**
- 新建：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/gui/lspr_single_prediction_widget.py`
- 新建：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/gui/lspr_spectrum_comparison_widget.py`
- 新建：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/gui/lspr_result_summary_widget.py`
- 新建：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/gui/lspr_ai_workbench.py`
- 修改：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/gui/menu_bar.py`
- 修改：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/gui/main_window.py`

- [ ] 先写失败测试或冒烟断言，覆盖：
  - 菜单中出现 `LSPR AI Workbench...`
  - 主窗口能够打开工作台
  - 工作台能够接收预载光谱

- [ ] 运行测试并确认失败：

```bash
pytest tests/test_menu_bar.py tests/test_lspr_ai_workbench_plan_smoke.py -q
```

- [ ] 实现工作台外壳，至少包含两个标签页：
  - `Single Spectrum`
  - `Spectrum Comparison`

- [ ] 在 `Single Spectrum` 中实现：
  - 导入单谱
  - 浓度预测
  - 结果摘要卡片：报告结果、原始结果、模式、ULOQ、模型
  - 将数据发送到对比标签页

- [ ] 在 `Spectrum Comparison` 中实现：
  - 多曲线绘图
  - 曲线显隐切换
  - 导出当前图像
  - 关键指标面板：峰位、红移、振幅、缩放和偏移

- [ ] 接通菜单与主窗口逻辑。

- [ ] 再次运行测试：

```bash
pytest tests/test_menu_bar.py tests/test_lspr_ai_workbench_plan_smoke.py tests/test_lspr_ai_service.py -q
```

- [ ] 提交：

```bash
git add nanosense/gui/menu_bar.py nanosense/gui/main_window.py nanosense/gui/lspr_single_prediction_widget.py nanosense/gui/lspr_spectrum_comparison_widget.py nanosense/gui/lspr_result_summary_widget.py nanosense/gui/lspr_ai_workbench.py tests/test_menu_bar.py tests/test_lspr_ai_workbench_plan_smoke.py
git commit -m "feat: add LSPR AI workbench single-spectrum flow"
```

---

## 任务 4：实现数字孪生标签页

**文件：**
- 新建：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/gui/lspr_digital_twin_widget.py`
- 修改：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/gui/lspr_ai_workbench.py`
- 修改：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/ml/lspr_ai_service.py`
- 测试：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/tests/test_lspr_ai_service.py`

- [ ] 先写失败测试，验证数字孪生服务输出包含：
  - 波长轴
  - 物理谱
  - 可选 AI 谱
  - 物理特征数据

- [ ] 运行测试并确认失败：

```bash
pytest tests/test_lspr_ai_service.py -q
```

- [ ] 实现 `Digital Twin` 标签页：
  - 浓度滑块
  - 峰位、红移、振幅标签
  - 基线谱、物理公式谱、AI 叠加谱图
  - 可选叠加已导入实验谱

- [ ] 确保该标签页可接收来自单谱预测标签页的最新输入或预测结果。

- [ ] 再次运行测试：

```bash
pytest tests/test_lspr_ai_service.py -q
```

- [ ] 提交：

```bash
git add nanosense/gui/lspr_digital_twin_widget.py nanosense/gui/lspr_ai_workbench.py nanosense/ml/lspr_ai_service.py tests/test_lspr_ai_service.py
git commit -m "feat: add LSPR digital twin visualization tab"
```

---

## 任务 5：增加多模型比较流程

**文件：**
- 新建：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/gui/lspr_model_comparison_widget.py`
- 修改：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/ml/lspr_master_bridge.py`
- 修改：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/ml/lspr_ai_service.py`
- 修改：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/gui/lspr_ai_workbench.py`
- 测试：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/tests/test_lspr_ai_service.py`

- [ ] 定义支持的模型注册表：
  - v1 predictor
  - v2 predictor
  - fusion（若存在）
  - stage3（若模型制品可发现）

- [ ] 先写失败测试，验证服务层多模型比较输出为“每个模型一条结果”。

- [ ] 运行测试并确认失败：

```bash
pytest tests/test_lspr_ai_service.py -q
```

- [ ] 实现模型比较标签页：
  - 可选模型列表
  - 结果表格
  - 多模型生成谱叠加图
  - 推荐默认模型提示

- [ ] 再次运行测试：

```bash
pytest tests/test_lspr_ai_service.py -q
```

- [ ] 提交：

```bash
git add nanosense/gui/lspr_model_comparison_widget.py nanosense/ml/lspr_master_bridge.py nanosense/ml/lspr_ai_service.py nanosense/gui/lspr_ai_workbench.py tests/test_lspr_ai_service.py
git commit -m "feat: add LSPR model comparison workflow"
```

---

## 任务 6：实现批量预测

**文件：**
- 新建：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/gui/lspr_batch_prediction_dialog.py`
- 修改：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/ml/lspr_ai_service.py`
- 修改：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/gui/lspr_ai_workbench.py`
- 测试：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/tests/test_lspr_ai_service.py`

- [ ] 先写失败测试，验证：
  - 文件夹输入能返回多行结果
  - 多列表文件能够正确展开
  - 每行结果包含浓度、模式和文件 / 列标签

- [ ] 运行测试并确认失败：

```bash
pytest tests/test_lspr_ai_service.py -q
```

- [ ] 实现批量输入源：
  - 文件夹
  - 单个多列表文件

- [ ] 实现批量结果表格：
  - 行标签
  - 模型名
  - 预测浓度
  - 报告模式
  - 报告文本
  - 点击后跳转详细分析

- [ ] 实现导出：
  - CSV 汇总
  - 如依赖已存在，则补 Excel 导出

- [ ] 再次运行测试：

```bash
pytest tests/test_lspr_ai_service.py -q
```

- [ ] 提交：

```bash
git add nanosense/gui/lspr_batch_prediction_dialog.py nanosense/ml/lspr_ai_service.py nanosense/gui/lspr_ai_workbench.py tests/test_lspr_ai_service.py
git commit -m "feat: add LSPR batch prediction workflow"
```

---

## 任务 7：将 AI 结果归档到数据库

**文件：**
- 修改：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/core/database_manager.py`
- 修改：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/core/data_access.py`
- 修改：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/gui/database_explorer.py`
- 新建：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/tests/test_lspr_ai_database.py`

- [ ] 先写失败测试，验证：
  - LSPR AI 结果可存为 analysis run
  - 指标项可查询
  - 浏览器访问层可读取归档 AI 详情

- [ ] 运行测试并确认失败：

```bash
pytest tests/test_lspr_ai_database.py -q
```

- [ ] 在 `DatabaseManager` 中实现：
  - 保存单次预测结果
  - 保存谱线对比附件
  - 保存批量预测结果

- [ ] 在 `data_access` 中增加读取接口。

- [ ] 在数据库浏览器中增加查看 / 重新打开 AI 结果的入口。

- [ ] 再次运行测试：

```bash
pytest tests/test_lspr_ai_database.py tests/test_data_access.py -q
```

- [ ] 提交：

```bash
git add nanosense/core/database_manager.py nanosense/core/data_access.py nanosense/gui/database_explorer.py tests/test_lspr_ai_database.py
git commit -m "feat: archive LSPR AI results in database"
```

---

## 任务 8：与测量和导入流程联动

**文件：**
- 修改：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/gui/measurement_widget.py`
- 修改：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/gui/main_window.py`
- 修改：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/nanosense/gui/lspr_ai_workbench.py`
- 测试：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/tests/test_lspr_ai_workbench_plan_smoke.py`

- [ ] 先写失败测试，验证：
  - 测量页可发送当前结果谱
  - 主窗口可用预载光谱打开工作台
  - 标签页切换后仍保留预载数据

- [ ] 运行测试并确认失败：

```bash
pytest tests/test_lspr_ai_workbench_plan_smoke.py -q
```

- [ ] 在测量页和相关导入流程中增加 `Send to LSPR AI Workbench` 入口。

- [ ] 让工作台能识别不同来源：
  - 实时测量
  - 外部文件导入
  - 数据库浏览器
  - 批量结果行

- [ ] 再次运行测试：

```bash
pytest tests/test_lspr_ai_workbench_plan_smoke.py -q
```

- [ ] 提交：

```bash
git add nanosense/gui/measurement_widget.py nanosense/gui/main_window.py nanosense/gui/lspr_ai_workbench.py tests/test_lspr_ai_workbench_plan_smoke.py
git commit -m "feat: connect workbench to measurement flow"
```

---

## 任务 9：文档、打磨与端到端验证

**文件：**
- 修改：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/README.md`
- 新建：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/docs/lspr_ai_workbench/lspr-ai-workbench-user-guide.md`
- 修改：`C:/Users/Spc/Desktop/3.LSPR-code/LSPR_code/25.10.23 - 测试/docs/ui/database_explorer_demo.md`

- [ ] 更新 README，说明：
  - 工作台能力范围
  - 所需模型制品
  - 支持的工作流
  - 环境限制与注意事项

- [ ] 补一份使用手册，包含：
  - 单谱预测流程
  - 谱线对比
  - 数字孪生使用方式
  - 模型比较
  - 批量预测
  - 归档与回看

- [ ] 运行最终聚焦测试集：

```bash
pytest tests/test_menu_bar.py tests/test_lspr_master_bridge.py tests/test_lspr_ai_service.py tests/test_lspr_ai_workbench_plan_smoke.py tests/test_lspr_ai_database.py tests/test_data_access.py -q
```

- [ ] 做一轮手工冒烟验证：
  - 从菜单打开工作台
  - 导入单条光谱
  - 渲染对比图
  - 拖动数字孪生滑块
  - 比较至少两个模型
  - 执行一次批量预测
  - 将一个结果归档，并从数据库浏览器重新打开

- [ ] 提交：

```bash
git add README.md docs/lspr_ai_workbench/lspr-ai-workbench-user-guide.md docs/ui/database_explorer_demo.md
git commit -m "docs: add LSPR AI workbench documentation"
```

---

## 验证说明

在任何阶段声称“已完成”之前，都必须重新运行验证。至少包括：

- 每个任务后的目标测试
- 交付前的聚焦测试集
- 覆盖五个核心标签页的一轮手工冒烟验证

如果最终版本只能预测浓度数字，却没有谱线对比或数字孪生可视化，则不能认定为“已集成完成”。

---

## 依赖与环境策略

首选实现路径：

- 在任务 1 中同时落地两种后端骨架：
  - `inprocess`
  - `subprocess`
- 配置层增加 `backend_mode`：
  - `inprocess`
  - `subprocess`
  - `auto`
- `auto` 模式下先做健康检查：
  - 若同进程健康检查通过，则优先同进程
  - 若同进程失败，则自动切换子进程
- 不允许采用“先只做同进程，出问题再改”的策略

- 子进程方案在任务 1 就必须具备最小可运行骨架：
  - 统一 JSON 协议
  - 超时控制
  - 结构化错误返回
  - `health` 命令
  - `predict_single` 命令

这个决策必须被封装在桥接层内部。GUI 层和服务层不应感知推理是同进程还是子进程。

---

## 成功标准

只有同时满足以下条件，才算集成成功：

- 主软件分析菜单中存在 `LSPR AI Workbench...`
- 用户可以将实时谱或导入谱送入工作台
- 预测结果不仅有浓度，还有图形解释
- 数字孪生可视化是可交互的
- 至少两种模型模式可在同一界面中比较
- 批量预测可处理多条光谱
- AI 结果可以归档并从数据库重新打开
- 文档完整说明了新流程
