import React, { useRef, useEffect, useState } from 'react';
import { Card, Row, Col, Tag, List, Typography, Button, Space, Divider } from 'antd';

const { Title, Text } = Typography;

interface DiffItem {
  element_id: string;
  type: string;
  status: 'ADD' | 'DELETE' | 'CHANGE' | 'MOVE';
  page_index: number;
  elements: string;
  diff: Array<Array<{
    text: string;
    page_index: number;
    line_index: number;
    doc_index: number;
    char_polygons: number[][];
    polygon: number[];
    sub_info: Array<{
      page_id: number;
      sub_polygons: number[];
      sub_text_index: {
        start_index: number;
        length: number;
      };
    }>;
    sub_type: string;
  }>>;
}

interface DiffViewerProps {
  standardImages: string[];
  targetImages: string[];
  diffList: DiffItem[];
  summary: {
    total_differences: number;
    additions: number;
    deletions: number;
    changes: number;
    moves: number;
  };
}

const DiffViewer: React.FC<DiffViewerProps> = ({ 
  standardImages, 
  targetImages, 
  diffList, 
  summary 
}) => {
  const [selectedDiff, setSelectedDiff] = useState<DiffItem | null>(null);
  const [currentPage, setCurrentPage] = useState(0);

  const statusColors = {
    ADD: '#52c41a',      // 绿色 - 新增
    DELETE: '#ff4d4f',   // 红色 - 删除
    CHANGE: '#faad14',   // 橙色 - 修改
    MOVE: '#1890ff'      // 蓝色 - 移动
  };

  const statusLabels = {
    ADD: '新增',
    DELETE: '删除', 
    CHANGE: '修改',
    MOVE: '移动'
  };

  const handleDiffClick = (diff: DiffItem) => {
    setSelectedDiff(diff);
    setCurrentPage(diff.page_index);
  };

  const renderImageWithOverlays = (imageSrc: string, docIndex: number, pageIndex: number) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const imageRef = useRef<HTMLImageElement>(null);
    
    useEffect(() => {
      if (canvasRef.current && imageRef.current && imageSrc) {
        const canvas = canvasRef.current;
        const img = imageRef.current;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        // 设置Canvas尺寸与图片显示尺寸一致
        canvas.width = img.offsetWidth;
        canvas.height = img.offsetHeight;
        
        // 清除画布
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // 计算坐标缩放比例
        // 后端提供的坐标是基于原始图片像素尺寸（1224x1584）
        // 前端Canvas是基于图片显示尺寸（可能被浏览器缩放）
        const scaleX = img.offsetWidth / img.naturalWidth;
        const scaleY = img.offsetHeight / img.naturalHeight;
        
        console.log(`[DEBUG] 图片缩放比例: scaleX=${scaleX}, scaleY=${scaleY}`);
        console.log(`[DEBUG] 图片显示尺寸: ${img.offsetWidth}x${img.offsetHeight}`);
        console.log(`[DEBUG] 图片原始尺寸: ${img.naturalWidth}x${img.naturalHeight}`);
        
        // 绘制差异标记
        diffList.forEach(diff => {
          if (diff.page_index === pageIndex && diff.diff) {
            const color = statusColors[diff.status];
            
            diff.diff.forEach(charGroup => {
              charGroup.forEach(charInfo => {
                if (charInfo.doc_index === docIndex && charInfo.char_polygons) {
                  charInfo.char_polygons.forEach(polygon => {
                    const [x, y, x2, y2] = polygon;
                    
                    // 将原始图片坐标缩放到Canvas坐标
                    const canvasX = x * scaleX;
                    const canvasY = y * scaleY;
                    const canvasX2 = x2 * scaleX;
                    const canvasY2 = y2 * scaleY;
                    
                    console.log(`[DEBUG] 坐标转换: 原始(${x}, ${y}, ${x2}, ${y2}) -> Canvas(${canvasX}, ${canvasY}, ${canvasX2}, ${canvasY2})`);
                    
                    // 绘制半透明填充
                    ctx.fillStyle = `${color}40`;
                    ctx.fillRect(canvasX, canvasY, canvasX2 - canvasX, canvasY2 - canvasY);
                    
                    // 绘制边框
                    ctx.strokeStyle = color;
                    ctx.lineWidth = 2;
                    ctx.strokeRect(canvasX, canvasY, canvasX2 - canvasX, canvasY2 - canvasY);
                  });
                }
              });
            });
          }
        });
      }
    }, [imageSrc, diffList, pageIndex, docIndex, selectedDiff]);

    return (
      <div style={{ position: 'relative', display: 'inline-block' }}>
        <img 
          ref={imageRef}
          src={imageSrc}
          alt={`文档页面 ${pageIndex + 1}`}
          style={{ 
            maxWidth: '100%', 
            height: 'auto',
            border: '1px solid #d9d9d9',
            borderRadius: '4px',
            display: 'block'
          }}
          onLoad={() => {
            // 图片加载完成后重新绘制差异标记
            if (canvasRef.current && imageRef.current) {
              const canvas = canvasRef.current;
              const img = imageRef.current;
              const ctx = canvas.getContext('2d');
              if (!ctx) return;

              canvas.width = img.offsetWidth;
              canvas.height = img.offsetHeight;
              ctx.clearRect(0, 0, canvas.width, canvas.height);
              
              // 计算坐标缩放比例
              const scaleX = img.offsetWidth / img.naturalWidth;
              const scaleY = img.offsetHeight / img.naturalHeight;
              
              console.log(`[DEBUG] onLoad - 图片缩放比例: scaleX=${scaleX}, scaleY=${scaleY}`);
              
              // 重新绘制差异标记
              diffList.forEach(diff => {
                if (diff.page_index === pageIndex && diff.diff) {
                  const color = statusColors[diff.status];
                  
                  diff.diff.forEach(charGroup => {
                    charGroup.forEach(charInfo => {
                      if (charInfo.doc_index === docIndex && charInfo.char_polygons) {
                        charInfo.char_polygons.forEach(polygon => {
                          const [x, y, x2, y2] = polygon;
                          
                          // 将原始图片坐标缩放到Canvas坐标
                          const canvasX = x * scaleX;
                          const canvasY = y * scaleY;
                          const canvasX2 = x2 * scaleX;
                          const canvasY2 = y2 * scaleY;
                          
                          // 绘制半透明填充
                          ctx.fillStyle = `${color}40`;
                          ctx.fillRect(canvasX, canvasY, canvasX2 - canvasX, canvasY2 - canvasY);
                          
                          // 绘制边框
                          ctx.strokeStyle = color;
                          ctx.lineWidth = 2;
                          ctx.strokeRect(canvasX, canvasY, canvasX2 - canvasX, canvasY2 - canvasY);
                        });
                      }
                    });
                  });
                }
              });
            }
          }}
        />
        <canvas 
          ref={canvasRef}
          style={{ 
            position: 'absolute',
            top: 0,
            left: 0,
            pointerEvents: 'none',
            zIndex: 1
          }}
        />
      </div>
    );
  };

  return (
    <div className="diff-viewer">
      {/* 差异统计 */}
      <Card className="summary-card" style={{ marginBottom: 16 }}>
        <Title level={4}>差异统计</Title>
        <Row gutter={16}>
          <Col span={6}>
            <div className="stat-item">
              <Text strong>总差异数</Text>
              <div className="stat-number">{summary.total_differences}</div>
            </div>
          </Col>
          <Col span={6}>
            <div className="stat-item">
              <Text strong>新增</Text>
              <div className="stat-number" style={{ color: statusColors.ADD }}>
                {summary.additions}
              </div>
            </div>
          </Col>
          <Col span={6}>
            <div className="stat-item">
              <Text strong>删除</Text>
              <div className="stat-number" style={{ color: statusColors.DELETE }}>
                {summary.deletions}
              </div>
            </div>
          </Col>
          <Col span={6}>
            <div className="stat-item">
              <Text strong>修改</Text>
              <div className="stat-number" style={{ color: statusColors.CHANGE }}>
                {summary.changes}
              </div>
            </div>
          </Col>
        </Row>
      </Card>

      <Row gutter={16}>
        {/* 图片对比区域 */}
        <Col span={16}>
          <Card title="文档对比" size="small">
            <Space direction="vertical" style={{ width: '100%' }}>
              {/* 页面切换 */}
              {standardImages.length > 1 && (
                <div style={{ textAlign: 'center' }}>
                  <Space>
                    <Button 
                      disabled={currentPage === 0}
                      onClick={() => setCurrentPage(currentPage - 1)}
                    >
                      上一页
                    </Button>
                    <Text>第 {currentPage + 1} 页 / 共 {standardImages.length} 页</Text>
                    <Button 
                      disabled={currentPage === standardImages.length - 1}
                      onClick={() => setCurrentPage(currentPage + 1)}
                    >
                      下一页
                    </Button>
                  </Space>
                </div>
              )}

              {/* 图片对比 */}
              <Row gutter={16}>
                <Col span={12}>
                  <div style={{ textAlign: 'center' }}>
                    <Title level={5}>标准文档</Title>
                    {standardImages[currentPage] ? (
                      renderImageWithOverlays(standardImages[currentPage], 1, currentPage)
                    ) : (
                      <div style={{ 
                        height: '400px', 
                        border: '1px dashed #d9d9d9',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: '#999'
                      }}>
                        暂无图片
                      </div>
                    )}
                  </div>
                </Col>
                <Col span={12}>
                  <div style={{ textAlign: 'center' }}>
                    <Title level={5}>待审核文档</Title>
                    {targetImages[currentPage] ? (
                      renderImageWithOverlays(targetImages[currentPage], 2, currentPage)
                    ) : (
                      <div style={{ 
                        height: '400px', 
                        border: '1px dashed #d9d9d9',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: '#999'
                      }}>
                        暂无图片
                      </div>
                    )}
                  </div>
                </Col>
              </Row>
            </Space>
          </Card>
        </Col>

        {/* 差异列表 */}
        <Col span={8}>
          <Card title="差异清单" size="small">
            <List
              size="small"
              dataSource={diffList}
              renderItem={(diff, index) => (
                <List.Item
                  className={`diff-item ${selectedDiff?.element_id === diff.element_id ? 'selected' : ''}`}
                  onClick={() => handleDiffClick(diff)}
                  style={{ cursor: 'pointer' }}
                >
                  <div className="diff-item-content">
                    <div className="diff-header">
                      <Tag color={statusColors[diff.status]}>
                        {statusLabels[diff.status]}
                      </Tag>
                      <Text type="secondary">#{index + 1}</Text>
                    </div>
                    <div className="diff-content">
                      <Text code>{diff.elements}</Text>
                    </div>
                    <div className="diff-meta">
                      <Text type="secondary">
                        页面 {diff.page_index + 1}
                      </Text>
                    </div>
                  </div>
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>

      {/* 差异详情 */}
      {selectedDiff && (
        <Card title="差异详情" style={{ marginTop: 16 }}>
          <div className="diff-detail">
            <Row gutter={16}>
              <Col span={12}>
                <Text strong>差异类型：</Text>
                <Tag color={statusColors[selectedDiff.status]}>
                  {statusLabels[selectedDiff.status]}
                </Tag>
              </Col>
              <Col span={12}>
                <Text strong>页面位置：</Text>
                <Text>第 {selectedDiff.page_index + 1} 页</Text>
              </Col>
            </Row>
            <Divider />
            <div>
              <Text strong>差异内容：</Text>
              <div style={{ marginTop: 8 }}>
                <Text code>{selectedDiff.elements}</Text>
              </div>
            </div>
            <Divider />
            <div>
              <Text strong>坐标信息：</Text>
              <div style={{ marginTop: 8, maxHeight: '200px', overflow: 'auto' }}>
                {selectedDiff.diff.map((charGroup, groupIndex) => (
                  <div key={groupIndex} style={{ marginBottom: 8 }}>
                    <Text type="secondary">字符组 {groupIndex + 1}:</Text>
                    {charGroup.map((charInfo, charIndex) => (
                      <div key={charIndex} style={{ marginLeft: 16, fontSize: '12px' }}>
                        <Text>字符: "{charInfo.text}"</Text>
                        <br />
                        <Text type="secondary">
                          坐标: [{charInfo.char_polygons[0]?.join(', ')}]
                        </Text>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};

export default DiffViewer;
