import React, { useState, useEffect } from 'react';
import { Alert, FloatButton } from 'antd';
import { LeftOutlined, RightOutlined, RobotOutlined, SwapOutlined, MenuOutlined, CloseOutlined } from '@ant-design/icons';
import DiffSidebar from './DiffSidebar';
import SwipeablePageView from './SwipeablePageView';
// import ComparisonDisplayWithPDF from './ComparisonDisplayWithPDF'; // 已删除PDF渲染功能
import { DiffItem, DiffReview, ComparisonResponse } from '../types/document';

interface ComparisonDisplayProps {
  // 支持新的API响应格式
  comparisonData?: ComparisonResponse;
  // 保留向后兼容
  standardImages?: string[];
  targetImages?: string[];
  diffList?: DiffItem[];
  summary?: {
    total_differences: number;
    additions: number;
    deletions: number;
    modifications: number;
    moves: number;
  };
  comparisonId?: string;
  aiReviewEnabled?: boolean;
}

const ComparisonDisplay: React.FC<ComparisonDisplayProps> = ({ 
  comparisonData,
  standardImages, 
  targetImages, 
  diffList,
  summary,
  comparisonId,
  aiReviewEnabled = false
}) => {
  const [currentPage, setCurrentPage] = useState(0);
  const [aiReviews, setAiReviews] = useState<DiffReview[]>([]);
  const [aiReviewLoading, setAiReviewLoading] = useState(false);
  const [aiReviewStatus, setAiReviewStatus] = useState<'idle' | 'processing' | 'completed' | 'error'>('idle');
  const [swipeMode, setSwipeMode] = useState(false);
  const [sidebarVisible, setSidebarVisible] = useState(true);
  const [usePDFViewer] = useState(false); // 禁用PDF渲染，使用图片模式

  // 从comparisonData或props中获取数据
  const finalComparisonData: ComparisonResponse = comparisonData || {
    comparison_id: comparisonId || '',
    standard_images: standardImages || [],
    target_images: targetImages || [],
    diff_list: diffList || [],
    summary: summary || {
      total_differences: 0,
      additions: 0,
      deletions: 0,
      modifications: 0,
      moves: 0
    },
    ai_review_enabled: aiReviewEnabled
  };

  const finalComparisonId = comparisonData?.comparison_id || comparisonId;
  const finalAiReviewEnabled = comparisonData?.ai_review_enabled || aiReviewEnabled;

  const handleDiffClick = (diff: DiffItem) => {
    setCurrentPage(diff.page_index);
  };

  // 获取AI审查结果
  const fetchAiReviews = async () => {
    if (!finalComparisonId || !finalAiReviewEnabled) return;
    
    setAiReviewLoading(true);
    try {
      const response = await fetch(`/api/ai-review/comparisons/${finalComparisonId}/review`);
      if (response.ok) {
        const reviews = await response.json();
        setAiReviews(reviews);
        setAiReviewStatus(reviews.length > 0 ? 'completed' : 'processing');
      } else {
        setAiReviewStatus('error');
      }
    } catch (error) {
      console.error('获取AI审查结果失败:', error);
      setAiReviewStatus('error');
    } finally {
      setAiReviewLoading(false);
    }
  };

  // 手动刷新AI审查结果
  const handleRefreshAiReviews = () => {
    setAiReviewStatus('processing');
    fetchAiReviews();
  };

  // 组件挂载时获取AI审查结果，实现轮询机制
  useEffect(() => {
    if (finalAiReviewEnabled && finalComparisonId) {
      setAiReviewStatus('processing');
      
      // 轮询获取AI审查结果
      const pollAiReviews = async () => {
        let attempts = 0;
        const maxAttempts = 100; // 最多尝试100次
        const pollInterval = 3000; // 每3秒轮询一次
        
        const poll = async () => {
          if (attempts >= maxAttempts) {
            setAiReviewStatus('error');
            return;
          }
          
          attempts++;
          console.log(`第${attempts}次尝试获取AI审查结果...`);
          
          try {
            const response = await fetch(`/api/ai-review/comparisons/${finalComparisonId}/review`);
            if (response.ok) {
              const reviews = await response.json();
              if (reviews.length > 0) {
                setAiReviews(reviews);
                setAiReviewStatus('completed');
                console.log(`AI审查完成，获得${reviews.length}条结果`);
                return;
              }
            }
            
            // 如果还没有结果，继续轮询
            if (attempts < maxAttempts) {
              setTimeout(poll, pollInterval);
            } else {
              setAiReviewStatus('error');
            }
          } catch (error) {
            console.error('轮询AI审查结果失败:', error);
            if (attempts < maxAttempts) {
              setTimeout(poll, pollInterval);
            } else {
              setAiReviewStatus('error');
            }
          }
        };
        
        // 延迟3秒后开始第一次轮询
        setTimeout(poll, 3000);
      };
      
      pollAiReviews();
    }
  }, [finalComparisonId, finalAiReviewEnabled]);

  const handlePageChange = (direction: 'prev' | 'next') => {
    const maxPage = Math.max(
      finalComparisonData.standard_images?.length || 0, 
      finalComparisonData.target_images?.length || 0
    ) - 1;
    if (direction === 'prev' && currentPage > 0) {
      setCurrentPage(currentPage - 1);
    } else if (direction === 'next' && currentPage < maxPage) {
      setCurrentPage(currentPage + 1);
    }
  };

  // 检查是否支持PDF模式
  const supportsPDFMode = finalComparisonData.standard_pdf_url && finalComparisonData.target_pdf_url;
  
  // 添加调试日志
  console.log('[ComparisonDisplay] 调试信息:', {
    comparisonData: finalComparisonData,
    standard_pdf_url: finalComparisonData.standard_pdf_url,
    target_pdf_url: finalComparisonData.target_pdf_url,
    supportsPDFMode,
    usePDFViewer,
    willUsePDF: supportsPDFMode && usePDFViewer
  });

  // PDF模式已禁用，始终使用图片模式
  // if (supportsPDFMode && usePDFViewer) {
  //   console.log('[ComparisonDisplay] 使用PDF模式渲染');
  //   return (
  //     <ComparisonDisplayWithPDF
  //       comparisonData={finalComparisonData}
  //       aiReviews={aiReviews}
  //       aiReviewStatus={aiReviewStatus}
  //       aiReviewLoading={aiReviewLoading}
  //       onRefreshAiReviews={handleRefreshAiReviews}
  //     />
  //   );
  // }

  console.log('[ComparisonDisplay] 使用图片模式渲染');
  
  return (
    <div className="comparison-display" style={{ height: '100vh', display: 'flex', margin: 0, padding: 0 }}>
      {/* 合同展示区域 - 占据全部空间 */}
      <div style={{ 
        flex: 1,
        display: 'flex',
        background: '#f5f5f5',
        overflow: 'hidden',
        margin: 0,
        padding: 0,
        position: 'relative'
      }}>
        {swipeMode ? (
          <SwipeablePageView
            standardImages={finalComparisonData.standard_images || []}
            targetImages={finalComparisonData.target_images || []}
            currentPage={currentPage}
            onPageChange={setCurrentPage}
            className="swipe-mode"
          />
        ) : (
          <div style={{ 
            display: 'flex', 
            height: '100%', 
            width: '100%',
            gap: '2px'
          }}>
            {/* 标准文档区域 */}
            <div style={{ 
              flex: 1,
              display: 'flex', 
              flexDirection: 'column',
              position: 'relative',
              background: '#fff',
              borderRadius: '8px 0 0 8px',
              overflow: 'hidden',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
            }}>
              {/* 文档头部 */}
              <div style={{
                height: '50px',
                background: 'linear-gradient(135deg, #1890ff 0%, #40a9ff 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '0 20px',
                color: 'white',
                fontWeight: 'bold',
                fontSize: '16px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div style={{
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    background: '#fff',
                    boxShadow: '0 0 6px rgba(255,255,255,0.8)'
                  }}></div>
                  标准文档
                </div>
                <div style={{
                  background: 'rgba(255,255,255,0.2)',
                  padding: '4px 12px',
                  borderRadius: '12px',
                  fontSize: '12px',
                  backdropFilter: 'blur(10px)'
                }}>
                  第 {currentPage + 1} 页
                </div>
              </div>
              
              {/* 图片显示区域 */}
              <div style={{ 
                flex: 1,
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                padding: '10px',
                background: '#fafafa',
                overflow: 'auto',
                position: 'relative'
              }}>
                {finalComparisonData.standard_images?.[currentPage] && (
                  <img 
                    src={finalComparisonData.standard_images[currentPage]}
                    alt={`标准文档页面 ${currentPage + 1}`}
                    style={{
                      maxWidth: '100%',
                      maxHeight: '100%',
                      width: 'auto',
                      height: 'auto',
                      objectFit: 'contain',
                      display: 'block',
                      borderRadius: '4px',
                      boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                      transition: 'transform 0.2s ease',
                      minWidth: '300px', // 确保最小宽度
                      minHeight: '200px' // 确保最小高度
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.transform = 'scale(1.02)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.transform = 'scale(1)';
                    }}
                  />
                )}

                {/* AI审查状态 - 标准文档区域内 */}
                {aiReviewEnabled && (
                  <div style={{
                    position: 'absolute',
                    top: '20px',
                    left: '20px',
                    zIndex: 10,
                    maxWidth: '280px'
                  }}>
                    {aiReviewStatus === 'processing' && (
                      <Alert
                        message="AI审查进行中..."
                        description="正在分析合同差异，请稍候"
                        type="info"
                        icon={<RobotOutlined />}
                        showIcon
                        style={{ fontSize: '12px' }}
                      />
                    )}
                    {aiReviewStatus === 'completed' && (
                      <Alert
                        message={`AI审查完成 (${aiReviews.length}条)`}
                        type="success"
                        icon={<RobotOutlined />}
                        showIcon
                        style={{ fontSize: '12px' }}
                      />
                    )}
                    {aiReviewStatus === 'error' && (
                      <Alert
                        message="AI审查失败"
                        description="请检查网络连接或稍后重试"
                        type="error"
                        icon={<RobotOutlined />}
                        showIcon
                        style={{ fontSize: '12px' }}
                      />
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* 分隔线 */}
            <div style={{
              width: '2px',
              background: 'linear-gradient(to bottom, #e8e8e8, #d9d9d9, #e8e8e8)',
              position: 'relative'
            }}>
              <div style={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                background: '#fff',
                border: '2px solid #d9d9d9',
                borderRadius: '50%',
                width: '20px',
                height: '20px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '12px',
                color: '#666',
                fontWeight: 'bold'
              }}>
                VS
              </div>
            </div>

            {/* 目标文档区域 */}
            <div style={{ 
              flex: 1,
              display: 'flex', 
              flexDirection: 'column',
              position: 'relative',
              background: '#fff',
              borderRadius: '0 8px 8px 0',
              overflow: 'hidden',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
            }}>
              {/* 文档头部 */}
              <div style={{
                height: '50px',
                background: 'linear-gradient(135deg, #52c41a 0%, #73d13d 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '0 20px',
                color: 'white',
                fontWeight: 'bold',
                fontSize: '16px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div style={{
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    background: '#fff',
                    boxShadow: '0 0 6px rgba(255,255,255,0.8)'
                  }}></div>
                  目标文档
                </div>
                <div style={{
                  background: 'rgba(255,255,255,0.2)',
                  padding: '4px 12px',
                  borderRadius: '12px',
                  fontSize: '12px',
                  backdropFilter: 'blur(10px)'
                }}>
                  第 {currentPage + 1} 页
                </div>
              </div>
              
              {/* 图片显示区域 */}
              <div style={{ 
                flex: 1,
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                padding: '10px',
                background: '#fafafa',
                overflow: 'auto'
              }}>
                {finalComparisonData.target_images?.[currentPage] && (
                  <img 
                    src={finalComparisonData.target_images[currentPage]}
                    alt={`目标文档页面 ${currentPage + 1}`}
                    style={{
                      maxWidth: '100%',
                      maxHeight: '100%',
                      width: 'auto',
                      height: 'auto',
                      objectFit: 'contain',
                      display: 'block',
                      borderRadius: '4px',
                      boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                      transition: 'transform 0.2s ease',
                      minWidth: '300px', // 确保最小宽度
                      minHeight: '200px' // 确保最小高度
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.transform = 'scale(1.02)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.transform = 'scale(1)';
                    }}
                  />
                )}
              </div>
            </div>
          </div>
        )}

        {/* 浮动按钮组 */}
        <FloatButton.Group
          trigger="hover"
          type="primary"
          style={{ right: 24, top: 24 }}
          icon={<MenuOutlined />}
        >
          <FloatButton
            icon={sidebarVisible ? <CloseOutlined /> : <MenuOutlined />}
            tooltip={sidebarVisible ? "隐藏差异列表" : "显示差异列表"}
            onClick={() => setSidebarVisible(!sidebarVisible)}
          />
          <FloatButton
            icon={<SwapOutlined />}
            tooltip={swipeMode ? "关闭滑动翻页" : "开启滑动翻页"}
            onClick={() => setSwipeMode(!swipeMode)}
          />
          {!swipeMode && (
            <>
              {currentPage > 0 && (
                <FloatButton
                  icon={<LeftOutlined />}
                  tooltip="上一页"
                  onClick={() => handlePageChange('prev')}
                />
              )}
              {currentPage < Math.max(
                finalComparisonData.standard_images?.length || 0, 
                finalComparisonData.target_images?.length || 0
              ) - 1 && (
                <FloatButton
                  icon={<RightOutlined />}
                  tooltip="下一页"
                  onClick={() => handlePageChange('next')}
                />
              )}
            </>
          )}
        </FloatButton.Group>

        {/* 页面信息 - 右上角 */}
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
          第 {currentPage + 1} 页 / 共 {Math.max(
            finalComparisonData.standard_images?.length || 0, 
            finalComparisonData.target_images?.length || 0
          )} 页
        </div>

      </div>

      {/* 右边栏 - 可收缩 */}
      {sidebarVisible && (
        <div style={{ 
          width: '350px',
          height: '100%',
          background: '#fff',
          borderLeft: '2px solid #e8e8e8',
          overflow: 'hidden',
          boxShadow: '-4px 0 12px rgba(0,0,0,0.1)',
          transition: 'all 0.3s ease'
        }}>
          <DiffSidebar 
            diffList={finalComparisonData.diff_list || []}
            onDiffClick={handleDiffClick}
            aiReviews={aiReviews}
            aiReviewStatus={aiReviewStatus}
            aiReviewLoading={aiReviewLoading}
            onRefreshAiReviews={handleRefreshAiReviews}
          />
        </div>
      )}
    </div>
  );
};

export default ComparisonDisplay;