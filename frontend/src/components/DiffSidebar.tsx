import React, { useState } from 'react';
import { Tabs, Typography, Tag, Space, Button, Spin, Tooltip } from 'antd';
import { PlusOutlined, MinusOutlined, EditOutlined, RobotOutlined, ReloadOutlined, ExclamationCircleOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import { DiffItem, DiffReview } from '../types/document';

const { Text, Paragraph } = Typography;

// 移除重复的DiffItem接口定义，使用从types导入的

interface DiffSidebarProps {
  diffList: DiffItem[];
  onDiffClick?: (diff: DiffItem) => void;
  summary?: {
    total_differences: number;
    additions: number;
    deletions: number;
    modifications: number;
    moves: number;
  };
  aiReviews?: DiffReview[];
  aiReviewStatus?: 'idle' | 'processing' | 'completed' | 'error';
  aiReviewLoading?: boolean;
  onRefreshAiReviews?: () => void;
}

const DiffSidebar: React.FC<DiffSidebarProps> = ({ 
  diffList, 
  onDiffClick,
  aiReviews = [],
  aiReviewStatus = 'idle',
  aiReviewLoading = false,
  onRefreshAiReviews
}) => {
  const [activeTab, setActiveTab] = useState('all');

  // 按类型分类差异
  const categorizedDiffs = {
    all: diffList,
    add: diffList.filter(diff => diff.status === 'ADD'),
    delete: diffList.filter(diff => diff.status === 'DELETE'),
    modify: diffList.filter(diff => diff.status === 'MODIFY'),
    move: diffList.filter(diff => diff.status === 'MOVE')
  };

  // 渲染句子中的差异高亮
  const renderHighlightedSentence = (diff: DiffItem) => {
    if (!diff.full_sentence) {
      return <Text>{diff.elements}</Text>;
    }

    const { sentence } = diff.full_sentence;
    const diff_start = diff.diff_start || 0;
    const diff_end = diff_start + (diff.diff_length || 0);
    const beforeDiff = sentence.substring(0, diff_start);
    const diffText = sentence.substring(diff_start, diff_end);
    const afterDiff = sentence.substring(diff_end);

    // 对于修改类型，显示原文本 -> 新文本
    if (diff.status === 'MODIFY' && diff.old_text && diff.new_text) {
      return (
        <Text>
          {beforeDiff}
          <Text
            mark
            style={{
              backgroundColor: '#ff4d4f',
              color: '#fff',
              padding: '2px 4px',
              borderRadius: '3px',
              fontWeight: 'bold',
              textDecoration: 'line-through'
            }}
          >
            {diff.old_text}
          </Text>
          <Text
            mark
            style={{
              backgroundColor: '#52c41a',
              color: '#fff',
              padding: '2px 4px',
              borderRadius: '3px',
              fontWeight: 'bold',
              marginLeft: '4px'
            }}
          >
            {diff.new_text}
          </Text>
          {afterDiff}
        </Text>
      );
    }

    return (
      <Text>
        {beforeDiff}
        <Text
          mark
          style={{
            backgroundColor: getStatusColor(diff.status),
            color: '#fff',
            padding: '2px 4px',
            borderRadius: '3px',
            fontWeight: 'bold'
          }}
        >
          {diffText}
        </Text>
        {afterDiff}
      </Text>
    );
  };

  // 获取状态颜色
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ADD':
        return '#52c41a';
      case 'DELETE':
        return '#ff4d4f';
      case 'MODIFY':
        return '#faad14';  // 橙色表示修改
      case 'MOVE':
        return '#1890ff';
      default:
        return '#d9d9d9';
    }
  };

  // 获取状态图标
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'ADD':
        return <PlusOutlined style={{ color: '#52c41a' }} />;
      case 'DELETE':
        return <MinusOutlined style={{ color: '#ff4d4f' }} />;
      case 'MODIFY':
        return <EditOutlined style={{ color: '#faad14' }} />;
      case 'MOVE':
        return <EditOutlined style={{ color: '#1890ff' }} />;
      default:
        return null;
    }
  };

  // 获取状态文本
  const getStatusText = (status: string) => {
    switch (status) {
      case 'ADD':
        return '新增';
      case 'DELETE':
        return '删除';
      case 'MODIFY':
        return '修改';
      case 'MOVE':
        return '移动';
      default:
        return status;
    }
  };

  // 获取AI审查结果
  const getAiReview = (diffId: string) => {
    return aiReviews.find(review => review.diff_id === diffId);
  };

  // 获取风险级别颜色
  const getRiskLevelColor = (riskLevel: string) => {
    switch (riskLevel) {
      case '高': return 'red';
      case '中': return 'orange';
      case '低': return 'green';
      default: return 'default';
    }
  };

  // 获取合规性图标
  const getComplianceIcon = (compliance: string) => {
    if (compliance.includes('符合')) return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
    if (compliance.includes('不符合')) return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
    return <ExclamationCircleOutlined style={{ color: '#faad14' }} />;
  };

  // 渲染差异列表
  const renderDiffList = (diffs: DiffItem[]) => {
    if (diffs.length === 0) {
      return (
        <div style={{ textAlign: 'center', padding: '20px', color: '#999' }}>
          暂无差异
        </div>
      );
    }

    return (
      <div>
        {diffs.map((diff) => (
          <div
            key={diff.element_id}
            style={{
              marginBottom: '8px',
              padding: '12px',
              cursor: 'pointer',
              border: '1px solid #f0f0f0',
              borderRadius: '6px',
              background: '#fff',
              transition: 'all 0.2s ease'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = '#1890ff';
              e.currentTarget.style.boxShadow = '0 2px 8px rgba(24, 144, 255, 0.2)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = '#f0f0f0';
              e.currentTarget.style.boxShadow = 'none';
            }}
            onClick={() => onDiffClick?.(diff)}
          >
            <div style={{ marginBottom: '8px' }}>
              <Space size="small">
                {getStatusIcon(diff.status)}
                <Tag color={getStatusColor(diff.status)} style={{ fontSize: '11px', padding: '2px 6px' }}>
                  {getStatusText(diff.status)}
                </Tag>
                <Text type="secondary" style={{ fontSize: '11px' }}>
                  第 {diff.page_index + 1} 页
                </Text>
              </Space>
            </div>
            
            <div style={{ fontSize: '13px', lineHeight: '1.4' }}>
              {renderHighlightedSentence(diff)}
            </div>
            
            {/* AI审查结果 */}
            {diff.element_id && (() => {
              const aiReview = getAiReview(diff.element_id);
              if (aiReview) {
                return (
                  <div style={{ 
                    marginTop: '8px', 
                    padding: '8px', 
                    background: '#f6ffed', 
                    border: '1px solid #b7eb8f', 
                    borderRadius: '4px' 
                  }}>
                    <div style={{ marginBottom: '4px' }}>
                      <Space size="small">
                        <RobotOutlined style={{ color: '#52c41a' }} />
                        <Tag color={getRiskLevelColor(aiReview.risk_level)}>
                          {aiReview.risk_level}风险
                        </Tag>
                        <Tooltip title={aiReview.compliance}>
                          {getComplianceIcon(aiReview.compliance)}
                        </Tooltip>
                      </Space>
                    </div>
                    <Paragraph 
                      style={{ 
                        fontSize: '12px', 
                        margin: 0, 
                        color: '#595959',
                        lineHeight: '1.3'
                      }}
                      ellipsis={{ rows: 2, expandable: true }}
                    >
                      {aiReview.review_suggestions}
                    </Paragraph>
                  </div>
                );
              }
              return null;
            })()}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* 差异列表 */}
      <div style={{ flex: 1, overflow: 'hidden' }}>
        {/* AI审查状态栏 */}
        {aiReviewStatus !== 'idle' && (
          <div style={{ 
            padding: '8px 16px', 
            borderBottom: '1px solid #f0f0f0',
            background: aiReviewStatus === 'completed' ? '#f6ffed' : 
                        aiReviewStatus === 'error' ? '#fff2f0' : '#e6f7ff'
          }}>
            <Space size="small">
              {aiReviewStatus === 'processing' && <Spin size="small" />}
              {aiReviewStatus === 'completed' && <CheckCircleOutlined style={{ color: '#52c41a' }} />}
              {aiReviewStatus === 'error' && <CloseCircleOutlined style={{ color: '#ff4d4f' }} />}
              <Text style={{ fontSize: '12px' }}>
                {aiReviewStatus === 'processing' && 'AI审查进行中...'}
                {aiReviewStatus === 'completed' && `AI审查完成 (${aiReviews.length}条)`}
                {aiReviewStatus === 'error' && 'AI审查失败'}
              </Text>
              {aiReviewStatus === 'error' && onRefreshAiReviews && (
                <Button 
                  type="link" 
                  size="small" 
                  icon={<ReloadOutlined />}
                  onClick={onRefreshAiReviews}
                  style={{ padding: 0, height: 'auto' }}
                >
                  重试
                </Button>
              )}
            </Space>
          </div>
        )}

        <Tabs 
          activeKey={activeTab} 
          onChange={setActiveTab}
          size="small"
          style={{ height: '100%' }}
          tabBarStyle={{ margin: '0 16px', marginTop: '16px' }}
          items={[
            {
              key: 'all',
              label: `全部`,
              children: (
                <div style={{ height: 'calc(100vh - 120px)', overflow: 'auto', padding: '0 16px' }}>
                  {renderDiffList(categorizedDiffs.all)}
                </div>
              )
            },
            {
              key: 'add',
              label: `新增`,
              children: (
                <div style={{ height: 'calc(100vh - 120px)', overflow: 'auto', padding: '0 16px' }}>
                  {renderDiffList(categorizedDiffs.add)}
                </div>
              )
            },
            {
              key: 'delete',
              label: `删除`,
              children: (
                <div style={{ height: 'calc(100vh - 120px)', overflow: 'auto', padding: '0 16px' }}>
                  {renderDiffList(categorizedDiffs.delete)}
                </div>
              )
            },
            {
              key: 'modify',
              label: `修改`,
              children: (
                <div style={{ height: 'calc(100vh - 120px)', overflow: 'auto', padding: '0 16px' }}>
                  {renderDiffList(categorizedDiffs.modify)}
                </div>
              )
            }
          ]}
        />
      </div>
    </div>
  );
};

export default DiffSidebar;
