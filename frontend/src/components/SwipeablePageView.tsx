import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Tag } from 'antd';

interface SwipeablePageViewProps {
  standardImages: string[];
  targetImages: string[];
  currentPage: number;
  onPageChange: (page: number) => void;
  className?: string;
}

const SwipeablePageView: React.FC<SwipeablePageViewProps> = ({
  standardImages,
  targetImages,
  currentPage,
  onPageChange,
  className = ''
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  // const [isScrolling] = useState(false); // 未使用
  // const [scrollTimeout] = useState<number | null>(null); // 未使用
  const [touchStartY, setTouchStartY] = useState(0);
  const [touchStartTime, setTouchStartTime] = useState(0);
  const [isTransitioning, setIsTransitioning] = useState(false);

  const maxPage = Math.max(standardImages.length, targetImages.length) - 1;

  // 处理滚轮事件
  const handleWheel = useCallback((e: WheelEvent) => {
    e.preventDefault();
    
    if (isTransitioning) return;
    
    const deltaY = e.deltaY;
    const threshold = 50; // 滚动阈值
    
    if (Math.abs(deltaY) > threshold) {
      if (deltaY > 0 && currentPage < maxPage) {
        // 向下滚动，下一页
        handlePageChange(currentPage + 1);
      } else if (deltaY < 0 && currentPage > 0) {
        // 向上滚动，上一页
        handlePageChange(currentPage - 1);
      }
    }
  }, [currentPage, maxPage, isTransitioning]);

  // 处理触摸开始
  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    setTouchStartY(e.touches[0].clientY);
    setTouchStartTime(Date.now());
  }, []);

  // 处理触摸结束
  const handleTouchEnd = useCallback((e: React.TouchEvent) => {
    if (isTransitioning) return;
    
    const touchEndY = e.changedTouches[0].clientY;
    const touchEndTime = Date.now();
    const deltaY = touchStartY - touchEndY;
    const deltaTime = touchEndTime - touchStartTime;
    
    // 判断是否为有效的滑动手势
    const minSwipeDistance = 50;
    const maxSwipeTime = 500;
    
    if (Math.abs(deltaY) > minSwipeDistance && deltaTime < maxSwipeTime) {
      if (deltaY > 0 && currentPage < maxPage) {
        // 向上滑动，下一页
        handlePageChange(currentPage + 1);
      } else if (deltaY < 0 && currentPage > 0) {
        // 向下滑动，上一页
        handlePageChange(currentPage - 1);
      }
    }
  }, [touchStartY, touchStartTime, currentPage, maxPage, isTransitioning]);

  // 处理键盘事件
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (isTransitioning) return;
    
    switch (e.key) {
      case 'ArrowDown':
      case 'PageDown':
        e.preventDefault();
        if (currentPage < maxPage) {
          handlePageChange(currentPage + 1);
        }
        break;
      case 'ArrowUp':
      case 'PageUp':
        e.preventDefault();
        if (currentPage > 0) {
          handlePageChange(currentPage - 1);
        }
        break;
      case 'Home':
        e.preventDefault();
        handlePageChange(0);
        break;
      case 'End':
        e.preventDefault();
        handlePageChange(maxPage);
        break;
    }
  }, [currentPage, maxPage, isTransitioning]);

  // 页面切换处理
  const handlePageChange = useCallback((newPage: number) => {
    if (newPage < 0 || newPage > maxPage || newPage === currentPage || isTransitioning) {
      return;
    }
    
    setIsTransitioning(true);
    onPageChange(newPage);
    
    // 重置过渡状态
    setTimeout(() => {
      setIsTransitioning(false);
    }, 300);
  }, [currentPage, maxPage, isTransitioning, onPageChange]);

  // 添加事件监听器
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    container.addEventListener('wheel', handleWheel, { passive: false });
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      container.removeEventListener('wheel', handleWheel);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleWheel, handleKeyDown]);

  // 清理定时器
  useEffect(() => {
    return () => {
      if (scrollTimeout) {
        clearTimeout(scrollTimeout);
      }
    };
  }, [scrollTimeout]);

  return (
    <div
      ref={containerRef}
      className={`swipeable-page-view ${className}`}
      style={{
        height: '100%',
        width: '100%',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
        overflow: 'hidden',
        userSelect: 'none',
        touchAction: 'pan-y',
        margin: 0,
        padding: 0
      }}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
    >
      {/* 页面指示器 - 右上角 */}
      <div style={{
        position: 'absolute',
        top: '20px',
        right: '20px',
        zIndex: 100,
        background: 'rgba(0, 0, 0, 0.7)',
        color: 'white',
        padding: '8px 16px',
        borderRadius: '20px',
        fontSize: '14px',
        fontWeight: 'bold',
        backdropFilter: 'blur(10px)',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.3)'
      }}>
        {currentPage + 1} / {maxPage + 1}
      </div>

      {/* 翻页提示 */}
      {currentPage > 0 && (
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '20px',
          transform: 'translateY(-50%)',
          zIndex: 50,
          background: 'rgba(0, 0, 0, 0.6)',
          color: 'white',
          padding: '12px 16px',
          borderRadius: '8px',
          fontSize: '12px',
          backdropFilter: 'blur(10px)',
          animation: 'fadeInOut 2s infinite'
        }}>
          ↑ 上一页
        </div>
      )}

      {currentPage < maxPage && (
        <div style={{
          position: 'absolute',
          bottom: '20px',
          left: '50%',
          transform: 'translateX(-50%)',
          zIndex: 50,
          background: 'rgba(0, 0, 0, 0.6)',
          color: 'white',
          padding: '12px 16px',
          borderRadius: '8px',
          fontSize: '12px',
          backdropFilter: 'blur(10px)',
          animation: 'fadeInOut 2s infinite'
        }}>
          ↓ 下一页
        </div>
      )}

      {/* 主要内容区域 */}
      <div style={{
        flex: 1,
        display: 'flex',
        background: '#f5f5f5',
        transition: isTransitioning ? 'transform 0.3s ease-in-out' : 'none',
        width: '100%',
        height: '100%',
        margin: 0,
        padding: 0
      }}>
        {/* 标准文档 */}
        <div style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          position: 'relative',
          overflow: 'hidden',
          borderRight: '2px solid #e8e8e8'
        }}>
          {/* 文档标签 */}
          <div style={{
            position: 'absolute',
            top: '16px',
            left: '16px',
            zIndex: 20
          }}>
            <Tag color="blue" style={{
              fontSize: '14px',
              padding: '6px 12px',
              fontWeight: 'bold',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)'
            }}>
              标准文档
            </Tag>
          </div>

          {/* 图片显示 */}
          <div style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '40px 5px 5px',
            overflow: 'auto',
            width: '100%',
            height: '100%'
          }}>
            {standardImages[currentPage] && (
              <img
                src={standardImages[currentPage]}
                alt={`标准文档页面 ${currentPage + 1}`}
                style={{
                  maxWidth: '100%',
                  maxHeight: '100%',
                  height: 'auto',
                  objectFit: 'contain',
                  display: 'block',
                  boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
                  borderRadius: '8px',
                  transition: 'transform 0.2s ease'
                }}
                onLoad={() => {
                  // 图片加载完成后的处理
                }}
              />
            )}
          </div>
        </div>

        {/* 目标文档 */}
        <div style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          position: 'relative',
          overflow: 'hidden'
        }}>
          {/* 文档标签 */}
          <div style={{
            position: 'absolute',
            top: '16px',
            left: '16px',
            zIndex: 20
          }}>
            <Tag color="green" style={{
              fontSize: '14px',
              padding: '6px 12px',
              fontWeight: 'bold',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)'
            }}>
              目标文档
            </Tag>
          </div>

          {/* 图片显示 */}
          <div style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '40px 5px 5px',
            overflow: 'auto',
            width: '100%',
            height: '100%'
          }}>
            {targetImages[currentPage] && (
              <img
                src={targetImages[currentPage]}
                alt={`目标文档页面 ${currentPage + 1}`}
                style={{
                  maxWidth: '100%',
                  maxHeight: '100%',
                  height: 'auto',
                  objectFit: 'contain',
                  display: 'block',
                  boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
                  borderRadius: '8px',
                  transition: 'transform 0.2s ease'
                }}
                onLoad={() => {
                  // 图片加载完成后的处理
                }}
              />
            )}
          </div>
        </div>
      </div>

      {/* 样式定义 */}
      <style>{`
        @keyframes fadeInOut {
          0%, 100% { opacity: 0.6; }
          50% { opacity: 1; }
        }
        
        .swipeable-page-view {
          -webkit-overflow-scrolling: touch;
        }
        
        .swipeable-page-view img:hover {
          transform: scale(1.02);
        }
      `}</style>
    </div>
  );
};

export default SwipeablePageView;
