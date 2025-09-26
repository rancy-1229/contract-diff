import subprocess
import os
import uuid
from typing import Optional
from app.config import settings

class FormatConverter:
    def __init__(self):
        self.temp_dir = settings.TEMP_DIR
        os.makedirs(self.temp_dir, exist_ok=True)
    
    async def convert_docx_to_pdf(self, docx_path: str) -> Optional[str]:
        """将Word文档转换为PDF - 步骤1"""
        print(f"[DEBUG] 开始转换Word文档: {docx_path}")
        
        try:
            # 生成唯一的PDF文件名
            pdf_filename = f"{uuid.uuid4()}.pdf"
            pdf_path = os.path.join(self.temp_dir, pdf_filename)
            
            # 方法1: 尝试使用LibreOffice
            if await self._convert_with_libreoffice(docx_path, pdf_path):
                print(f"[DEBUG] LibreOffice转换成功: {pdf_path}")
                return pdf_path
            
            # 方法2: 尝试使用docx2pdf
            if await self._convert_with_docx2pdf(docx_path, pdf_path):
                print(f"[DEBUG] docx2pdf转换成功: {pdf_path}")
                return pdf_path
            
            print("[DEBUG] 所有转换方法都失败了")
            return None
                
        except Exception as e:
            print(f"[DEBUG] 转换异常: {e}")
            return None
    
    async def _convert_with_libreoffice(self, docx_path: str, pdf_path: str) -> bool:
        """使用LibreOffice转换"""
        try:
            cmd = [
                '/Applications/LibreOffice.app/Contents/MacOS/soffice',
                '--headless',
                '--convert-to', 'pdf',
                '--outdir', os.path.dirname(pdf_path),
                docx_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # LibreOffice会以原始文件名生成PDF，我们需要找到它并重命名
                original_filename_base = os.path.splitext(os.path.basename(docx_path))[0]
                generated_pdf_path = os.path.join(os.path.dirname(pdf_path), f"{original_filename_base}.pdf")
                
                if os.path.exists(generated_pdf_path):
                    # 重命名为目标文件名
                    os.rename(generated_pdf_path, pdf_path)
                    return True
                else:
                    print(f"[DEBUG] LibreOffice转换失败: 未找到生成的PDF文件 {generated_pdf_path}")
                    return False
            else:
                print(f"[DEBUG] LibreOffice转换失败: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"[DEBUG] LibreOffice转换异常: {e}")
            return False
    
    async def _convert_with_docx2pdf(self, docx_path: str, pdf_path: str) -> bool:
        """使用docx2pdf转换"""
        try:
            from docx2pdf import convert
            convert(docx_path, pdf_path)
            
            if os.path.exists(pdf_path):
                return True
            else:
                print("[DEBUG] docx2pdf转换失败")
                return False
                
        except Exception as e:
            print(f"[DEBUG] docx2pdf转换异常: {e}")
            return False
