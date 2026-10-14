# CMAES Water Optimization：水分子结构优化

[English](README.md) · [完整实验说明](docs/experiment.md)

这是一个小型计算化学实验：通过 **CMA-ES（协方差矩阵自适应进化策略）** 搜索单个 H₂O 分子的几何结构，由 **PySCF** 计算 **B3LYP/6-31G\*** 单点能。优化器只使用能量，不调用解析梯度。

**PySCF 是项目的主要运行版本。** 两条 O–H 键约束为等长，因此当前优化变量只有共同键长（Å）和 H–O–H 键角（度）。早期 Gaussian 实现及参考输入单独放在 [legacy/gaussian/](legacy/gaussian/README.md)。

## 快速开始

使用 Python 3.10 或更新版本，并确认平台受到 [PySCF 支持](https://pyscf.org/user/install.html)。

```bash
git clone https://github.com/weida-feng/CMAES-Water-Optimization.git
cd CMAES-Water-Optimization
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
jupyter lab notebooks/water_optimization_pyscf.ipynb
```

选择该环境中的 Python 内核，重启内核并运行全部单元格。程序先检查初始结构能量，再进行优化。完整运行需要多次 DFT 计算，通常耗时几分钟。

也可以直接执行 Notebook，将结果保存在 `outputs/`：

```bash
mkdir -p outputs
jupyter nbconvert --to notebook --execute \
  --ExecutePreprocessor.timeout=1800 \
  --output-dir=outputs notebooks/water_optimization_pyscf.ipynb
```

若 Python 加载了旧的手工安装版本，可检查 `pyscf.__file__`，在当前环境中移除指向旧安装的 `PYTHONPATH` 设置，再重启内核。

## 优化流程

1. CMA-ES 采样候选向量 `[键长, 键角 / 100]`。
2. 能量函数将键角恢复为度，构建两条 O–H 键等长的水分子 Z-matrix。
3. PySCF 计算单点能；SCF 未收敛或能量不是有限值时，拒绝该候选结构。
4. CMA-ES 根据能量排序更新采样分布，直到满足停止条件。

键角除以 100 后，两类变量的数值尺度更接近。默认搜索范围为 0.5–2.0 Å 和 30–170°，迭代上限为 80。计算方法、基组、内存、线程数、初始结构和随机种子都集中在 Notebook 开头。

## 当前 PySCF 运行结果

使用默认参数从头执行 Notebook，得到：

| 等长 O–H / Å | H–O–H / ° | 能量 / Hartree | 评估次数 | 停止条件 |
| ---: | ---: | ---: | ---: | --- |
| 0.96866169 | 103.86624878 | -76.407023582773 | 306 | `tolfun = 1e-8` |

环境和验证范围见 [验证记录](docs/validation.md)。不同版本不一定逐位复现这些数值；输出中的 `maxiter` 表示迭代预算耗尽，需要结合停止原因判断运行情况。

## 核心思路：坐标表示影响能量拟合与优化

相关探索还尝试过用多层感知机（MLP）近似 DFT 能量，再用 CMA-ES 最小化模型预测值。不同表示所保留的变量不同：

| 表示 | 变量数 | 含义 |
| --- | ---: | --- |
| 固定氧原子的笛卡尔坐标 | 6 | 两个氢的空间位置，整体旋转仍会改变输入 |
| 内坐标 | 3 | 两条 O–H 键长和一个 H–O–H 键角 |
| 当前 PySCF 等长键示例 | 2 | 共同键长与键角 |

历史能量模型实验记录如下：

| 能量模型输入 | 测试集 R² | 两条 O–H / Å | H–O–H / ° |
| --- | ---: | --- | ---: |
| 笛卡尔坐标 | 0.7523 | 0.8779、1.0249 | 78.25 |
| 内坐标 | 0.9725 | 0.9541、0.9738 | 105.70 |
| DFT 结构参考 | — | 0.9687、0.9687 | 103.65 |

内坐标实验获得了更接近参考的结构。但实验同时调整了网络大小与正则化，因此不能将全部差异归因于坐标选择；能量拟合的 R² 较高，也不保证势能面最低点和各区域的预测都准确。

[完整实验说明](docs/experiment.md)已在仓库内整理数据生成、坐标转换、训练设置、结构对比、80–130° 柔性扫描、关键数值和结论。当前可执行 Notebook 每次直接调用 PySCF；历史 MLP 训练流程及数据设置作为实验记录说明，仓库没有包含该训练数据集和可执行训练程序。

## 目录

| 路径 | 内容 |
| --- | --- |
| `notebooks/water_optimization_pyscf.ipynb` | 主要运行示例 |
| `requirements.txt` | PySCF、CMA-ES 和 Jupyter 的默认依赖 |
| `docs/experiment.md` | 完整实验原理、设置、结果和讨论 |
| `docs/data/relaxed_scan.csv` | 历史 MLP 柔性扫描结果表 |
| `docs/validation.md` | 当前 PySCF 运行验证 |
| `legacy/gaussian/` | 早期 Gaussian 实现、独立依赖及参考输入 |
| `tests/` | 后端能量检查与失败处理 |

## 检查与适用范围

```bash
python -m unittest discover -s tests -v
```

检查涵盖 SCF 未收敛、异常能量、自旋/方法传递，以及 legacy Gaussian 的日志解析和进程失败处理，不需要 Gaussian，也不运行完整优化。未安装 PySCF 时会跳过相关检查。

这个受约束的单水分子实验用于验证思路；其结果和搜索范围不能直接推广到更大体系。扩展时仍需要考虑坐标设计、原子交换对称性、能量模型在搜索区域的可靠性，以及电子结构计算设置。
