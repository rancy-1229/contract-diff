import { useState } from 'react';
import { Layout, Typography, Row, Col, message, Button } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import DocumentUpload from './components/DocumentUpload';
import ComparisonSection from './components/ComparisonSection';
import ComparisonDisplay from './components/ComparisonDisplay';

const { Header, Content } = Layout;
const { Title, Text } = Typography;

interface Document {
  id: string;
  filename: string;
  document_type: string;
  status: string;
  file_size: number;
  created_at: string;
  original_filename: string;
  file_path: string;
  file_type: string;
}

function App() {
  const [currentStandard, setCurrentStandard] = useState<Document | null>(null);
  const [currentTarget, setCurrentTarget] = useState<Document | null>(null);
  const [showComparisonDisplay, setShowComparisonDisplay] = useState(false);
  const [comparisonResult, setComparisonResult] = useState<any>(null);

  const handleUploadSuccess = async (documentType: string, uploadResponse: any) => {
    message.success(`${documentType === 'standard' ? '标准' : '待审核'}文档上传成功`);
    
    // 获取完整的文档信息
    try {
      const response = await fetch('/api/documents/');
      const data = await response.json();
      const fullDocument = data.documents.find((doc: Document) => doc.id === uploadResponse.document_id);
      
      if (fullDocument) {
        if (documentType === 'standard') {
          setCurrentStandard(fullDocument);
        } else {
          setCurrentTarget(fullDocument);
        }
      }
    } catch (error) {
      console.error('获取文档信息失败:', error);
    }
  };

  const handleComparisonSuccess = (result: any) => {
    console.log('[App] 对比结果接收:', result);
    console.log('[App] PDF URLs:', {
      standard_pdf_url: result.standard_pdf_url,
      target_pdf_url: result.target_pdf_url
    });
    setComparisonResult(result);
    setShowComparisonDisplay(true);
  };

  const handleBackToMain = () => {
    setShowComparisonDisplay(false);
    setComparisonResult(null);
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#fff', padding: '0 24px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Title level={3} style={{ margin: '16px 0', color: '#1890ff' }}>
            合同差异对比
          </Title>
          <div style={{ display: 'flex', gap: '8px' }}>
            {showComparisonDisplay && (
              <Button 
                icon={<ArrowLeftOutlined />} 
                onClick={handleBackToMain}
                type="primary"
              >
                返回主页面
              </Button>
            )}
          </div>
        </div>
      </Header>
      
      <Content style={{ padding: '24px', background: '#f5f5f5' }}>
        {showComparisonDisplay && comparisonResult ? (
          <ComparisonDisplay
            comparisonData={comparisonResult}
            standardImages={comparisonResult.standard_images}
            targetImages={comparisonResult.target_images}
            diffList={comparisonResult.diff_list}
            summary={comparisonResult.summary}
            comparisonId={comparisonResult.comparison_id}
            aiReviewEnabled={comparisonResult.ai_review_enabled}
          />
        ) : (
          <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
            {/* 主标题 */}
            <div style={{ textAlign: 'center', marginBottom: '40px' }}>
              <Title level={2} style={{ color: '#1890ff', marginBottom: '8px' }}>
                合同差异对比
              </Title>
              <Text type="secondary" style={{ fontSize: '16px' }}>
                上传标准文档和待审核文档，快速识别差异
              </Text>
            </div>

            {/* 文档上传区域 */}
            <Row gutter={[32, 32]} style={{ marginBottom: '40px' }}>
              <Col xs={24} md={12}>
                <DocumentUpload
                  documentType="standard"
                  currentDocument={currentStandard}
                  onUploadSuccess={(doc) => handleUploadSuccess('standard', doc)}
                />
              </Col>
              <Col xs={24} md={12}>
                <DocumentUpload
                  documentType="target"
                  currentDocument={currentTarget}
                  onUploadSuccess={(doc) => handleUploadSuccess('target', doc)}
                />
              </Col>
            </Row>

            {/* 开始对比按钮 */}
            <div style={{ textAlign: 'center' }}>
              <ComparisonSection
                currentStandard={currentStandard}
                currentTarget={currentTarget}
                onComparisonSuccess={handleComparisonSuccess}
              />
            </div>
          </div>
        )}
      </Content>
    </Layout>
  );
}

export default App;
