# AI 审查差异功能

## 功能概述

第二阶段：AI 审查差异功能，针对第一阶段发现的差异段落进行智能审查，给出专业的风险评估和修改建议。

## 技术架构

### 后端实现

#### 1. AI审查服务
- **模型**: 使用豆包AI模型（字节跳动开发）
- **API**: OpenAI兼容接口
- **配置**: 通过环境变量配置API Key和Base URL

#### 2. 差异编码系统
- **唯一标识**: 为每个差异生成唯一ID
- **编码格式**: `diff_{timestamp}_{hash}`
- **存储**: 在差异数据中保存ID，便于追踪和引用

#### 3. 审查流程
1. 提取差异的完整句子上下文
2. 构建标准条款和目标条款对比
3. 调用AI模型进行审查
4. 解析AI返回的审查结果
5. 存储审查意见到数据库

### 前端展示

#### 1. 审查结果展示
- **风险级别**: 高/中/低（颜色标识）
- **法律合规性**: 是否符合相关法律规定
- **审查意见**: 详细的风险提示和修改建议
- **差异ID**: 唯一标识，便于追踪

#### 2. 交互功能
- **展开/收起**: 审查意见的详细展示
- **筛选**: 按风险级别筛选差异
- **导出**: 导出审查报告

## API设计

### 1. 审查差异接口

```http
POST /api/comparisons/{comparison_id}/review
```

**请求体**:
```json
{
  "diff_ids": ["diff_1", "diff_2", "diff_3"]
}
```

**响应体**:
```json
{
  "review_results": [
    {
      "diff_id": "diff_1",
      "risk_level": "高",
      "legal_compliance": "不符合",
      "review_opinion": "试用期过长，违反劳动合同法规定...",
      "suggestions": "建议将试用期调整为3个月以内..."
    }
  ]
}
```

### 2. 获取审查结果接口

```http
GET /api/comparisons/{comparison_id}/review
```

## 提示词设计

### 系统提示词
```
你是合同审查专家，请分析以下合同条款差异并给出风险评估和修改建议。
```

### 用户提示词模板
```
标准条款：
{standard_text}

目标条款：
{target_text}

请输出：
1. 风险级别（高/中/低）
2. 是否符合法律规定（如劳动合同法/合同法）
3. 审查意见或修改建议
4. 差异ID：{diff_id}
```

## 数据模型

### 1. 差异审查结果表

```sql
CREATE TABLE diff_reviews (
    id SERIAL PRIMARY KEY,
    comparison_id INTEGER REFERENCES comparisons(id),
    diff_id VARCHAR(100) NOT NULL,
    risk_level VARCHAR(10) NOT NULL, -- 高/中/低
    legal_compliance VARCHAR(20) NOT NULL, -- 符合/不符合/部分符合
    review_opinion TEXT NOT NULL,
    suggestions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. 差异数据扩展

```json
{
  "element_id": "diff_1",
  "diff_id": "diff_1703123456_abc123",
  "type": "text",
  "status": "MODIFY",
  "page_index": 0,
  "full_sentence": {
    "sentence": "本合同期限为两年，自2024年1月1日起至2025年12月31日止。",
    "diff_start": 6,
    "diff_end": 8
  },
  "standard_text": "两年",
  "target_text": "三年",
  "review_result": {
    "risk_level": "低",
    "legal_compliance": "符合",
    "review_opinion": "合同期限调整合理，符合法律规定。",
    "suggestions": "建议在合同中明确续签条件。"
  }
}
```

## 实现步骤

### 阶段1: 后端API开发
1. 安装OpenAI客户端库
2. 创建AI审查服务类
3. 实现差异编码系统
4. 开发审查API接口
5. 添加数据库模型

### 阶段2: 前端界面开发
1. 更新差异显示组件
2. 添加审查结果展示
3. 实现风险级别标识
4. 添加审查意见展开功能

### 阶段3: 集成测试
1. 测试AI审查功能
2. 验证差异编码系统
3. 测试前后端集成
4. 优化用户体验

## 配置说明

### 环境变量
```bash
ARK_API_KEY=your_api_key_here
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
ARK_MODEL=ep-20241220123456-abcdef
```

### 依赖安装
```bash
pip install --upgrade "openai>=1.0"
```

## 注意事项

1. **API限制**: 注意AI模型的调用频率限制
2. **错误处理**: 处理AI服务不可用的情况
3. **数据安全**: 确保敏感合同信息的安全传输
4. **性能优化**: 考虑异步处理和缓存机制
5. **成本控制**: 监控AI API的调用成本

## 扩展功能

1. **批量审查**: 支持批量提交多个差异进行审查
2. **审查历史**: 保存审查历史，支持版本对比
3. **自定义提示词**: 支持不同合同类型的定制化提示词
4. **审查报告**: 生成完整的审查报告PDF
5. **智能推荐**: 基于历史数据推荐相似条款的审查意见
