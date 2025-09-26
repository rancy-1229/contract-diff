import React, { useState } from 'react';
import { Upload, message, Card, Typography, Tag, Button } from 'antd';
import { InboxOutlined, FileTextOutlined } from '@ant-design/icons';
import { DocumentType, UploadResponse } from '../types/document';

const { Dragger } = Upload;
const { Text } = Typography;

interface Document {
  id: string;
  filename: string;
  document_type: string;
  status: string;
  file_size: number;
  created_at: string;
  original_filename: string;
}

interface DocumentUploadProps {
  documentType: DocumentType;
  currentDocument: Document | null;
  onUploadSuccess: (document: UploadResponse) => void;
}

const DocumentUpload: React.FC<DocumentUploadProps> = ({ documentType, currentDocument, onUploadSuccess }) => {
  const [uploading, setUploading] = useState(false);

  const handleUpload = async (file: File) => {
    setUploading(true);
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', documentType);

    try {
      const response = await fetch('/api/documents/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '上传失败');
      }

      const result: UploadResponse = await response.json();
      message.success(`${documentType === 'standard' ? '标准' : '待审核'}文档上传成功`);
      onUploadSuccess(result);
      
    } catch (error) {
      message.error(error instanceof Error ? error.message : '上传失败');
    } finally {
      setUploading(false);
    }

    return false; // 阻止默认上传行为
  };

  const beforeUpload = (file: File) => {
    const isValidType = file.type === 'application/pdf' || 
                       file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
    
    if (!isValidType) {
      message.error('只支持 PDF 和 Word 格式文件');
      return false;
    }

    const isLt50M = file.size / 1024 / 1024 < 50;
    if (!isLt50M) {
      message.error('文件大小不能超过 50MB');
      return false;
    }

    return handleUpload(file);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };


  return (
    <Card 
      title={
        <div style={{ textAlign: 'center', fontSize: '18px', fontWeight: 'bold' }}>
          {documentType === 'standard' ? '📄 标准文档' : '📋 待审核文档'}
        </div>
      }
      style={{ 
        height: '100%',
        borderRadius: '12px',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)'
      }}
      styles={{ body: { padding: '24px' } }}
    >
      {currentDocument ? (
        // 显示已上传的文件信息
        <div style={{ textAlign: 'center' }}>
          <div style={{ marginBottom: '20px' }}>
            <FileTextOutlined style={{ fontSize: '64px', color: '#52c41a' }} />
          </div>
          
          <div style={{ marginBottom: '16px' }}>
            <Text strong style={{ fontSize: '18px', color: '#1890ff' }}>
              {currentDocument.original_filename}
            </Text>
          </div>
          
          <div style={{ marginBottom: '12px' }}>
            <Tag color={currentDocument.status === 'processed' ? 'green' : 'orange'} style={{ fontSize: '14px', padding: '4px 12px' }}>
              {currentDocument.status === 'processed' ? '✅ 已处理完成' : '⏳ 处理中...'}
            </Tag>
          </div>
          
          <div style={{ marginBottom: '20px' }}>
            <Text type="secondary" style={{ fontSize: '14px' }}>
              文件大小: {formatFileSize(currentDocument.file_size)}
            </Text>
          </div>
          
          <Button 
            type="default" 
            onClick={() => window.location.reload()}
            style={{ borderRadius: '6px' }}
          >
            重新上传
          </Button>
        </div>
      ) : (
        // 显示上传区域
        <Dragger
          name="file"
          multiple={false}
          accept=".pdf,.docx,.doc"
          beforeUpload={beforeUpload}
          showUploadList={false}
          style={{ 
            background: uploading ? '#f0f0f0' : '#fafafa',
            border: '2px dashed #d9d9d9',
            borderRadius: '8px',
            minHeight: '200px'
          }}
        >
          <p className="ant-upload-drag-icon">
            <InboxOutlined style={{ fontSize: '64px', color: uploading ? '#1890ff' : '#d9d9d9' }} />
          </p>
          <p className="ant-upload-text" style={{ fontSize: '18px', marginBottom: '12px', fontWeight: 'bold' }}>
            {uploading ? '正在上传...' : '点击或拖拽文件到此区域上传'}
          </p>
          <p className="ant-upload-hint" style={{ fontSize: '14px', color: '#999' }}>
            支持 PDF、Word 格式文件，文件大小不超过 50MB
          </p>
        </Dragger>
      )}
    </Card>
  );
};

export default DocumentUpload;
