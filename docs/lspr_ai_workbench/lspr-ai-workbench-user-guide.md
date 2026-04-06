# LSPR AI Workbench 使用指南

## 1. 入口

当前可通过以下方式打开 `LSPR AI Workbench`：

- 分析菜单中的 `LSPR AI Workbench...`
- 测量页中的 `Send to LSPR AI Workbench`
- 数据库浏览器中的 `Open in LSPR AI Workbench`
- 数据库浏览器 `AI Runs` 标签页中重新打开已归档结果

## 2. 单谱预测

1. 打开工作台。
2. 通过 `Import Spectrum...` 导入光谱，或从测量页 / 数据库浏览器预载入光谱。
3. 选择 `Backend` 和 `Model`。
4. 点击 `Run AI Prediction`。

执行后可看到：

- 浓度预测结果
- 报告模式与报告文本
- 峰位、缩放、偏移等对比指标
- 输入谱与 AI 对比图

## 3. 谱线对比

工作台 `Analysis` 页会显示：

- 当前输入谱
- 生成谱
- 对齐谱

可使用：

- `Export Current Plot` 导出当前图
- `Find Main Peak` 查看主峰位置、强度和 FWHM

如果当前模型不支持生成器，界面会显示回退说明。

## 4. 数字孪生

切换到 `Digital Twin` 标签页后，可：

- 通过滑块或数值框调节浓度
- 生成物理谱、基线谱和 AI 叠加谱
- 叠加当前实验谱进行对比
- 导出数字孪生图像

关键指标包括：

- Peak Wavelength
- Delta Lambda
- Peak Intensity

## 5. 多模型比较

切换到 `Model Comparison` 标签页后，可：

- 勾选要比较的模型模式
- 运行模型比较
- 查看每个模型的浓度、模式和报告文本
- 对比不同模型的对齐谱

当前默认推荐模型显示为 `Recommended: auto`，由后端自动选择当前环境下最稳妥的可用模式。

## 6. 批量预测

切换到 `Batch Prediction` 标签页后，可：

- 通过 `Load Folder...` 导入文件夹中的多条光谱
- 通过 `Load Multi-column File...` 导入多列表文件
- 点击 `Run Batch Prediction` 生成批量结果
- 使用 `Export CSV...` 导出批量结果
- 双击结果表中的某一行，将该行光谱回填到当前工作台分析页

## 7. 结果归档

在完成单谱预测后，可点击 `Archive AI Result` 将结果写入数据库。

当前归档内容包括：

- 结构化 `analysis_runs`
- 关键指标 `analysis_metrics`
- 输入谱、比较数据、数字孪生上下文等 JSON 元数据

如果当前光谱没有已有实验记录，系统会自动在数据库中创建一个 `LSPR AI Workbench` 项目下的实验记录。

## 8. 数据库回看

数据库浏览器支持两种 AI 回看方式：

- 选中实验后，切换到 `AI Runs` 标签页查看已归档的 AI 结果
- 在 `AI Runs` 页中选中某条记录，点击 `Open in LSPR AI Workbench`

重新打开时，系统会尽量恢复：

- 原始输入谱
- 结果摘要
- 谱线对比数据

如果历史归档缺少谱线上下文，则可能只能恢复指标信息。

## 9. 环境说明

推荐配置：

- `lspr_backend_mode = auto`
- `lspr_master_root` 指向 `DeepLearning/LSPR_Spectra_Master`

在当前工作站环境中，`auto` 往往会自动回退到 `subprocess`。只要预测和图形结果正常，这属于预期行为。
