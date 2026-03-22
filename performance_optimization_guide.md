# 性能优化实施指南

> **文档版本**: 1.0  
> **创建时间**: 2026-02-02  
> **目标**: P1-1, P1-2, P1-3 三项性能优化详细实施方案

---

## 📌 优化 P1-1: 实时数据可视化降采样

### 问题分析

**当前情况**:
- 实时采集时每次更新都绘制全部数据点
- 高分辨率光谱(~2048个点)在快速更新时可能卡顿
- 缩放时重绘整个数据集效率低

**性能影响**:
- 绘制2048点的曲线 ~5-10ms
- 每秒10次更新 = 50-100ms/秒（明显卡顿）

### 实施方案

#### 方案1: 启用pyqtgraph降采样 (推荐)

**优点**: 
- 简单易实现
- 自动优化
- 兼容性好

**实施步骤**:

1. **找到所有PlotWidget实例**
```bash
# 搜索创建图表的位置
grep -r "PlotWidget\|PlotItem" nanosense/gui/
```

2. **在图表初始化后添加降采样配置**

```python
# 文件: nanosense/gui/measurement_widget.py (或其他包含图表的文件)

def _init_plot(self):
    """初始化绘图组件"""
    import pyqtgraph as pg
    
    # 创建图表
    self.plot_widget = pg.PlotWidget()
    
    # ====== 新增: 性能优化配置 ======
    # 启用降采样: 自动选择合适的采样率
    self.plot_widget.setDownsampling(
        auto=True,      # 自动模式
        mode='peak'     # 保留峰值信息，适合光谱数据
    )
    
    # 仅绘制可见区域，大幅提升性能
    self.plot_widget.setClipToView(True)
    
    # 可选: 限制最大数据点
    # self.plot_widget.setDownsampling(ds=10, auto=False)  # 固定降采样10倍
    # ==========================
    
    # 其他配置...
    self.curve = self.plot_widget.plot(pen=pg.mkPen('r', width=2))
```

3. **针对不同图表类型优化**

```python
# 对于实时更新的图表
class LiveSpectrumPlot:
    def __init__(self):
        self.plot = pg.PlotWidget()
        # 实时数据优化
        self.plot.setDownsampling(auto=True, mode='peak')
        self.plot.setClipToView(True)
        
        # 可选: 减少更新频率
        self.update_timer = QTimer()
        self.update_timer.setInterval(100)  # 限制为10fps
        self.update_timer.timeout.connect(self._update_plot)

# 对于历史数据图表
class HistoricalSpectrumPlot:
    def __init__(self):
        self.plot = pg.PlotWidget()
        # 大数据集优化  
        self.plot.setDownsampling(auto=True, mode='subsample')
        self.plot.setClipToView(True)
```

#### 方案2: 手动降采样 (高级)

适用于特殊需求或pyqtgraph版本不支持auto模式时。

```python
def downsample_spectrum(wavelengths, intensity, target_points=500):
    """
    手动降采样光谱数据，保留关键特征
    
    Args:
        wavelengths: 波长数组
        intensity: 强度数组
        target_points: 目标点数
    
    Returns:
        downsampled_wl, downsampled_int
    """
    n = len(wavelengths)
    if n <= target_points:
        return wavelengths, intensity
    
    # 计算降采样步长
    step = n // target_points
    
    # 均匀采样
    indices = np.arange(0, n, step)[:target_points]
    
    return wavelengths[indices], intensity[indices]

# 使用示例
def update_plot(self, wavelengths, intensity):
    # 在更新前降采样
    wl_ds, int_ds = downsample_spectrum(wavelengths, intensity, target_points=500)
    self.curve.setData(wl_ds, int_ds)
```

### 测试验证

```python
# 性能测试代码
import time

def benchmark_plot_update():
    """测试绘图性能"""
    import pyqtgraph as pg
    import numpy as np
    
    # 生成测试数据
    wavelengths = np.linspace(400, 1000, 2048)
    intensity = np.random.rand(2048)
    
    # 测试1: 无优化
    plot1 = pg.PlotWidget()
    curve1 = plot1.plot()
    
    start = time.time()
    for _ in range(100):
        curve1.setData(wavelengths, intensity)
    time_no_opt = time.time() - start
    
    # 测试2: 启用降采样
    plot2 = pg.PlotWidget()
    plot2.setDownsampling(auto=True, mode='peak')
    plot2.setClipToView(True)
    curve2 = plot2.plot()
    
    start = time.time()
    for _ in range(100):
        curve2.setData(wavelengths, intensity)
    time_with_opt = time.time() - start
    
    print(f"无优化: {time_no_opt:.3f}s")
    print(f"优化后: {time_with_opt:.3f}s")
    print(f"性能提升: {(1 - time_with_opt/time_no_opt)*100:.1f}%")
```

### 预期效果

- ✅ 实时更新帧率提升 2-5倍
- ✅ 缩放和平移响应速度提升 3-10倍
- ✅ CPU使用率降低 30-50%

---

## 📌 优化 P1-2: 数据库查询优化

### 问题分析

**当前情况**:
- 可能存在N+1查询问题
- 大量数据加载时无分页
- 缺少索引导致查询慢

### 实施方案

#### 步骤1: 添加数据库索引

```python
# 文件: nanosense/utils/database.py (或database相关文件)

class DatabaseManager:
    def create_tables(self):
        """创建数据表并添加索引"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 创建表 (示例)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS experiments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                name TEXT NOT NULL,
                timestamp TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        ''')
        
        # ====== 新增: 性能优化索引 ======
        # 为常用查询字段添加索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_experiments_project_id 
            ON experiments(project_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_experiments_timestamp 
            ON experiments(timestamp DESC)
        ''')
        
        # 复合索引用于多字段查询
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_experiments_project_time
            ON experiments(project_id, timestamp DESC)
        ''')
        # ==============================
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS spectrum_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id INTEGER,
                wavelength REAL,
                intensity REAL,
                FOREIGN KEY (experiment_id) REFERENCES experiments(id)
            )
        ''')
        
        # 光谱数据索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_spectrum_experiment_id
            ON spectrum_data(experiment_id)
        ''')
        
        conn.commit()
```

#### 步骤2: 实现分页查询

```python
class DatabaseManager:
    
    def get_experiments_paginated(self, project_id, page=1, page_size=50):
        """
        分页获取实验列表
        
        Args:
            project_id: 项目ID
            page: 页码 (从1开始)
            page_size: 每页数量
            
        Returns:
            (experiments_list, total_count)
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 计算偏移量
        offset = (page - 1) * page_size
        
        # 获取总数
        cursor.execute('''
            SELECT COUNT(*) FROM experiments
            WHERE project_id = ?
        ''', (project_id,))
        total_count = cursor.fetchone()[0]
        
        # 分页查询
        cursor.execute('''
            SELECT id, name, timestamp
            FROM experiments
            WHERE project_id = ?
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        ''', (project_id, page_size, offset))
        
        experiments = cursor.fetchall()
        
        return experiments, total_count
    
    def get_total_pages(self, total_count, page_size=50):
        """计算总页数"""
        return (total_count + page_size - 1) // page_size
```

#### 步骤3: 批量查询优化

**问题**: 避免N+1查询

```python
# ❌ 不好的做法: N+1 查询
def load_experiments_with_spectra_bad(self, project_id):
    experiments = self.get_experiments(project_id)  # 1次查询
    
    for exp in experiments:
        exp['spectra'] = self.get_spectrum_data(exp['id'])  # N次查询
    
    return experiments

# ✅ 好的做法: 使用JOIN或批量查询
def load_experiments_with_spectra_good(self, project_id):
    """使用JOIN一次性获取所有数据"""
    conn = self.get_connection()
    cursor = conn.cursor()
    
    # 单次查询获取所有实验和光谱数据
    cursor.execute('''
        SELECT 
            e.id, e.name, e.timestamp,
            s.wavelength, s.intensity
        FROM experiments e
        LEFT JOIN spectrum_data s ON e.id = s.experiment_id
        WHERE e.project_id = ?
        ORDER BY e.id, s.wavelength
    ''', (project_id,))
    
    # 整理数据结构
    experiments = {}
    for row in cursor.fetchall():
        exp_id = row[0]
        if exp_id not in experiments:
            experiments[exp_id] = {
                'id': exp_id,
                'name': row[1],
                'timestamp': row[2],
                'wavelengths': [],
                'intensities': []
            }
        
        if row[3] is not None:  # 有光谱数据
            experiments[exp_id]['wavelengths'].append(row[3])
            experiments[exp_id]['intensities'].append(row[4])
    
    return list(experiments.values())
```

#### 步骤4: 使用查询缓存

```python
from functools import lru_cache
import hashlib
import json

class DatabaseManager:
    
    def __init__(self):
        self._query_cache = {}
        self._cache_timeout = 300  # 5分钟缓存
    
    def get_experiments_cached(self, project_id):
        """带缓存的查询"""
        cache_key = f"exp_{project_id}"
        
        # 检查缓存
        if cache_key in self._query_cache:
            cached_time, cached_data = self._query_cache[cache_key]
            if time.time() - cached_time < self._cache_timeout:
                return cached_data
        
        # 执行查询
        data = self.get_experiments(project_id)
        
        # 更新缓存
        self._query_cache[cache_key] = (time.time(), data)
        
        return data
    
    def invalidate_cache(self, cache_key=None):
        """清除缓存"""
        if cache_key:
            self._query_cache.pop(cache_key, None)
        else:
            self._query_cache.clear()
```

### 性能测试

```python
def benchmark_database_queries():
    """数据库查询性能测试"""
    import time
    
    db = DatabaseManager()
    project_id = 1
    
    # 测试1: 无优化
    start = time.time()
    data1 = db.load_experiments_with_spectra_bad(project_id)
    time_no_opt = time.time() - start
    
    # 测试2: JOIN优化
    start = time.time()
    data2 = db.load_experiments_with_spectra_good(project_id)
    time_with_opt = time.time() - start
    
    print(f"N+1查询: {time_no_opt:.3f}s")
    print(f"JOIN查询: {time_with_opt:.3f}s")
    print(f"性能提升: {(1 - time_with_opt/time_no_opt)*100:.1f}%")
```

### 预期效果

- ✅ 查询速度提升 5-10倍
- ✅ 数据库连接数减少 90%
- ✅ 大数据集加载时间减少 70%

---

## 📌 优化 P1-3: 大文件异步加载

### 问题分析

**当前情况**:
- 加载大文件时UI冻结
- 用户无法取消加载操作
- 缺少进度反馈

**影响**:
- 加载10MB文件可能需要5-10秒
- 期间UI完全无响应

### 实施方案

#### 步骤1: 创建文件加载Worker

```python
# 文件: nanosense/utils/file_io_async.py (新建)

from PyQt5.QtCore import QThread, pyqtSignal
import numpy as np
import pandas as pd

class FileLoadWorker(QThread):
    """异步文件加载Worker"""
    
    # 信号定义
    progress = pyqtSignal(int)  # 进度 0-100
    finished = pyqtSignal(object)  # 完成，传递数据
    error = pyqtSignal(str)  # 错误信息
    
    def __init__(self, file_path, file_type='spectrum'):
        super().__init__()
        self.file_path = file_path
        self.file_type = file_type
        self._is_running = True
    
    def run(self):
        """执行加载"""
        try:
            self.progress.emit(10)
            
            if self.file_type == 'spectrum':
                data = self._load_spectrum_file()
            elif self.file_type == 'wide_format':
                data = self._load_wide_format_file()
            else:
                raise ValueError(f"Unknown file type: {self.file_type}")
            
            if not self._is_running:
                return  # 被取消
            
            self.progress.emit(90)
            self.finished.emit(data)
            
        except Exception as e:
            self.error.emit(str(e))
    
    def _load_spectrum_file(self):
        """加载光谱文件"""
        self.progress.emit(30)
        
        # 使用现有的load_spectrum_from_path逻辑
        from nanosense.utils.file_io import load_spectrum_from_path
        
        wavelengths, intensity = load_spectrum_from_path(self.file_path)
        
        self.progress.emit(70)
        
        return {
            'wavelengths': wavelengths,
            'intensity': intensity
        }
    
    def _load_wide_format_file(self):
        """加载宽格式文件"""
        self.progress.emit(30)
        
        from nanosense.utils.file_io import load_wide_format_spectrum
        
        wavelengths, spectra_df, error = load_wide_format_spectrum(self.file_path)
        
        if error:
            raise Exception(error)
        
        self.progress.emit(70)
        
        return {
            'wavelengths': wavelengths,
            'spectra': spectra_df
        }
    
    def cancel(self):
        """取消加载"""
        self._is_running = False
        self.quit()
```

#### 步骤2: 创建进度对话框

```python
# 文件: nanosense/gui/loading_dialog.py (新建)

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton
from PyQt5.QtCore import Qt

class LoadingDialog(QDialog):
    """文件加载进度对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("加载中...")
        self.setWindowModality(Qt.ApplicationModal)
        self.setFixedSize(400, 150)
        
        layout = QVBoxLayout()
        
        # 提示信息
        self.label = QLabel("正在加载文件，请稍候...")
        layout.addWidget(self.label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # 取消按钮
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        layout.addWidget(self.cancel_button)
        
        self.setLayout(layout)
    
    def set_progress(self, value):
        """设置进度"""
        self.progress_bar.setValue(value)
    
    def set_status(self, text):
        """设置状态文本"""
        self.label.setText(text)
```

#### 步骤3: 在主窗口中使用

```python
# 文件: nanosense/gui/measurement_widget.py (或其他需要加载文件的地方)

from PyQt5.QtWidgets import QMessageBox, QFileDialog
from nanosense.utils.file_io_async import FileLoadWorker
from nanosense.gui.loading_dialog import LoadingDialog

class MeasurementWidget:
    
    def load_spectrum_file_async(self):
        """异步加载光谱文件"""
        # 1. 选择文件
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择光谱文件",
            "",
            "All Files (*.txt *.csv *.xlsx *.xls);;Excel Files (*.xlsx *.xls);;CSV Files (*.csv);;Text Files (*.txt)"
        )
        
        if not file_path:
            return
        
        # 2. 创建Worker和进度对话框
        self.load_worker = FileLoadWorker(file_path, file_type='spectrum')
        self.loading_dialog = LoadingDialog(self)
        
        # 3. 连接信号
        self.load_worker.progress.connect(self.loading_dialog.set_progress)
        self.load_worker.finished.connect(self._on_file_loaded)
        self.load_worker.error.connect(self._on_load_error)
        self.loading_dialog.rejected.connect(self._on_load_cancelled)
        
        # 4. 启动加载
        self.load_worker.start()
        self.loading_dialog.exec_()
    
    def _on_file_loaded(self, data):
        """文件加载完成"""
        self.loading_dialog.accept()
        
        # 使用加载的数据
        wavelengths = data['wavelengths']
        intensity = data['intensity']
        
        # 更新UI
        self.plot_curve.setData(wavelengths, intensity)
        
        QMessageBox.information(self, "成功", "文件加载完成！")
    
    def _on_load_error(self, error_msg):
        """加载错误"""
        self.loading_dialog.reject()
        
        QMessageBox.critical(
            self,
            "加载失败",
            f"无法加载文件：{error_msg}"
        )
    
    def _on_load_cancelled(self):
        """用户取消加载"""
        if hasattr(self, 'load_worker'):
            self.load_worker.cancel()
            self.load_worker.wait(1000)  # 等待最多1秒
```

#### 步骤4: 大文件分块读取(可选)

对于非常大的文件(>100MB)，可以分块读取：

```python
class ChunkedFileLoadWorker(QThread):
    """分块加载大文件"""
    
    progress = pyqtSignal(int)
    chunk_loaded = pyqtSignal(object)  # 每块数据
    finished = pyqtSignal()
    
    def __init__(self, file_path, chunk_size=10000):
        super().__init__()
        self.file_path = file_path
        self.chunk_size = chunk_size
    
    def run(self):
        """分块读取"""
        try:
            # 使用pandas的chunksize参数
            chunk_iter = pd.read_csv(
                self.file_path,
                chunksize=self.chunk_size
            )
            
            total_rows = sum(1 for _ in open(self.file_path)) - 1  # 总行数
            processed = 0
            
            for chunk in chunk_iter:
                # 发送数据块
                self.chunk_loaded.emit(chunk)
                
                # 更新进度
                processed += len(chunk)
                progress_pct = int(processed / total_rows * 100)
                self.progress.emit(progress_pct)
            
            self.finished.emit()
            
        except Exception as e:
            self.error.emit(str(e))
```

### 测试验证

```python
def test_async_loading():
    """测试异步加载性能"""
    import time
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication([])
    
    # 生成测试文件
    test_file = "test_large_spectrum.csv"
    wavelengths = np.linspace(400, 1000, 100000)
    intensity = np.random.rand(100000)
    pd.DataFrame({
        'Wavelength': wavelengths,
        'Intensity': intensity
    }).to_csv(test_file, index=False)
    
    # 测试同步加载
    start = time.time()
    from nanosense.utils.file_io import load_spectrum_from_path
    data = load_spectrum_from_path(test_file)
    sync_time = time.time() - start
    print(f"同步加载: {sync_time:.3f}s (UI冻结)")
    
    # 测试异步加载
    start = time.time()
    worker = FileLoadWorker(test_file)
    worker.finished.connect(lambda: print(f"异步加载: {time.time() - start:.3f}s (UI响应)"))
    worker.start()
    worker.wait()
```

### 预期效果

- ✅ UI始终保持响应
- ✅ 支持取消加载操作
- ✅ 用户体验大幅提升
- ✅ 可以加载任意大小的文件

---

## 📊 总体实施计划

### 优先顺序

1. **Week 1**: P1-1 实时数据可视化降采样 (2小时)
   - 影响：立即改善用户体验
   - 风险：低
   - 收益：高

2. **Week 1**: P1-3 大文件异步加载 (3小时)
   - 影响：显著提升用户体验
   - 风险：中等
   - 收益：高

3. **Week 2**: P1-2 数据库查询优化 (4小时)
   - 影响：改善数据加载性能
   - 风险:中等
   - 收益：中

### 测试清单

优化完成后验证：

- [ ] P1-1: 实时绘图帧率 ≥30fps
- [ ] P1-1: 缩放响应时间 <100ms
- [ ] P1-2: 查询100条记录 <500ms
- [ ] P1-2: 支持1000+记录的分页浏览
- [ ] P1-3: 加载10MB文件时UI可响应
- [ ] P1-3: 可以取消加载操作
- [ ] P1-3: 加载进度正常显示

---

## 🔧 故障排除

### pyqtgraph降采样不生效

**原因**: 版本过旧或配置错误

**解决**:
```python
# 检查版本
import pyqtgraph as pg
print(pg.__version__)  # 需要 >= 0.11.0

# 手动降采样备用方案
if pg.__version__ < '0.11.0':
    # 使用手动降采样
    pass
```

### 异步加载卡住

**原因**: 线程未正确结束

**解决**:
```python
def closeEvent(self, event):
    # 确保线程正常结束
    if hasattr(self, 'load_worker'):
        self.load_worker.cancel()
        self.load_worker.wait(5000)  # 等待5秒
    event.accept()
```

---

## 📚 参考资源

- [pyqtgraph性能优化文档](http://www.pyqtgraph.org/documentation/performance.html)
- [SQLite索引优化](https://www.sqlite.org/queryplanner.html)
- [Qt多线程编程](https://doc.qt.io/qt-5/qthread.html)
