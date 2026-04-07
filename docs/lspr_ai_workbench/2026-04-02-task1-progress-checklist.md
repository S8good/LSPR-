# LSPR AI 工作台任务 1 进展清单

更新时间：2026-04-02

---

## 一、当前已完成的工作

### 1. 任务 1 的协议层与后端抽象已建立

已新增以下核心文件：

- `nanosense/ml/lspr_backend_protocol.py`
- `nanosense/ml/lspr_backend_factory.py`
- `nanosense/ml/lspr_master_bridge.py`
- `nanosense/ml/lspr_inprocess_backend.py`
- `nanosense/ml/lspr_subprocess_backend.py`
- `nanosense/ml/lspr_ai_service.py`

当前已具备的能力：

- 统一的 JSON 兼容请求 / 响应协议
- `LSPRBackend` 抽象接口
- `inprocess / subprocess / auto` 三种后端选择模式
- `auto` 模式下的健康检查与自动回退逻辑
- 服务层不感知具体执行后端

### 2. 子进程 runner 骨架已建立

已新增：

- `DeepLearning/LSPR_Spectra_Master/scripts/lspr_bridge_runner.py`

当前 runner 已支持：

- `health`
- `predict_single`

当前 runner 已具备：

- JSON 输入输出
- 结构化错误返回
- Windows 下的 DLL 搜索路径补全
- 将模型加载日志重定向到 `stderr`，避免污染 JSON 输出

### 3. `LSPR_Spectra_Master` 的环境问题已定位并修通

根因已确认不是“必须换 CPU 版”，而是：

- 直接调用 `py39/python.exe` 或 `gan/python.exe` 时，没有把对应 conda 环境的 `bin` / `Library/bin` 目录加入 DLL 搜索路径
- `FullSpectrumAIEngine` 默认仍按旧文件名查找模型，和当前 `models/pretrained/` 中现有的 v2 权重命名不一致

已完成的修正：

- `lspr_subprocess_backend.py` 现在会为指定解释器自动补充 conda 环境的 DLL 路径
- `lspr_bridge_runner.py` 也增加了防御性 DLL 路径配置
- `src/core/ai_engine.py` 已调整为优先兼容当前已有的 v2 预测模型，并将旧版 v1 / generator 改为可选加载

### 4. 当前已验证通过的内容

测试：

- `pytest tests/test_lspr_master_bridge.py tests/test_lspr_ai_service.py -q`
- 结果：`12 passed`

环境验证：

- `py39` 环境下，`SubprocessLSPRBackend(...).health_check()` 返回 `ok=True`
- `gan` 环境下，`SubprocessLSPRBackend(...).health_check()` 返回 `ok=True`
- `backend_mode='auto'` 时，当前会正确选择 `SubprocessLSPRBackend`

功能验证：

- `lspr_bridge_runner.py predict_single` 已能返回结构化浓度预测结果

---

## 二、当前已知限制

以下内容还没有完成，属于任务 1 之后的下一阶段：

- `InProcessLSPRBackend` 目前只有健康检查，真实预测能力仍是骨架
- `SubprocessLSPRBackend` 的 `build_comparison` 仍未接通真实逻辑
- `SubprocessLSPRBackend` 的 `build_digital_twin` 仍未接通真实逻辑
- `SubprocessLSPRBackend` 的 `predict_batch` 仍未接通真实逻辑
- GUI 工作台还没有开始接入这些服务
- 配置界面还没有增加 `backend_mode`、`lspr_subprocess_python` 等设置项

---

## 三、建议的下一步工作顺序

### 下一步 1：打通 `build_comparison`

目标：

- 基于 `predict_spectrum_from_spectrum(...)` 返回：
  - 输入谱
  - 生成谱
  - 对齐谱
  - 波长轴
  - 关键指标

这是后续 `Spectrum Comparison` 标签页的核心数据来源。

### 下一步 2：打通 `build_digital_twin`

目标：

- 基于 `DigitalTwinService.build_plot_context(...)` 返回：
  - 基线谱
  - 物理谱
  - AI 谱
  - 峰位 / 红移 / 振幅等物理特征

这是后续 `Digital Twin` 标签页的核心数据来源。

### 下一步 3：打通 `predict_batch`

目标：

- 支持一组输入样本的批量预测
- 返回统一行结构，供后续表格展示和导出

### 下一步 4：补配置项

建议新增：

- `backend_mode`
- `lspr_subprocess_python`
- `lspr_master_root`
- `lspr_subprocess_timeout_seconds`

### 下一步 5：开始 GUI 集成

在服务层和子进程后端稳定后，再开始：

- `LSPR AI Workbench` 主窗口
- `Single Spectrum` 标签页
- `Spectrum Comparison` 标签页
- `Digital Twin` 标签页

---

## 四、当前结论

任务 1 的核心目标已经完成：

- 协议层已建立
- 双后端骨架已建立
- 子进程 runner 已建立
- `py39 / gan` 的 GPU 版 torch 环境已能通过 `health`

因此，后续实现可以安全地默认走：

- `backend_mode = auto`
- 优先尝试同进程
- 不可用时自动切到 `subprocess`

而不是继续把环境可用性问题暴露给 GUI 层。

---

## 五、2026-04-03 增量进展

- 任务 2 已启动：`config_manager.py` 已增加 `lspr_*` 默认配置项，`settings_dialog.py` 已增加 `LSPR AI` 设置区块。
- 任务 3 已启动：已新增 `LSPRAIWorkbench` 外壳、`Single Spectrum` 标签页、`Spectrum Comparison` 标签页，并接入主菜单入口。
- 当前验证：
  - `pytest tests/test_menu_bar.py tests/test_lspr_ai_workbench_plan_smoke.py -q`
  - `pytest tests/test_menu_bar.py tests/test_lspr_ai_workbench_plan_smoke.py tests/test_lspr_ai_service.py -q`
  - 结果：`11 passed`
