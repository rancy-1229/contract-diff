import React, { useRef, useEffect, useCallback, useState } from 'react';
import { DiffItem } from '../types/document';

interface HighlightRendererProps {
  diffList: DiffItem[];
  pageIndex: number;
  scale: number;
  canvasWidth: number;
  canvasHeight: number;
  onDiffClick: (diff: DiffItem) => void;
  className?: string;
  style?: React.CSSProperties;
}

interface HighlightStyle {
  color: string;
  opacity: number;
  strokeColor: string;
  strokeWidth: number;
}

// 差异类型对应的样式配置
const DIFF_STYLES: Record<string, HighlightStyle> = {
  ADD: {
    color: '#52c41a',
    opacity: 0.3,
    strokeColor: '#52c41a',
    strokeWidth: 1
  },
  DELETE: {
    color: '#ff4d4f',
    opacity: 0.3,
    strokeColor: '#ff4d4f',
    strokeWidth: 1
  },
  MODIFY: {
    color: '#faad14',
    opacity: 0.3,
    strokeColor: '#faad14',
    strokeWidth: 1
  },
  MOVE: {
    color: '#1890ff',
    opacity: 0.3,
    strokeColor: '#1890ff',
    strokeWidth: 1
  }
};

// 坐标转换工具类
class CoordinateTransformer {
  /**
   * 将PDF坐标转换为Canvas坐标
   * @param pdfCoords PDF坐标 [x0, y0, x1, y1]
   * @param pageWidth PDF页面宽度
   * @param pageHeight PDF页面高度
   * @param canvasWidth Canvas宽度
   * @param canvasHeight Canvas高度
   * @param scale 缩放比例
   * @returns Canvas坐标 [x0, y0, x1, y1]
   */
  static pdfToCanvas(
    pdfCoords: [number, number, number, number],
    pageWidth: number,
    pageHeight: number,
    canvasWidth: number,
    canvasHeight: number,
    scale: number
  ): [number, number, number, number] {
    const [x0, y0, x1, y1] = pdfCoords;
    
    // 计算缩放比例
    const scaleX = (canvasWidth / pageWidth) * scale;
    const scaleY = (canvasHeight / pageHeight) * scale;
    
    return [
      x0 * scaleX,
      y0 * scaleY,
      x1 * scaleX,
      y1 * scaleY
    ];
  }

  /**
   * 检查点是否在矩形内
   * @param point 点坐标 [x, y]
   * @param rect 矩形坐标 [x0, y0, x1, y1]
   * @returns 是否在矩形内
   */
  static isPointInRect(
    point: [number, number],
    rect: [number, number, number, number]
  ): boolean {
    const [x, y] = point;
    const [x0, y0, x1, y1] = rect;
    return x >= x0 && x <= x1 && y >= y0 && y <= y1;
  }
}

const HighlightRenderer: React.FC<HighlightRendererProps> = ({
  diffList,
  pageIndex,
  scale,
  canvasWidth,
  canvasHeight,
  onDiffClick,
  className,
  style
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [hoveredDiff, setHoveredDiff] = useState<DiffItem | null>(null);

  // 绘制单个高亮
  const drawHighlight = useCallback((
    ctx: CanvasRenderingContext2D,
    diff: DiffItem,
    style: HighlightStyle,
    isHovered: boolean = false
  ) => {
    // 获取差异的坐标信息
    const charDiffs = diff.diff || [];
    
    charDiffs.forEach(charGroup => {
      charGroup.forEach(charInfo => {
        if (charInfo.page_index === pageIndex) {
          const charPolygons = charInfo.char_polygons || [];
          
          charPolygons.forEach(polygon => {
            if (polygon.length >= 4) {
              const [x0, y0, x1, y1] = polygon;
              
              // 设置样式
              ctx.fillStyle = style.color;
              ctx.globalAlpha = isHovered ? style.opacity * 1.5 : style.opacity;
              ctx.strokeStyle = style.strokeColor;
              ctx.lineWidth = isHovered ? style.strokeWidth * 2 : style.strokeWidth;
              
              // 绘制高亮矩形
              const width = x1 - x0;
              const height = y1 - y0;
              ctx.fillRect(x0, y0, width, height);
              ctx.strokeRect(x0, y0, width, height);
              
              // 重置透明度
              ctx.globalAlpha = 1.0;
            }
          });
        }
      });
    });
  }, [pageIndex]);

  // 渲染所有高亮
  const renderHighlights = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    // 设置Canvas尺寸
    canvas.width = canvasWidth;
    canvas.height = canvasHeight;
    
    // 清除画布
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // 获取当前页面的差异
    const pageDiffs = diffList.filter(diff => diff.page_index === pageIndex);
    
    // 绘制高亮
    pageDiffs.forEach(diff => {
      const style = DIFF_STYLES[diff.status] || DIFF_STYLES.ADD;
      const isHovered = hoveredDiff?.element_id === diff.element_id;
      drawHighlight(ctx, diff, style, isHovered);
    });
    
    console.log(`[HighlightRenderer] 页面 ${pageIndex} 渲染了 ${pageDiffs.length} 个高亮`);
  }, [diffList, pageIndex, canvasWidth, canvasHeight, drawHighlight, hoveredDiff]);

  // 查找点击的差异
  const findClickedDiff = useCallback((
    x: number,
    y: number
  ): DiffItem | null => {
    const pageDiffs = diffList.filter(diff => diff.page_index === pageIndex);
    
    for (const diff of pageDiffs) {
      const charDiffs = diff.diff || [];
      
      for (const charGroup of charDiffs) {
        for (const charInfo of charGroup) {
          if (charInfo.page_index === pageIndex) {
            const charPolygons = charInfo.char_polygons || [];
            
            for (const polygon of charPolygons) {
              if (polygon.length >= 4) {
                const [x0, y0, x1, y1] = polygon;
                
                if (CoordinateTransformer.isPointInRect([x, y], [x0, y0, x1, y1])) {
                  return diff;
                }
              }
            }
          }
        }
      }
    }
    
    return null;
  }, [diffList, pageIndex]);

  // 处理Canvas点击事件
  const handleCanvasClick = useCallback((event: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    
    const clickedDiff = findClickedDiff(x, y);
    if (clickedDiff) {
      console.log(`[HighlightRenderer] 点击了差异: ${clickedDiff.element_id}`);
      onDiffClick(clickedDiff);
    }
  }, [findClickedDiff, onDiffClick]);

  // 处理鼠标移动事件（悬停效果）
  const handleMouseMove = useCallback((event: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    
    const hovered = findClickedDiff(x, y);
    setHoveredDiff(hovered);
    
    // 更新鼠标样式
    canvas.style.cursor = hovered ? 'pointer' : 'default';
  }, [findClickedDiff]);

  // 处理鼠标离开事件
  const handleMouseLeave = useCallback(() => {
    setHoveredDiff(null);
    const canvas = canvasRef.current;
    if (canvas) {
      canvas.style.cursor = 'default';
    }
  }, []);

  // 渲染高亮
  useEffect(() => {
    renderHighlights();
  }, [renderHighlights]);

  return (
    <canvas
      ref={canvasRef}
      className={className}
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        pointerEvents: 'auto',
        zIndex: 10,
        ...style
      }}
      onClick={handleCanvasClick}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    />
  );
};

export default HighlightRenderer;
