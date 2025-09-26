import React, { useState } from 'react';
import { Button, message, Switch, Space, Typography } from 'antd';
import { PlayCircleOutlined, RobotOutlined } from '@ant-design/icons';
import { Document, ComparisonRequest, ComparisonResponse } from '../types/document';

const { Text } = Typography;

interface ComparisonSectionProps {
  currentStandard: Document | null;
  currentTarget: Document | null;
  onComparisonSuccess?: (result: ComparisonResponse) => void;
}

const ComparisonSection: React.FC<ComparisonSectionProps> = ({ 
  currentStandard, 
  currentTarget,
  onComparisonSuccess
}) => {
  const [comparing, setComparing] = useState(false);
  const [enableAiReview, setEnableAiReview] = useState(true);


  const handleCompare = async () => {
    if (!currentStandard || !currentTarget) {
      message.warning('请先上传标准文档和待审核文档');
      return;
    }

    setComparing(true);
    
    try {
      const request: ComparisonRequest = {
        standard_document_id: currentStandard.id,
        target_document_id: currentTarget.id,
        enable_ai_review: enableAiReview,
      };

      const response = await fetch('/api/comparisons/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '对比失败');
      }

      const result: ComparisonResponse = await response.json();
      message.success('文档对比完成');
      
      // 调用成功回调
      if (onComparisonSuccess) {
        onComparisonSuccess(result);
      }
      
    } catch (error) {
      message.error(error instanceof Error ? error.message : '对比失败');
    } finally {
      setComparing(false);
    }
  };

  const canCompare = currentStandard && currentTarget && !comparing;

  return (
    <div>
      {/* AI审查选项 */}
      <div style={{ 
        marginBottom: '20px', 
        padding: '16px', 
        background: '#f6ffed', 
        border: '1px solid #b7eb8f', 
        borderRadius: '8px' 
      }}>
        <Space align="center">
          <RobotOutlined style={{ color: '#52c41a' }} />
          <Text strong>AI智能审查</Text>
          <Switch 
            checked={enableAiReview}
            onChange={setEnableAiReview}
            checkedChildren="开启"
            unCheckedChildren="关闭"
          />
        </Space>
        <div style={{ marginTop: '8px' }}>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {enableAiReview ? 
              '将自动分析合同差异并提供风险评估和修改建议' : 
              '仅进行基础差异对比，不包含AI审查功能'
            }
          </Text>
        </div>
      </div>

      {/* 对比按钮 */}
      <Button
        type="primary"
        icon={<PlayCircleOutlined />}
        onClick={handleCompare}
        loading={comparing}
        disabled={!canCompare}
        size="large"
        style={{ 
          minWidth: '200px',
          height: '50px',
          fontSize: '16px',
          borderRadius: '8px'
        }}
      >
        {comparing ? '对比中...' : '开始对比'}
      </Button>
      
      {!canCompare && (
        <div style={{ color: '#999', fontSize: '14px', marginTop: '12px' }}>
          {!currentStandard && !currentTarget ? '请先上传标准文档和待审核文档' :
           !currentStandard ? '请先上传标准文档' :
           !currentTarget ? '请先上传待审核文档' : ''}
        </div>
      )}
    </div>
  );
};

export default ComparisonSection;
