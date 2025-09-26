# 合同差异对比系统

一个基于Web的智能合同差异对比系统，支持文档上传、差异识别、AI审查和可视化展示。

## 功能特性

- 📄 **文档上传**: 支持Word文档(.docx)和PDF文档上传
- 🔍 **智能对比**: 自动识别文档间的差异，包括文本增删、修改等
- 🤖 **AI审查**: 集成AI智能审查，提供差异分析和建议
- 🎨 **可视化展示**: 直观的并排对比界面，支持差异高亮显示
- 📱 **响应式设计**: 适配不同设备和屏幕尺寸
- ⚡ **实时处理**: 快速文档处理和差异识别

## 技术架构

### 后端技术栈
- **Python 3.12**: 主要开发语言
- **FastAPI**: 高性能Web框架
- **SQLAlchemy**: ORM数据库操作
- **PyMuPDF**: PDF文档处理
- **python-docx**: Word文档处理
- **OpenAI API**: AI智能审查
- **Pillow**: 图像处理

### 前端技术栈
- **React 18**: 用户界面框架
- **TypeScript**: 类型安全的JavaScript
- **Ant Design**: UI组件库
- **Vite**: 构建工具
- **Axios**: HTTP客户端

## 项目结构

```
contract-diff/
├── backend/                 # 后端服务
│   ├── app/                # 应用核心代码
│   │   ├── api/           # API路由
│   │   ├── models/        # 数据模型
│   │   ├── schemas/       # 数据模式
│   │   ├── services/      # 业务逻辑
│   │   └── utils/         # 工具函数
│   ├── requirements.txt   # Python依赖
│   ├── run.py            # 启动脚本
│   └── uploads/          # 文件上传目录
├── frontend/              # 前端应用
│   ├── src/              # 源代码
│   │   ├── components/   # React组件
│   │   ├── services/     # API服务
│   │   ├── types/        # TypeScript类型
│   │   └── utils/        # 工具函数
│   ├── package.json      # 前端依赖
│   └── vite.config.ts    # Vite配置
├── docs/                 # 项目文档
├── start.sh             # 启动脚本
└── README.md            # 项目说明
```

## 快速开始

### 环境要求

- Python 3.12+
- Node.js 18+
- npm 或 yarn

### 安装步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd contract-diff
   ```

2. **后端设置**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **前端设置**
   ```bash
   cd frontend
   npm install
   ```

4. **启动服务**
   ```bash
   # 启动后端服务
   cd backend
   python run.py
   
   # 启动前端服务（新终端）
   cd frontend
   npm run dev
   ```

5. **访问应用**
   - 前端: http://localhost:5173
   - 后端API: http://localhost:8000

## 使用说明

### 基本流程

1. **上传文档**
   - 上传标准文档（参考版本）
   - 上传目标文档（待对比版本）

2. **开始对比**
   - 点击"开始对比"按钮
   - 系统自动处理文档并识别差异

3. **查看结果**
   - 并排显示两个文档
   - 差异区域高亮显示
   - 右侧显示差异列表

4. **AI审查**（可选）
   - 系统自动进行AI智能审查
   - 提供差异分析和建议

### 功能说明

- **文档支持**: 支持.docx和.pdf格式
- **差异类型**: 文本增加、删除、修改
- **页面导航**: 支持翻页查看多页文档
- **响应式**: 适配桌面和移动设备

## API文档

### 主要接口

- `POST /api/documents/upload` - 文档上传
- `POST /api/comparisons/` - 创建对比任务
- `GET /api/comparisons/{id}` - 获取对比结果
- `GET /api/ai-review/comparisons/{id}/review` - 获取AI审查结果

详细API文档请访问: http://localhost:8000/docs

## 配置说明

### 环境变量

1. **创建配置文件**
   ```bash
   # 复制配置文件模板
   cp backend/app/config.example.py backend/app/config.py
   ```

2. **配置环境变量**
   创建 `.env` 文件并配置以下变量：
   ```env
   # 数据库配置
   DATABASE_URL=postgresql://username:password@localhost:5432/contract_diff
   
   # AI模型配置
   ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3/
   ARK_API_KEY=your_api_key_here
   ARK_MODEL=doubao-seed-1-6-flash-250828
   
   # 文件上传配置
   UPLOAD_DIR=./uploads
   MAX_FILE_SIZE=50MB
   ```

3. **修改config.py**
   根据你的环境修改 `backend/app/config.py` 中的配置项。

### 开发配置

- 后端开发模式: `python run.py --reload`
- 前端开发模式: `npm run dev`
- 生产构建: `npm run build`

## 部署说明

### Docker部署

```bash
# 构建镜像
docker build -t contract-diff .

# 运行容器
docker run -p 8000:8000 -p 5173:5173 contract-diff
```

### 生产部署

1. 构建前端
   ```bash
   cd frontend
   npm run build
   ```

2. 配置生产环境变量

3. 启动后端服务
   ```bash
   cd backend
   python run.py
   ```

## 开发指南

### 代码规范

- 后端: 遵循PEP 8 Python代码规范
- 前端: 使用TypeScript，遵循ESLint规则
- 提交信息: 使用约定式提交格式

### 测试

```bash
# 后端测试
cd backend
python -m pytest

# 前端测试
cd frontend
npm test
```

## 常见问题

### Q: 文档上传失败？
A: 检查文件格式是否支持(.docx, .pdf)，文件大小是否超限。

### Q: 对比结果不准确？
A: 确保文档格式正确，文本清晰可读。

### Q: AI审查功能不工作？
A: 检查OpenAI API密钥配置是否正确。

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

- 项目维护者: [Your Name]
- 邮箱: [your.email@example.com]
- 项目地址: [GitHub Repository URL]

## 更新日志

### v1.0.0 (2024-01-01)
- 初始版本发布
- 基础文档对比功能
- AI智能审查集成
- 响应式用户界面

---

**注意**: 这是一个开发版本，请在生产环境中谨慎使用。# contract-diff
