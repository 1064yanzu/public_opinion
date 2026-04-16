# Tauri 桌面化迁移施工文档

## 文档信息

- 任务日期：2026-04-15
- 任务目标：评估当前舆情分析系统是否适合迁移为 `Tauri` 桌面应用，并给出可执行的实施方案
- 评估范围：`frontend`、`backend`、本地数据存储、AI 能力、爬虫能力、设置闭环、打包分发

---

## 启动崩溃排障记录（2026-04-15）

### 现象

macOS 打包产物启动后立即崩溃，系统崩溃报告表面指向：

- `tao::platform_impl::platform::app_delegate::did_finish_launching`
- `panic_cannot_unwind`
- `EXC_CRASH (SIGABRT)`

### 实际根因

这不是单纯的 `tao` 或 `Tauri` 窗口框架缺陷，而是 `Tauri setup` 阶段初始化内置 Python sidecar 失败，错误又发生在 macOS 原生启动回调中，最终被放大成不可 unwind 的 Rust panic。

排查结果分为三层：

1. `backend/run_desktop.py` 使用了字符串入口：

```python
uvicorn.run("app.main:app", ...)
```

`PyInstaller` 不会可靠追踪这种字符串动态导入，导致首个打包产物缺少 `app.main`，运行时直接报：

```text
Could not import module "app.main"
```

2. 修复 `app.main` 后，继续暴露出第二层动态导入缺失：

```text
ModuleNotFoundError: No module named 'aiosqlite'
ModuleNotFoundError: No module named 'passlib.handlers.pbkdf2'
```

这来自：

- `SQLAlchemy async sqlite` 对 `aiosqlite` 的动态加载
- `passlib` 对 handler 子模块的动态注册

3. 即便依赖补齐，`PyInstaller --onefile` 在当前依赖组合下冷启动仍偏慢。实测打包后二进制返回 `/health` 需要约 `48s`，而原先 Rust 侧只等待 `15s`，因此会被误判为“后端启动超时”。

### 已实施修复

#### 后端入口改造

- 文件：`backend/run_desktop.py`
- 改动：
  - 显式 `from app.main import app`
  - 改为 `uvicorn.run(app, ...)`

这样 `PyInstaller` 能静态感知 `app.main` 及其依赖链。

#### 打包脚本加固

- 文件：`backend/scripts/build_desktop_backend.sh`
- 增加：
  - `--hidden-import aiosqlite`
  - `--collect-submodules passlib.handlers`

用于补齐运行时动态导入依赖。

#### Tauri 启动日志加固

- 文件：`frontend/src-tauri/src/main.rs`
- 改动：
  - sidecar 的 `stdout/stderr` 不再丢弃
  - 输出到应用数据目录 `logs/backend.log`

这样后续即便后端启动失败，也能从日志文件直接看到真实 Python 异常，而不是只看到桌面壳崩溃。

#### 启动超时窗口调整

- 文件：`frontend/src-tauri/src/main.rs`
- 改动：
  - 后端等待时间从 `15s` 调整到 `120s`
  - 超时文案明确提示检查 `logs/backend.log`

### 验证结果

- `./.venv/bin/python -m compileall backend/app backend/run_desktop.py`：通过
- `backend/scripts/build_desktop_backend.sh`：通过
- 打包后端二进制独立运行验证：
  - `frontend/src-tauri/resources/backend/public_opinion_backend`
  - 在 `48s` 内成功返回 `/health`
- `npm run build`：通过
- `cargo build --release`：通过
- `frontend/src-tauri/target/release/public_opinion_desktop`：已验证不再在启动阶段立即崩溃

### 当前结论

当前问题本质上是：

- `PyInstaller` 动态导入漏收集
- `onefile` 冷启动慢
- Tauri 侧缺少日志与等待冗余

并不是你的应用在业务逻辑层“随机崩溃”，也不是单纯因为 macOS 版本过新导致完全不可运行。

### 后续优化建议

若下一步继续优化桌面体验，优先级如下：

1. 评估将 Python sidecar 从 `PyInstaller --onefile` 改为 `onedir`
2. 在前端增加“桌面后端启动中”状态页，避免用户误以为卡死
3. 在设置页增加桌面日志目录入口与一键打开日志能力

---

## Sidecar 打包策略优化记录（2026-04-15）

### 目标

在“启动不再崩溃”之后，继续优化桌面端 sidecar 的启动体验，重点评估是否应从 `PyInstaller --onefile` 切换到 `--onedir`。

### 调整内容

#### 1. Python sidecar 改为目录化分发

- 文件：`backend/scripts/build_desktop_backend.sh`
- 调整：
  - 从 `--onefile` 改为 `--onedir`

新产物结构变为：

```text
frontend/src-tauri/resources/backend/
└── public_opinion_backend/
    ├── public_opinion_backend
    └── _internal/
```

这更符合桌面 sidecar 的使用场景，因为不再要求每次启动都先解开整个单文件包。

#### 2. Tauri 兼容两种 sidecar 路径

- 文件：`frontend/src-tauri/src/main.rs`
- `packaged_backend_path()` 现在会依次检查：
  - `resources/backend/public_opinion_backend`
  - `resources/backend/public_opinion_backend/public_opinion_backend`
  - 以及 Tauri 构建后的 `resource_dir/resources/...` 对应路径

这样做的好处是：

- 旧产物还能兼容
- 新产物可以直接切换
- 构建目录与应用包目录都能统一处理

### 实测结果

#### 打包与运行验证

- `backend/scripts/build_desktop_backend.sh`：通过
- `cargo build --release`：通过
- `./target/release/public_opinion_desktop`：通过，已验证能按新目录布局拉起 sidecar

#### 启动耗时观测

目录化 sidecar 在本机上的实测结果如下：

- 首次冷启动：约 `56s`
- 连续重复启动：约 `5s`

这说明：

1. 当前首次启动慢，不只是 `onefile` 解包导致
2. 还包含 Python 运行时装载、动态库解析、`numpy/scipy/pandas/matplotlib` 初始化等成本
3. 当系统文件缓存与资源布局稳定后，重复启动时间会明显下降

### 当前结论

`onedir` 仍然是更适合当前项目的 sidecar 方案，原因是：

- 路径结构更清晰
- 问题排查更直接
- 不依赖启动时临时解包
- 重复启动体验更稳定

但它并不能单独解决“首次启动较慢”的问题。当前首启瓶颈已经更接近“Python 科学计算运行时过重”，而不是打包格式本身。

### 后续建议

如果下一步要继续优化首次启动体验，建议按这个顺序做：

1. 在前端加入明确的“桌面后端启动中”过渡界面
2. 盘点是否有模块在应用启动阶段被过早导入
3. 考虑把词云、报告、部分高级分析依赖延后到真正使用时再加载
4. 评估将 sidecar 拆成“核心服务 + 重分析能力”两层

---

## 启动过渡层与日志闭环补齐（2026-04-15）

### 目标

解决桌面端在后端尚未就绪时“长时间空白”的体验问题，并把启动失败后的排障入口补到设置页，减少用户无反馈等待和定位成本。

### 本次改动

#### 1. 前端入口增加独立启动壳

- 文件：
  - `frontend/src/bootstrap/BootstrapApp.tsx`
  - `frontend/src/bootstrap/BootstrapScreen.tsx`
  - `frontend/src/bootstrap/BootstrapScreen.module.css`
  - `frontend/src/main.tsx`

处理方式：

- 不再等 `loadAppRuntime()` 完成后才首次渲染 React
- 现在先渲染启动壳，再异步装载运行时与路由
- 桌面模式下会明确提示：
  - 正在唤起本地后端
  - 正在装载分析能力
  - 首次冷启动会明显慢于后续启动

这样用户能明确知道当前不是卡死，而是在等待本地 sidecar 与运行时准备完成。

#### 2. 设置页补齐日志入口

- 文件：
  - `backend/app/schemas/system.py`
  - `backend/app/routers/system.py`
  - `frontend/src/types/index.ts`
  - `frontend/src/components/settings/SystemSettingsPanel.tsx`

调整内容：

- `/api/system/runtime` 新增 `log_dir`
- 设置页新增：
  - 打开日志目录
  - 打开 `backend.log`

这样启动失败后，用户不需要自己手动找应用数据目录，也不需要了解内部结构，就能直接进入日志文件查看问题。

### 当前效果

本次改动后，桌面端启动链路形成了完整闭环：

1. 启动中有明确过渡反馈
2. 启动完成后进入主界面
3. 启动失败时可从设置页直接打开日志排障

这比单纯延长等待时间更符合桌面应用预期，也更容易让用户理解系统正在做什么。

### 验证

- `npm run build`：通过
- `./.venv/bin/python -m compileall backend/app`：通过

---

## React 前端功能补齐与旧版视图对齐（2026-04-15）

### 目标

排查 Tauri 桌面版中的 React 前端为何相比旧版 `views` 页面功能不全，并把缺失入口、接口能力和数据映射补齐到可实际运行的状态。

### 发现的问题

本轮检查确认，之前的桌面 React 前端并未完整覆盖旧版页面能力，主要缺口有三类：

1. 页面入口缺失
   - 旧版 `views/page/templates` 中存在：
     - `spider_setting.html`
     - `bigdata.html`
     - `case_study.html`
     - `manual.html`
   - React 前端此前没有对应路由和导航入口。

2. 前后端契约存在错配
   - `Analysis.tsx` 将后端统计结构中的数量字段误当成比例字段使用
   - `Dashboard.tsx` 将累计数据误展示为“今日新增”
   - `Reports.tsx` 对报告生成失败缺少明确处理
   - `Advanced.tsx` 中词云图片地址未统一走桌面运行时后端地址解析

3. 后端缺少旧版页面所需的部分内容接口
   - 只有案例列表，没有案例详情接口
   - 没有把项目中的真实 `网络舆情应对手册.md` 暴露给 React 页面

### 本次改动

#### 1. 后端补齐页面内容服务

- 新增文件：
  - `backend/app/services/page_content.py`
- 新增接口：
  - `GET /api/page/cases/{case_id}`
  - `GET /api/page/manual-content`

实现效果：

- 案例详情现在基于真实任务与真实微博/抖音数据聚合返回
- 手册页面现在直接读取仓库中的 `网络舆情应对手册.md`

#### 2. React 前端补齐旧版主要页面

- 新增页面：
  - `frontend/src/pages/Spider.tsx`
  - `frontend/src/pages/BigData.tsx`
  - `frontend/src/pages/Cases.tsx`
  - `frontend/src/pages/Manual.tsx`
- 新增样式：
  - `Spider.module.css`
  - `BigData.module.css`
  - `Cases.module.css`
  - `Manual.module.css`
- 新增页面服务层：
  - `frontend/src/services/page.ts`

实现效果：

- 新增“爬虫控制”页，支持创建任务、查看任务、停止任务、查看抓取结果
- 新增“数据看板”页，对齐旧版大屏的热点、监测、情感分布能力
- 新增“案例库”页，支持案例列表与案例详情联动
- 新增“应对手册”页，直接渲染真实手册正文

#### 3. React 路由与导航补齐

- 修改：
  - `frontend/src/App.tsx`
  - `frontend/src/components/layout/Sidebar.tsx`

新增路由：

- `/spider`
- `/bigdata`
- `/cases`
- `/manual`

### 4. 已有页面数据映射修正

- 修改：
  - `frontend/src/pages/Analysis.tsx`
  - `frontend/src/pages/Dashboard.tsx`
  - `frontend/src/pages/Reports.tsx`
  - `frontend/src/pages/Advanced.tsx`
  - `frontend/src/types/index.ts`

修复内容：

- 分析页改为读取真实趋势、真实风险和真实统计
- 仪表盘“今日新增内容”改为使用 `today_posts`
- 报告页增加生成失败反馈和刷新列表逻辑
- 高级洞察页词云图片统一通过桌面后端地址解析

### 5. 文档同步

- 更新：
  - `docs/api_documentation.md`

补充说明了：

- 案例详情接口
- 手册正文接口

### 验证

- `cd frontend && npm run build`：通过
- `./.venv/bin/python -m compileall backend/app backend/run_desktop.py`：通过
- 冒烟验证：
  - `GET /health`：200
  - `GET /api/page/manual-content`：200
  - `GET /api/page/cases`：200

### 额外记录

在本地直接从项目根目录用 `uvicorn app.main:app` 启动时，会被根目录遗留的旧 `app.py` 抢占模块名 `app`，导致导入串到旧 Flask 文件。当前正确的开发态启动方式应从 `backend` 目录启动，或显式处理模块路径。

### 后续建议

如果继续优化桌面端首启体验，下一步最值得做的是：

1. 把“启动中”页与实际启动阶段打通，显示更细的阶段文案
2. 让前端在后端超时后直接提示“去设置页查看日志”
3. 继续排查哪些重分析模块可以延迟导入

---

## macOS 安装包构建记录（2026-04-15）

### 目标

生成当前桌面版的 macOS 可分发安装包，并确认包内已带上目录化 Python sidecar。

### 构建步骤

执行顺序如下：

1. `npm run tauri:build:backend`
2. `npm run tauri:build`

构建完成后，Tauri 产出了：

- `bundle/macos/舆情洞察.app`
- `bundle/dmg/舆情洞察_0.1.0_aarch64.dmg`

### 构建中发现的问题

尽管：

- `frontend/src-tauri/target/release/resources/backend`

已经存在目录化 sidecar，但 Tauri 生成的初始 `.app` 中只有：

- `Contents/MacOS/public_opinion_desktop`

没有自动生成：

- `Contents/Resources/backend`

这意味着默认产物在安装后有较高概率无法找到打包后的 Python sidecar。

### 本次修复方式

为确保本次可以交付可用安装包，采用了直接修补产物的方式：

1. 手动创建：

```text
舆情洞察.app/Contents/Resources/backend
```

2. 将以下目录复制进去：

```text
frontend/src-tauri/target/release/resources/backend
```

3. 对修复后的 `.app` 执行：

```bash
codesign --force --deep -s -
```

4. 基于修复后的 `.app` 重新生成：

```text
舆情洞察_0.1.0_aarch64_fixed.dmg
```

### 验证结果

直接从包内执行：

```text
舆情洞察.app/Contents/MacOS/public_opinion_desktop
```

已验证它会拉起包内 sidecar：

```text
舆情洞察.app/Contents/Resources/backend/public_opinion_backend
```

这说明修复后的 `.app` 已经具备独立运行所需的后端资源。

### 当前交付建议

本次应优先使用修复后的产物：

- `frontend/src-tauri/target/release/bundle/dmg/舆情洞察_0.1.0_aarch64_fixed.dmg`

原始 Tauri 生成的 `.dmg` 虽然构建成功，但由于 `.app` 初始不含 `Contents/Resources/backend`，不建议直接分发。

### 后续建议

当前这个问题已经被规避，但后续仍建议继续收口为“构建流程自动化修复”，避免每次打包后都手工补资源。优先方向：

1. 研究 Tauri v2 对 `bundle.resources` 目录型资源在 macOS bundle 下的实际复制行为
2. 如官方路径仍不稳定，可在打包脚本中加入后处理步骤，自动补齐 `Contents/Resources/backend`
3. 后续若改为 CI 构建，务必把这一步纳入流水线

---

## 一、结论

**可以迁移到 Tauri，但不建议现在直接改成“纯 Tauri + 纯 Rust 后端”。**

当前项目更适合的方案是：

**`Tauri Shell + React 前端 + 内置 Python FastAPI Sidecar + SQLite/本地文件存储`**

这个方案能满足“用户不需要手动安装前后端依赖，直接安装桌面包即可使用”的目标，同时最大限度复用现有代码，迁移风险也最低。

---

## 二、基于现状的判断依据

### 1. 前端已经具备接入 Tauri 的基础

- 当前前端是 `React + Vite + TypeScript`
- API 请求统一从 `frontend/src/services/api.ts` 发起，当前 `baseURL` 为相对路径 `/api`
- Vite 开发环境通过 `frontend/vite.config.ts` 把 `/api` 和 `/static` 代理到 `http://127.0.0.1:8000`

这意味着前端迁入 Tauri 时，不需要推倒重来，只需要把“请求目标地址”和“本地文件访问方式”抽象出来。

### 2. 后端天然更适合“被内置”，而不是被重写

- 当前新架构后端已经是 `FastAPI`
- 主入口 `backend/app/main.py` 已具备独立服务能力，包含生命周期、路由注册、静态资源挂载和健康检查
- 配置层 `backend/app/config.py` 已使用 `Pydantic Settings`
- 数据库存储已经切到本地 `SQLite`

这说明项目已经从“传统部署式 Web 服务”走向“可本地运行服务”，和桌面应用的运行模型是兼容的。

### 3. 核心业务明显依赖 Python 生态

当前业务能力大量依赖以下 Python 生态：

- `jieba`、`snownlp`、`wordcloud`
- `pandas`、`numpy`、`scikit-learn`
- `aiohttp`、`requests`
- `openai`、`zhipuai`

如果改成纯 Rust，等于把 NLP、词云、报告、爬虫、AI 接口整套业务重新实现一遍，成本高，回归风险也高，不符合当前项目阶段。

---

## 三、推荐架构

## 方案 A：推荐

### `Tauri + React + Python Sidecar`

运行方式：

1. Tauri 启动桌面窗口
2. Tauri 在本地启动一个内置 Python 后端进程
3. React 前端通过本地 HTTP 地址访问 FastAPI
4. FastAPI 继续负责：
   - 用户认证
   - 爬虫任务
   - 数据分析
   - AI 助手
   - 词云和报告生成
   - SQLite 与本地文件读写

### 优点

- 最大化复用现有前后端代码
- 用户无需自己安装 Python、Node、数据库
- 保留现有 API 架构，后续 Web 版和桌面版仍可共用后端
- 后续如果要保留浏览器版，不会被桌面化方案锁死

### 缺点

- 打包时需要处理 Python 运行时和依赖体积
- 不同平台的打包流程需要单独适配
- 桌面端首次启动速度会比纯前端壳稍慢

---

## 四、不推荐的方案

## 方案 B：纯 Tauri（Rust 重写后端）

不建议现在做，原因如下：

- 当前分析能力、词云、NLP、爬虫逻辑都在 Python
- 要重做数据处理链路和报告能力
- 需要重建 AI 接口封装
- 迁移周期长，且容易引入功能回退

只有在以下前提都成立时，才值得考虑：

- 你明确要彻底放弃 Web 部署形态
- 你愿意接受一次大规模后端重写
- 你优先追求极致体积和原生集成，而不是交付速度

---

## 五、当前项目进入 Tauri 前必须先处理的点

## 1. 后端路径不能继续按“当前工作目录”思维写

当前后端里仍有一些相对路径使用方式，例如：

- `backend/app/main.py` 中直接创建 `static`、`reports`
- 报告、词云等服务默认输出到相对目录

这在服务器部署时还能工作，但打包到桌面应用后，运行目录不稳定，容易出现：

- 报告写到错误目录
- 数据库位置漂移
- 静态资源找不到

### 需要调整为

- 统一由一个“应用数据根目录”生成：
  - 数据库目录
  - 报告目录
  - 词云目录
  - 日志目录
  - 上传目录

建议桌面版目录结构：

```text
AppData/PublicOpinion/
├── data/
├── database/
├── reports/
├── wordcloud/
├── logs/
└── config/
```

## 2. 前端请求地址要从“Vite 代理”切到“运行时感知”

当前前端通过：

- `frontend/src/services/api.ts` 里的 `/api`
- `frontend/vite.config.ts` 的本地代理

这只适合开发环境，不适合桌面打包。

### 需要调整为

- 开发环境：继续走 Vite 代理或环境变量
- Tauri 环境：走本地 Sidecar 服务地址，例如 `http://127.0.0.1:{动态端口}`

建议新增一层：

- `frontend/src/services/runtime.ts`
- `frontend/src/services/api-base.ts`

由运行时统一决定 API 根地址，避免后续把 Tauri 判断逻辑散落到各页面。

## 3. 设置页必须补齐桌面端配置闭环

当前 `frontend/src/pages/Settings.tsx` 的系统配置仍是只读展示，且文案明确写着“由环境变量控制，请联系管理员修改”。

这对桌面版不成立。

桌面版必须允许用户直接在设置界面管理：

- 本地数据目录
- AI 服务类型
- AI API Key / Base URL / Model ID
- 抖音 Cookie
- 后端运行状态
- 日志导出
- 报告导出目录
- 自动启动后端
- 自动更新开关

### 后端需要新增的接口

建议后续补充以下接口，并同步维护到 `/docs`：

- `GET /api/system/config`
- `PUT /api/system/config`
- `GET /api/system/runtime`
- `POST /api/system/runtime/restart`
- `GET /api/system/logs`

这些接口当前尚未实现，本次仅作为迁移施工建议。

## 4. 打包时需要处理 Python Runtime

桌面化后，用户不能再手动安装 Python 依赖，因此需要把 Python 运行环境一起分发。

推荐方式：

- macOS / Windows 分平台构建 Python 可执行包
- 再由 Tauri 作为 `sidecar` 启动

可选实现路径：

1. 使用 `PyInstaller`/`Nuitka` 先把 FastAPI 后端打成可执行文件
2. 再让 Tauri 调用该二进制

相比直接把裸 Python 环境塞进去，这种方式更利于分发。

## 5. 词云字体与系统依赖要显式处理

词云生成当前会按系统路径查找中文字体。

桌面化后，这种策略不稳定。建议：

- 将可分发的中文字体放入应用资源目录
- 词云服务优先使用内置字体路径
- 只有在找不到内置字体时，才回退到系统字体

否则不同平台上词云功能会出现：

- 无法生成图片
- 中文乱码
- 生成失败但前端只看到通用错误

---

## 六、推荐的实施顺序

## 阶段 1：把后端改成“可嵌入运行”的结构

目标：

- 所有输出目录配置化
- 所有运行路径统一收口
- 日志目录固定化
- 静态资源目录统一化

建议改动：

- 新增 `backend/app/core/paths.py`
- 新增 `backend/app/core/runtime_config.py`
- 把报告、词云、数据库、上传目录全部改为从路径模块读取

## 阶段 2：补齐桌面版设置闭环

目标：

- 用户可在前端设置页完成核心桌面配置
- 不再要求手改 `.env`

建议改动：

- 新增系统配置读写 API
- 设置页新增“桌面运行”板块
- 前端增加本地状态检测与错误提示

## 阶段 3：抽象前端 API 运行时

目标：

- 同一套前端同时支持浏览器版和 Tauri 版

建议改动：

- API 基地址抽象
- 静态资源 URL 抽象
- SSE/流式接口兼容本地服务地址

## 阶段 4：引入 Tauri 壳层

目标：

- 建立 `src-tauri`
- 打通开发模式和生产模式
- 实现后端 sidecar 启停与健康检查

建议能力：

- 启动时轮询 `/health`
- 关闭窗口时优雅停止后端
- 启动失败时显示故障恢复页面

## 阶段 5：打包与签名

目标：

- 产出真正可分发的安装包
- 用户安装后可直接使用

输出物：

- macOS `.dmg` / `.app`
- Windows `.msi` / `.exe`

---

## 七、成本和风险评估

## 预估复杂度

- 架构可行性：高
- 首版可交付性：中高
- 跨平台打包复杂度：中高
- 纯 Rust 重写必要性：低

## 主要风险

1. Python Sidecar 打包体积偏大
2. 多平台字体与文件权限差异
3. 本地端口占用与后端启动失败恢复
4. 抖音 Cookie、AI Key 等敏感配置需要本地安全存储
5. 当前部分路径和相对目录逻辑尚未完全桌面化

---

## 八、建议决策

如果你的目标是：

**“让用户像安装普通桌面软件一样直接使用，不再自己配前后端环境。”**

那么建议直接走：

**第一阶段目标：先做 `Tauri + 内置 Python FastAPI` 桌面版。**

不建议现在投入纯 Rust 重写。

---

## 九、本次评估后的下一步建议

如果继续推进，我建议下一轮直接做以下落地工作：

1. 初始化 `src-tauri`
2. 抽象前端 API 基地址
3. 收口后端路径配置
4. 设计并实现桌面版系统设置 API
5. 补 `/docs` 中新增的桌面配置接口文档

这样做能最快从“评估”进入“可运行原型”。

---

## 十、实施进展（2026-04-15）

本轮已经完成的落地工作：

1. **后端路径系统完成收口**
   - 新增 `backend/app/core/paths.py`
   - 新增 `backend/app/core/runtime_config.py`
   - `static`、`reports`、`wordcloud`、`database`、`upload`、`log` 目录统一改为由运行时配置解析

2. **桌面配置 API 已落地**
   - 新增 `GET /api/system/config`
   - 新增 `PUT /api/system/config`
   - 新增 `GET /api/system/runtime`
   - 设置页不再停留在“环境变量只读提示”

3. **前端运行时抽象已落地**
   - 新增 `frontend/src/services/runtime.ts`
   - `main.tsx` 启动时先加载运行时，再配置 API 客户端
   - Web 模式继续支持浏览器路由
   - Desktop 模式切换到 `HashRouter`

4. **设置页已完成桌面闭环改造**
   - 新增账户信息面板
   - 新增密码修改面板
   - 新增桌面系统配置面板
   - 支持保存 AI 配置、本地目录配置、后端重启、打开数据目录

5. **Tauri 工程已初始化**
   - 新增 `frontend/src-tauri`
   - Rust 壳层已实现：
     - 内置后端启动
     - 获取桌面运行时
     - 重启内置后端
     - 打开系统目录
     - 选择目录

6. **桌面后端打包脚本已落地**
   - 新增 `backend/run_desktop.py`
   - 新增 `backend/scripts/build_desktop_backend.sh`
   - 新增 `frontend/package.json` 中的：
     - `tauri:dev`
     - `tauri:build`
     - `tauri:build:backend`

7. **文档同步更新**
   - 新增 `docs/desktop_development.md`
   - 更新 `docs/api_documentation.md`
   - 更新 `frontend/README.md`

### 本轮验证状态

- Python 编译校验：已通过
- 前端生产构建：已通过
- Tauri Rust 编译：进行中，首次会拉取大量 crates，受磁盘空间和依赖下载速度影响较大

---

## Tauri 资源扫描故障修复（2026-04-15）

### 问题现象

在运行以下命令时：

- `cd frontend && npm run tauri:dev`
- `cd frontend && npm run tauri:build`

Rust 会在 `public_opinion_desktop` 的 `custom build command` 阶段失败，报错为：

- `Not a directory (os error 20)`

并指向：

- `frontend/src-tauri/resources/backend/public_opinion_backend/_internal/...`

最初暴露在：

- `三极泼墨体.ttf`

后续继续暴露在：

- `aiohttp/_helpers.cpython-312-darwin.so`

### 根因

问题不只是中文文件名，而是 `tauri-build` 会在开发态和默认构建态扫描 `bundle.resources`。

而当前 `resources/backend` 里放的是 `PyInstaller --onedir` 的完整 sidecar 目录，内部包含：

- `.so`
- `.dylib`
- 符号链接
- Python 运行时目录树

这类结构不适合被 `tauri-build` 在开发态递归扫描，因此会持续触发 `Not a directory` 一类异常。

### 修复方案

#### 1. 拆分 Tauri 配置

- 修改：
  - `frontend/src-tauri/tauri.conf.json`
- 新增：
  - `frontend/src-tauri/tauri.bundle.conf.json`

调整为：

- 默认配置不再声明 `bundle.resources`
- 只有正式打包时，才通过额外配置文件注入：
  - `resources/backend`

这样：

- `tauri dev` 不再扫描 sidecar 目录
- `tauri build` 仍能在正式打包时带上 sidecar

#### 2. 调整前端脚本

- 修改：
  - `frontend/package.json`

当前脚本行为：

- `npm run tauri:dev`
  - 使用默认配置，避免扫描 `resources/backend`
- `npm run tauri:build`
  - 先执行 `npm run tauri:build:backend`
  - 再执行：
    - `tauri build --config src-tauri/tauri.bundle.conf.json`

#### 3. 规避 sidecar 中的中文字体资源名

- 修改：
  - `backend/scripts/build_desktop_backend.sh`
  - `backend/app/services/wordcloud_generator.py`

处理方式：

- sidecar 内字体不再使用 `三极泼墨体.ttf`
- 改为 ASCII 文件名：
  - `sanjipomoti.ttf`
- 词云逻辑优先查找该新文件名

### 验证结果

- `npm run tauri:build:backend`：通过
- 新 sidecar 资源中已确认存在：
  - `frontend/src-tauri/resources/backend/public_opinion_backend/_internal/sanjipomoti.ttf`
- `npm run tauri:dev`：
  - 已验证不再在 `custom build command` 阶段报 `Not a directory (os error 20)`
  - 已进入正常 Rust 编译阶段

### 当前使用方式

- 开发模式：
  - `cd frontend && npm run tauri:dev`
- 正式打包：
  - `cd frontend && npm run tauri:build`

---

## 桌面端爬虫失效排查与大屏回退适配（2026-04-16）

### 排查结论

本轮不是“前端按钮没反应”，而是桌面端后端确实收到了请求、也创建了任务，但微博采集阶段被接口风控拦截。

实际桌面运行时数据位置：

- 日志：
  - `~/Library/Application Support/com.publicopinion.desktop/logs/backend.log`
- 数据库：
  - `~/Library/Application Support/com.publicopinion.desktop/database/public_opinion.db`

日志中的真实错误为：

- 微博分页请求连续返回 `HTTP 432`
- 最终没有拿到任何微博数据

原先的问题在于：

- 后端把“0 条数据”错误标记成了 `completed`
- 前端因此只能看到任务结束，但没有结果，也没有明确报错

### 本次修复

#### 1. 微博风控失败改为真实失败状态

- 修改：
  - `backend/app/services/weibo_spider.py`

修复内容：

- 新增 `last_error`
- 遇到 `HTTP 432` 时写入明确错误：
  - 需要在设置页补充可用微博 Cookie
- 当最终没有拿到任何数据时，不再返回伪成功，而是直接抛出异常

这样任务会被后端标记为：

- `failed`

并保留明确 `error_message`

#### 2. 设置页补齐微博 Cookie 配置

- 修改：
  - `backend/app/schemas/system.py`
  - `backend/app/core/runtime_config.py`
  - `backend/app/config.py`
  - `frontend/src/types/index.ts`
  - `frontend/src/components/settings/SystemSettingsPanel.tsx`

新增：

- `weibo_cookie`

现在用户可以直接在桌面设置页填写微博 Cookie，而不需要手动修改环境变量或源码。

#### 3. 大数据看板按旧版结构回退

- 修改：
  - `frontend/src/pages/BigData.tsx`
  - `frontend/src/pages/BigData.module.css`

调整方式：

- 采用旧版 `views/page/templates/bigdata.html` 的六块布局结构：
  - 中国热力图
  - 情感分析
  - 性别分布
  - 预警提示
  - 时事热点
  - 实时监测
- 仅对数据源做 React/接口适配

### 验证

- `./.venv/bin/python -m compileall backend/app backend/run_desktop.py`：通过
- `cd frontend && npm run build`：通过

### 当前说明

如果微博继续返回 `HTTP 432`，现在前端不再表现成“没反应”，而会展示明确失败原因。下一步使用时，需要在设置页填写可用微博 Cookie，再重新执行采集任务。

### 补充验证

为避免误判为“新后端回归”，本轮还直接验证了旧版微博脚本：

- 文件：
  - `spiders/articles_spider.py`
- 直接运行结果：
- 旧脚本当前环境下同样拿不到数据
- 原始 `requests.get()` 对 `m.weibo.cn/api/container/getIndex` 的最小测试结果：
  - `HTTP 432`
- 按抓包反向补齐最新访客链后再次测试：
  - 已不再返回 `432`
  - 但微博搜索接口真实返回：
    - `{"ok":-100,"url":"https://passport.weibo.com/sso/signin?..."}`

结论是：

- 不是当前 Tauri/FastAPI 改造把原本可用的“无 Cookie 微博爬虫”改坏了
- 而是当前微博接口环境已经变化，旧脚本在这台机器和当前时间点下也同样无法无 Cookie 取数
- 并且在最新访客入口下，官方搜索接口仍要求登录态

### 新增兼容处理

- `backend/app/services/weibo_spider.py`

现在微博爬虫会：

1. 优先使用设置页填写的 `weibo_cookie`
2. 若未配置，再自动执行：
   - `passport.weibo.com/visitor/genvisitor`
   - `passport.weibo.com/visitor/visitor`
   - `m.weibo.cn/search` 预热
3. 如果官方仍返回 `ok:-100`，则明确提示：
   - 需要有效微博 Cookie

---

## 中国热力图真实可视化补齐（2026-04-16）

### 目标

不再把“中国热力图”停留在文字占位态，而是接入真正的中国地图可视化，并打通省份数据从爬虫到接口再到前端的链路。

### 本次改动

#### 1. 数据模型补齐省份/性别字段

- 修改：
  - `backend/app/models/weibo.py`
  - `backend/app/models/douyin.py`

新增字段用于支持大屏统计：

- `province`
- `city`
- `gender`
- 以及微博的 `country`
- 抖音的 `followers_count`

#### 2. SQLite 老库自动补列

- 修改：
  - `backend/app/database.py`

处理方式：

- 在 `init_db()` 后增加 `PRAGMA table_info`
- 对桌面端旧数据库自动执行 `ALTER TABLE ... ADD COLUMN`

这样不需要手工删库重建，老桌面库也能自动补齐新字段。

#### 3. 爬虫写入地域与画像字段

- 修改：
  - `backend/app/services/weibo_spider.py`
  - `backend/app/services/douyin_spider.py`

现在新采集数据会写入：

- 省份
- 城市
- 性别

#### 4. 图表接口返回真实省份热力数据

- 修改：
  - `backend/app/routers/page.py`

现在 `/api/page/chart-data` 会：

- 聚合微博与抖音的省份字段
- 规范化省份名称
- 返回 ECharts 可直接使用的：
  - `[{ name, value }]`

#### 5. 前端接入 ECharts 中国地图

- 新增：
  - `frontend/src/components/charts/ChinaHeatmap.tsx`
- 修改：
  - `frontend/src/components/charts/index.ts`
  - `frontend/src/pages/BigData.tsx`

实现方式：

- 前端引入 `echarts`
- 运行时加载已有：
  - `/static/assets/js/china.js`
- 在大数据看板中真实渲染中国地图热力图

### 验证

- `./.venv/bin/python -m compileall backend/app backend/run_desktop.py`：通过
- `cd frontend && npm run build`：通过

### 当前限制

地图现在已经是真实可视化，但能否显示出热区，仍取决于数据库里是否已经有带省份字段的新采集数据。

也就是说：

- 旧历史数据如果没有 `province`
- 或微博采集仍被 `HTTP 432` 拦截

则地图仍可能为空，但这时前后端链路已经是完整的，后续只差真实数据进入库中。

---

## 手册页 Markdown 真渲染补齐（2026-04-16）

### 问题

此前手册页虽然读取了真实 `.md` 文件，但前端只是自己按行拆分标题和段落，不能正确渲染：

- 目录锚点
- 列表层级
- 表格
- 代码块
- 原始 HTML
- 内嵌图片

### 本次改动

- 新增依赖：
  - `react-markdown`
  - `remark-gfm`
  - `rehype-raw`
- 修改：
  - `frontend/src/pages/Manual.tsx`
  - `frontend/src/pages/Manual.module.css`

### 结果

手册页现在会对真实 Markdown 正文做标准渲染，而不再是假解析文本。

---

## 微博连接测试 UI 闭环与看板视觉升级（2026-04-16）

### 目标

把“微博自动访客 / 登录 Cookie 回退”的策略显式暴露给用户，并继续提升大数据看板的成品感。

### 本次改动

#### 1. 设置页新增微博连接测试闭环

- 后端新增接口：
  - `GET /api/system/weibo-connection-test`
- 修改：
  - `backend/app/routers/system.py`
  - `frontend/src/services/system.ts`
  - `frontend/src/types/index.ts`
  - `frontend/src/components/settings/SystemSettingsPanel.tsx`
  - `frontend/src/components/settings/SettingsPanels.module.css`

功能效果：

- 设置页现在会明确说明：
  - 默认自动访客模式
  - 若官方接口仍要求登录态，再回退使用用户粘贴的完整 Cookie header
- 新增“测试微博连接”按钮
- 测试结果会直接展示：
  - 当前模式（访客 / Cookie）
  - 可否取到样本
  - 当前失败原因

#### 2. 爬虫页增加模式提示

- 修改：
  - `frontend/src/pages/Spider.tsx`
  - `frontend/src/pages/Spider.module.css`

效果：

- 在爬虫页顶部增加信息提示条
- 当任务错误里出现“要求登录态”时，会明确提示去设置页补 Cookie

#### 3. 大数据看板继续做成品化视觉升级

- 修改：
  - `frontend/src/pages/BigData.tsx`
  - `frontend/src/pages/BigData.module.css`

本轮提升：

- 增加顶部 eyebrow、说明文案、时钟和指标带
- 卡片层级、边界、阴影、悬浮反馈进一步优化
- 整体观感从“功能容器”提升到更接近成品大屏

### 验证

- `./.venv/bin/python -m compileall backend/app`：通过
- `cd frontend && npm run build`：通过
