# GitHub Action 构建报错修复施工文档

## 文档信息

- 任务日期：2026-04-16
- 任务目标：修复 `frontend` 在 GitHub Actions / Tauri 打包流程中因 TypeScript 严格检查导致的构建失败
- 影响范围：前端页面、类型定义、服务层、构建稳定性记录

---

## 本轮问题概述

`release.yml` 在执行前端 `npm run build` 时被 `tsc` 拦截，主要错误分为两类：

1. 多处未使用导入或形参触发 `TS6133`
2. `BigData` 页面访问 `RealtimeMonitoringItem.link/url`，但前端类型仅声明了 `Link`，触发 `TS2551` / `TS2339`

这些问题都属于“本地运行可能没感觉，但 CI 严格构建必炸”的典型问题。

---

## 本次实施内容

### 1. 清理无效导入与无效符号

- 文件：
  - `frontend/src/components/charts/ChinaHeatmap.tsx`
  - `frontend/src/components/layout/Sidebar.tsx`
  - `frontend/src/components/spider/ScheduledJobsPanel.tsx`
  - `frontend/src/pages/Spider.tsx`
- 处理：
  - 删除未使用的 `resolveBackendUrl`
  - 删除未使用的 `BarChart`、`Search`
  - 删除未使用的 `useRef`、`createScheduledJob`
  - 删除 `Spider.tsx` 中未使用的 `createSpiderTask`

### 2. 修复实时监测链接字段的类型与使用不一致

- 文件：
  - `frontend/src/types/index.ts`
  - `frontend/src/pages/BigData.tsx`
- 处理：
  - 为 `RealtimeMonitoringItem` 增补 `link`、`url` 可选字段，兼容现有页面中的多来源字段读取
  - 在 `BigData` 页面抽出 `resolveMonitoringLink()`，统一归一链接解析逻辑，避免散落的字段兜底判断

### 3. 消除服务层无效参数告警

- 文件：
  - `frontend/src/services/page.ts`
- 处理：
  - 将 `forceGenerateWordcloud` 的入参改为带默认值的实际使用参数，消除未使用形参告警，同时保持原接口调用方式不变

---

## 风险评估

- 本轮未改动后端接口行为
- 前端对实时监测链接的处理变得更稳健，只是补充兼容，不会破坏现有返回结构
- 其余修改均为静态清理，不影响已有业务逻辑

---

## 验证计划

- 执行：`cd frontend && npm run build`
- 目标：确保本地与 GitHub Action 同口径的前端构建通过

## 本次验证结果

- `cd frontend && npm run build`：通过
- 补充观察：
  - 当前 `vite build` 仍提示部分 chunk 超过 `500 kB`
  - 该项为打包体积告警，不会导致 GitHub Action 失败
  - 若后续继续优化发布稳定性，可再单独做前端按路由或图表能力拆包
