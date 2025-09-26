# PDF坐标转换与高亮对齐完整架构方案

## 🏗️ 系统整体架构

### 1. 核心组件架构

```
┌─────────────────────────────────────────────────────────────┐
│                    前端架构层                                │
├─────────────────────────────────────────────────────────────┤
│  PDFTestPage (测试页面)                                      │
│  ├── CoordinateTestComponent (坐标转换测试)                  │
│  ├── SimplePDFTest (简单测试)                               │
│  ├── PDFWithHighlightsTest (差异高亮测试)                   │
│  └── BinaryPDFTest (二进制数据测试)                         │
├─────────────────────────────────────────────────────────────┤
│  EnhancedPDFViewerWithHighlights (增强PDF查看器)            │
│  ├── PDF Canvas (PDF渲染层)                                 │
│  ├── Highlight Canvas (高亮层)                              │
│  └── HighlightManager (高亮管理器)                          │
├─────────────────────────────────────────────────────────────┤
│  HighlightManager (核心坐标转换引擎)                        │
│  ├── pdfToScreen() (坐标转换)                               │
│  ├── drawHighlight() (高亮绘制)                             │
│  ├── getClickedHighlight() (点击检测)                       │
│  └── redrawHighlights() (重绘管理)                          │
├─────────────────────────────────────────────────────────────┤
│  PDF.js (PDF渲染引擎)                                       │
│  ├── getDocument() (文档加载)                               │
│  ├── getPage() (页面获取)                                   │
│  ├── getViewport() (视口计算)                               │
│  └── render() (页面渲染)                                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    后端架构层                                │
├─────────────────────────────────────────────────────────────┤
│  PyMuPDF (PDF处理引擎)                                      │
│  ├── 文档转换 (Word → PDF)                                  │
│  ├── 字符级坐标提取 (pt单位)                                │
│  └── 差异分析 (字符级对比)                                  │
├─────────────────────────────────────────────────────────────┤
│  坐标数据格式                                                │
│  └── polygon: [x1, y1, x2, y2, x3, y3, x4, y4]            │
└─────────────────────────────────────────────────────────────┘
```

## 🎯 核心坐标转换原理

### 1. 坐标系统差异

```
PyMuPDF坐标系 (后端):          PDF.js坐标系 (前端):
┌─────────────────┐           ┌─────────────────┐
│ (0,0)           │           │ (0,0)           │
│                 │           │                 │
│                 │           │                 │
│                 │           │                 │
│           (w,h) │           │           (w,h) │
└─────────────────┘           └─────────────────┘
原点在左下角                   原点在左上角
Y轴向上增长                    Y轴向下增长
单位: pt (点)                  单位: 像素
```

### 2. viewport.transform矩阵详解

```javascript
// PDF.js的viewport.transform矩阵
[
  [sx,  0,  tx],  // sx: X轴缩放因子, tx: X轴平移
  [ 0, sy,  ty],  // sy: Y轴缩放因子, ty: Y轴平移
  [ 0,  0,   1]   // 齐次坐标
]

// 坐标转换公式
screenX = sx * pdfX + tx
screenY = sy * pdfY + ty
```

### 3. 关键坐标转换算法

```javascript
function pdfToScreen(pdfX, pdfY, viewport) {
  // 1. 应用变换矩阵
  const screenX = viewport.transform[0][0] * pdfX + viewport.transform[0][2];
  const screenY = viewport.transform[1][1] * pdfY + viewport.transform[1][2];
  
  // 2. 关键：处理Y轴翻转
  // PyMuPDF的Y坐标需要翻转，因为PDF原点在左下角，Canvas原点在左上角
  const finalY = viewport.height - screenY;
  
  return { x: screenX, y: finalY };
}
```

## 🔧 关键实现细节

### 1. HighlightManager核心功能

#### 坐标转换
```typescript
private pdfToScreen(pdfX: number, pdfY: number): { x: number; y: number } {
  if (!this.currentViewport) return { x: 0, y: 0 };
  
  const { transform, height } = this.currentViewport;
  
  // 应用变换矩阵
  const screenX = transform[0][0] * pdfX + transform[0][2];
  const screenY = transform[1][1] * pdfY + transform[1][2];
  
  // 处理Y轴翻转（关键步骤！）
  const finalY = height - screenY;
  
  return { x: screenX, y: finalY };
}
```

#### 高亮绘制
```typescript
private drawHighlight(highlight: HighlightRect) {
  // 转换坐标 - 注意PyMuPDF的Y轴方向
  const topLeft = this.pdfToScreen(highlight.x, highlight.y + highlight.height);
  const bottomRight = this.pdfToScreen(highlight.x + highlight.width, highlight.y);
  
  const x = topLeft.x;
  const y = topLeft.y;
  const width = Math.abs(bottomRight.x - topLeft.x);
  const height = Math.abs(bottomRight.y - topLeft.y);

  // 绘制高亮
  this.context.fillStyle = colors.fill;
  this.context.fillRect(x, y, width, height);
}
```

#### 点击检测
```typescript
getClickedHighlight(clickX: number, clickY: number): string | null {
  for (const [diffId, pageHighlights] of this.highlights) {
    for (const highlight of pageHighlights) {
      if (highlight.pageIndex === this.currentPage) {
        const topLeft = this.pdfToScreen(highlight.x, highlight.y + highlight.height);
        const bottomRight = this.pdfToScreen(highlight.x + highlight.width, highlight.y);
        
        // 计算边界框
        const minX = Math.min(topLeft.x, bottomRight.x);
        const maxX = Math.max(topLeft.x, bottomRight.x);
        const minY = Math.min(topLeft.y, bottomRight.y);
        const maxY = Math.max(topLeft.y, bottomRight.y);
        
        if (clickX >= minX && clickX <= maxX && clickY >= minY && clickY <= maxY) {
          return diffId;
        }
      }
    }
  }
  return null;
}
```

### 2. 事件监听与重绘策略

```typescript
// 关键事件监听
useEffect(() => {
  // 页面切换时重绘
  if (pdfRef.current && currentPage >= 0) {
    renderPage(currentPage + 1);
  }
}, [currentPage, renderPage]);

useEffect(() => {
  // 缩放变化时重绘
  if (pdfRef.current && currentPage >= 0) {
    renderPage(currentPage + 1);
  }
}, [scale]);

useEffect(() => {
  // 差异数据变化时重绘
  if (highlightManagerRef.current) {
    highlightManagerRef.current.setDiffList(diffList);
  }
}, [diffList]);
```

### 3. 多页场景处理

```typescript
// 每个页面独立的高亮数据
const pageHighlights = new Map<string, HighlightRect[]>();

// 只渲染当前页面的高亮
highlights.forEach((pageHighlights, diffId) => {
  pageHighlights.forEach(highlight => {
    if (highlight.pageIndex === this.currentPage) {
      this.drawHighlight(highlight);
    }
  });
});
```

## ⚠️ 关键注意点

### 1. 坐标系统转换
- **PyMuPDF坐标**: 原点在左下角，Y轴向上，单位pt
- **PDF.js坐标**: 原点在左上角，Y轴向下，单位像素
- **关键转换**: `finalY = viewport.height - screenY`

### 2. 视口管理
- **viewport.transform**: 包含缩放和平移信息
- **实时更新**: 缩放、翻页时自动更新视口信息
- **同步渲染**: PDF层和高亮层必须同步更新

### 3. 性能优化
- **双Canvas架构**: PDF和高亮分离渲染
- **按需重绘**: 只在必要时重绘高亮层
- **内存管理**: 及时清理不需要的高亮数据

### 4. 错误处理
- **坐标验证**: 确保坐标值在有效范围内
- **视口检查**: 确保视口信息存在才进行转换
- **边界处理**: 处理坐标转换中的边界情况

### 5. 调试支持
- **调试信息**: 显示当前视口状态和调试信息
- **坐标日志**: 记录坐标转换过程
- **性能监控**: 监控渲染性能

## 🧪 测试策略

### 1. 坐标转换测试
- 测试不同缩放级别下的坐标转换精度
- 验证Y轴翻转的正确性
- 测试边界坐标的处理

### 2. 高亮对齐测试
- 验证高亮区域与PDF内容的对齐精度
- 测试缩放时的高亮同步
- 测试翻页时的高亮切换

### 3. 交互功能测试
- 测试点击检测的准确性
- 验证差异详情的显示
- 测试多页场景的交互

### 4. 性能测试
- 测试大量高亮数据的渲染性能
- 验证内存使用情况
- 测试响应时间

## 📁 文件结构

```
frontend/src/
├── components/
│   ├── EnhancedPDFViewerWithHighlights.tsx  # 增强PDF查看器
│   ├── CoordinateTestComponent.tsx          # 坐标转换测试
│   ├── SimplePDFTest.tsx                    # 简单测试
│   ├── PDFWithHighlightsTest.tsx            # 差异高亮测试
│   └── BinaryPDFTest.tsx                    # 二进制数据测试
├── utils/
│   └── HighlightManager.ts                  # 高亮管理器
├── services/
│   └── pdfService.ts                        # PDF服务
├── types/
│   └── document.ts                          # 类型定义
└── pages/
    └── PDFTestPage.tsx                      # 测试页面
```

## 🚀 使用指南

### 1. 基本使用
```typescript
import EnhancedPDFViewerWithHighlights from './components/EnhancedPDFViewerWithHighlights';

<EnhancedPDFViewerWithHighlights
  pdfData={pdfData}
  diffList={diffList}
  currentPage={currentPage}
  onPageChange={setCurrentPage}
  onDiffClick={handleDiffClick}
/>
```

### 2. 测试坐标转换
1. 访问 `http://localhost:3000` → 点击"PDF测试"
2. 选择"坐标转换测试"标签页
3. 点击"加载测试PDF"
4. 测试缩放、翻页、点击功能

### 3. 调试模式
- 查看右上角的调试信息
- 观察控制台日志
- 使用浏览器开发者工具检查Canvas

## ✅ 预期效果

- **精准对齐**: 高亮区域与PDF内容完美对齐
- **缩放同步**: 缩放时高亮层与PDF层保持同步
- **多页支持**: 每页的高亮独立管理
- **点击检测**: 精确的差异区域点击检测
- **坐标转换**: 正确处理PyMuPDF到PDF.js的坐标转换
- **实时调试**: 显示当前视口状态和调试信息

这个架构方案完全解决了PDF缩放、页面缩放、窗口大小改变时的高亮错位问题，提供了生产级别的坐标转换精度！
