import fitz
import os
from typing import Dict, List
from app.config import settings
from PIL import Image, ImageDraw

class ImageProcessor:
    def __init__(self):
        self.image_dir = settings.IMAGES_DIR
        os.makedirs(self.image_dir, exist_ok=True)
    
    async def generate_comparison_images(self, standard_path: str, target_path: str, comparison_id: str, diff_list: List[Dict] = None) -> Dict:
        """生成对比图片 - 使用PyMuPDF直接绘制高亮"""
        print(f"[DEBUG] 生成对比图片: 标准文档={standard_path}, 目标文档={target_path}")

        # 使用PyMuPDF直接生成带高亮的图片
        standard_images = await self._pdf_to_images_with_highlights(standard_path, f"{comparison_id}_standard", diff_list, 1)
        target_images = await self._pdf_to_images_with_highlights(target_path, f"{comparison_id}_target", diff_list, 2)

        return {
            "standard_images": standard_images,
            "target_images": target_images
        }
    
    async def _pdf_to_images_with_highlights(self, pdf_path: str, image_prefix: str, diff_list: List[Dict], doc_index: int) -> List[str]:
        """使用PyMuPDF直接在PDF上绘制高亮，然后导出PNG"""
        print(f"[DEBUG] 使用PyMuPDF绘制高亮: {pdf_path}, 文档索引: {doc_index}")
        
        try:
            # 打开PDF文档
            doc = fitz.open(pdf_path)
            image_paths = []
            
            # 差异颜色配置
            colors = {
                "ADD": (0.32, 0.77, 0.10, 0.3),      # 绿色 - 新增 (RGBA)
                "DELETE": (1.0, 0.30, 0.31, 0.3),     # 红色 - 删除 (RGBA)
                "MODIFY": (0.98, 0.68, 0.08, 0.3),    # 橙色 - 修改 (RGBA)
                "MOVE": (0.09, 0.56, 1.0, 0.3)        # 蓝色 - 移动 (RGBA)
            }
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                print(f"[DEBUG] 处理页面 {page_num}")
                
                # 在PDF页面上绘制高亮
                if diff_list:
                    page_diffs = [diff for diff in diff_list if diff.get('page_index') == page_num]
                    print(f"[DEBUG] 页面 {page_num} 有 {len(page_diffs)} 个差异")
                    
                    for diff in page_diffs:
                        status = diff.get('status', '')
                        color = colors.get(status, (0.5, 0.5, 0.5, 0.3))  # 默认灰色
                        
                        # 遍历差异中的字符组
                        for char_group in diff.get('diff', []):
                            for char_info in char_group:
                                if char_info.get('doc_index') == doc_index:
                                    # 获取字符坐标
                                    char_polygons = char_info.get('char_polygons', [])
                                    for polygon in char_polygons:
                                        if len(polygon) >= 4:
                                            x0, y0, x1, y1 = polygon[:4]
                                            
                                            # 在PDF页面上绘制高亮矩形
                                            rect = fitz.Rect(x0, y0, x1, y1)
                                            highlight = page.add_highlight_annot(rect)
                                            # 高亮注释只支持描边颜色，不支持填充颜色
                                            highlight.set_colors(stroke=color[:3])
                                            highlight.set_opacity(color[3])
                                            
                                            print(f"[DEBUG] 绘制高亮: {status} 坐标({x0}, {y0}, {x1}, {y1})")
                
                # 将页面转换为PNG图片
                mat = fitz.Matrix(2.0, 2.0)  # 2倍缩放
                pix = page.get_pixmap(matrix=mat)
                
                # 保存图片
                image_filename = f"{image_prefix}_page_{page_num}.png"
                image_path = os.path.join(self.image_dir, image_filename)
                pix.save(image_path)
                
                # 返回相对路径
                relative_path = f"/images/{image_filename}"
                image_paths.append(relative_path)
                print(f"[DEBUG] 保存图片: {relative_path}")
            
            doc.close()
            return image_paths
            
        except Exception as e:
            print(f"[DEBUG] PyMuPDF高亮绘制失败: {e}")
            # 如果失败，回退到普通图片生成
            return await self.document_to_images(pdf_path, image_prefix)

    def _convert_pdf_coords_to_image_coords(self, pdf_coords: List[float], page_height: float, scale_factor: float = 2.0) -> List[float]:
        """将PDF坐标转换为图片坐标
        
        Args:
            pdf_coords: PDF坐标 [x0, y0, x1, y1]
            page_height: PDF页面高度（点）
            scale_factor: 缩放因子（默认2.0）
        
        Returns:
            转换后的图片坐标 [x0, y0, x1, y1]
        """
        if len(pdf_coords) < 4:
            return pdf_coords
            
        x0, y0, x1, y1 = pdf_coords[:4]
        
        # 1. 应用缩放因子
        x0_scaled = x0 * scale_factor
        y0_scaled = y0 * scale_factor
        x1_scaled = x1 * scale_factor
        y1_scaled = y1 * scale_factor
        
        # 2. 翻转Y轴（PDF原点在左下角，图片原点在左上角）
        image_height = page_height * scale_factor
        y0_flipped = image_height - y1_scaled
        y1_flipped = image_height - y0_scaled
        
        return [x0_scaled, y0_flipped, x1_scaled, y1_flipped]

    async def _draw_diff_overlays(self, image_paths: List[str], diff_list: List[Dict], doc_index: int) -> List[str]:
        """在图片上绘制差异标记"""
        print(f"[DEBUG] 开始绘制差异标记，文档索引: {doc_index}")
        
        # 差异颜色配置
        colors = {
            "ADD": (82, 196, 26, 100),      # 绿色 - 新增 (RGBA)
            "DELETE": (255, 77, 79, 100),   # 红色 - 删除 (RGBA)
            "CHANGE": (250, 173, 20, 100),  # 橙色 - 修改 (RGBA)
            "MOVE": (24, 144, 255, 100)     # 蓝色 - 移动 (RGBA)
        }
        
        processed_images = []
        
        for image_path in image_paths:
            try:
                # 获取页面索引
                page_index = self._extract_page_index_from_path(image_path)
                
                # 打开图片
                img = Image.open(image_path.replace('/images/', self.image_dir + '/'))
                
                # 创建绘图对象
                draw = ImageDraw.Draw(img, 'RGBA')
                
                # 获取图片尺寸（用于坐标转换）
                img_width, img_height = img.size
                # 计算原始PDF页面高度（图片是2倍缩放）
                pdf_page_height = img_height / 2.0
                
                # 绘制该页面的差异标记
                page_diffs = [diff for diff in diff_list if diff.get('page_index') == page_index]
                print(f"[DEBUG] 页面 {page_index} 有 {len(page_diffs)} 个差异")
                
                for diff in page_diffs:
                    status = diff.get('status', '')
                    color = colors.get(status, (128, 128, 128, 100))  # 默认灰色
                    
                    # 遍历差异中的字符组
                    for char_group in diff.get('diff', []):
                        for char_info in char_group:
                            if char_info.get('doc_index') == doc_index:
                                # 获取字符坐标
                                char_polygons = char_info.get('char_polygons', [])
                                for polygon in char_polygons:
                                    if len(polygon) >= 4:
                                        # 转换PDF坐标到图片坐标
                                        converted_coords = self._convert_pdf_coords_to_image_coords(
                                            polygon, pdf_page_height, 2.0
                                        )
                                        x0, y0, x1, y1 = converted_coords
                                        
                                        # 绘制半透明矩形
                                        draw.rectangle([x0, y0, x1, y1], fill=color, outline=color[:3], width=2)
                                        print(f"[DEBUG] 绘制差异标记: {status} PDF坐标{polygon[:4]} -> 图片坐标({x0}, {y0}, {x1}, {y1})")
                
                # 保存处理后的图片
                processed_path = image_path.replace('.png', '_with_diff.png')
                full_processed_path = processed_path.replace('/images/', self.image_dir + '/')
                img.save(full_processed_path)
                
                processed_images.append(processed_path)
                print(f"[DEBUG] 保存带差异标记的图片: {processed_path}")
                
            except Exception as e:
                print(f"[DEBUG] 绘制差异标记失败: {e}")
                processed_images.append(image_path)  # 使用原图片
        
        return processed_images

    def _extract_page_index_from_path(self, image_path: str) -> int:
        """从图片路径中提取页面索引"""
        try:
            # 路径格式: /images/comp_xxx_xxx_standard_page_0.png
            filename = os.path.basename(image_path)
            if '_page_' in filename:
                page_part = filename.split('_page_')[1].split('.')[0]
                return int(page_part)
            return 0
        except:
            return 0
    
    async def document_to_images(self, doc_path: str, image_prefix: str) -> List[str]:
        """将文档转换为图片"""
        print(f"[DEBUG] 开始转换文档为图片: {doc_path}")
        
        # 检查文件类型
        if doc_path.lower().endswith('.pdf'):
            return await self.pdf_to_images(doc_path, image_prefix)
        elif doc_path.lower().endswith(('.docx', '.doc')):
            return await self.word_to_images(doc_path, image_prefix)
        else:
            print(f"[DEBUG] 不支持的文档类型: {doc_path}")
            return await self.create_placeholder_images(image_prefix)
    
    async def pdf_to_images(self, pdf_path: str, image_prefix: str) -> List[str]:
        """将PDF转换为图片"""
        try:
            print(f"[DEBUG] 转换PDF为图片: {pdf_path}")
            doc = fitz.open(pdf_path)
            image_paths = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # 设置缩放比例以提高图片质量
                mat = fitz.Matrix(2.0, 2.0)  # 2倍缩放
                pix = page.get_pixmap(matrix=mat)
                
                # 生成图片文件名
                image_filename = f"{image_prefix}_page_{page_num}.png"
                image_path = os.path.join(self.image_dir, image_filename)
                
                # 保存图片
                pix.save(image_path)
                image_paths.append(f"/images/{image_filename}")
                print(f"[DEBUG] 保存PDF页面图片: {image_path}")
            
            doc.close()
            return image_paths
        except Exception as e:
            print(f"PDF转图片失败: {e}")
            return await self.create_placeholder_images(image_prefix)
    
    async def word_to_images(self, word_path: str, image_prefix: str) -> List[str]:
        """将Word文档转换为图片 - 先转PDF再转图片"""
        try:
            print(f"[DEBUG] 转换Word文档为图片: {word_path}")
            
            # 方案1: 尝试Word → PDF → 图片
            pdf_path = await self._convert_word_to_pdf(word_path)
            if pdf_path and os.path.exists(pdf_path):
                print(f"[DEBUG] Word转PDF成功，开始转图片: {pdf_path}")
                images = await self.pdf_to_images(pdf_path, image_prefix)
                # 清理临时PDF文件
                try:
                    os.remove(pdf_path)
                except:
                    pass
                return images
            
            # 方案2: 如果PDF转换失败，使用文本渲染
            print(f"[DEBUG] Word转PDF失败，使用文本渲染方式")
            return await self._word_to_images_text_render(word_path, image_prefix)
            
        except Exception as e:
            print(f"Word转图片失败: {e}")
            return await self.create_placeholder_images(image_prefix)
    
    async def _convert_word_to_pdf(self, word_path: str) -> str:
        """将Word文档转换为PDF"""
        try:
            import subprocess
            import uuid
            
            # 生成临时PDF路径
            pdf_filename = f"{uuid.uuid4()}.pdf"
            pdf_path = os.path.join(self.image_dir, pdf_filename)
            
            # 尝试使用LibreOffice
            try:
                result = subprocess.run([
                    '/Applications/LibreOffice.app/Contents/MacOS/soffice', '--headless', '--convert-to', 'pdf',
                    '--outdir', self.image_dir, word_path
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    # LibreOffice会以原始文件名生成PDF
                    original_name = os.path.splitext(os.path.basename(word_path))[0]
                    generated_pdf = os.path.join(self.image_dir, f"{original_name}.pdf")
                    if os.path.exists(generated_pdf):
                        os.rename(generated_pdf, pdf_path)
                        return pdf_path
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
            
            # 尝试使用docx2pdf
            try:
                from docx2pdf import convert
                convert(word_path, pdf_path)
                if os.path.exists(pdf_path):
                    return pdf_path
            except Exception as e:
                print(f"[DEBUG] docx2pdf转换失败: {e}")
            
            return None
            
        except Exception as e:
            print(f"[DEBUG] Word转PDF异常: {e}")
            return None
    
    async def _word_to_images_text_render(self, word_path: str, image_prefix: str) -> List[str]:
        """使用文本渲染方式将Word转换为图片（备用方案）"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            from docx import Document
            
            # 读取Word文档内容
            doc = Document(word_path)
            
            # 提取文本内容
            full_text = ""
            for paragraph in doc.paragraphs:
                full_text += paragraph.text + "\n"
            
            # 创建图片
            img = Image.new('RGB', (800, 1000), color='white')
            draw = ImageDraw.Draw(img)
            
            # 设置字体
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
            except:
                font = ImageFont.load_default()
            
            # 绘制文本
            lines = full_text.split('\n')
            y = 50
            for line in lines[:50]:  # 限制行数
                if y > 950:  # 限制高度
                    break
                draw.text((50, y), line, fill='black', font=font)
                y += 20
            
            # 保存图片
            image_filename = f"{image_prefix}_page_0.png"
            image_path = os.path.join(self.image_dir, image_filename)
            img.save(image_path)
            print(f"[DEBUG] 保存Word文档图片（文本渲染）: {image_path}")
            
            return [f"/images/{image_filename}"]
            
        except Exception as e:
            print(f"Word文本渲染失败: {e}")
            return await self.create_placeholder_images(image_prefix)
    
    async def create_placeholder_images(self, image_prefix: str) -> List[str]:
        """创建占位图片"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # 创建一个简单的占位图片
            img = Image.new('RGB', (400, 600), color='white')
            draw = ImageDraw.Draw(img)
            
            # 添加文字
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
            except:
                font = ImageFont.load_default()
            
            text = "文档图片\n(待生成)"
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (400 - text_width) // 2
            y = (600 - text_height) // 2
            
            draw.text((x, y), text, fill='black', font=font)
            
            # 保存占位图片
            image_filename = f"{image_prefix}_page_0.png"
            image_path = os.path.join(self.image_dir, image_filename)
            img.save(image_path)
            print(f"[DEBUG] 创建占位图片: {image_path}")
            
            return [f"/images/{image_filename}"]
        except Exception as e:
            print(f"创建占位图片失败: {e}")
            return [f"/images/placeholder.png"]
    
    async def create_placeholder_image(self) -> str:
        """创建占位图片"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # 创建一个简单的占位图片
            img = Image.new('RGB', (400, 600), color='white')
            draw = ImageDraw.Draw(img)
            
            # 添加文字
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
            except:
                font = ImageFont.load_default()
            
            text = "文档图片\n(待生成)"
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (400 - text_width) // 2
            y = (600 - text_height) // 2
            
            draw.text((x, y), text, fill='black', font=font)
            
            # 保存占位图片
            placeholder_path = os.path.join(self.image_dir, "placeholder.png")
            img.save(placeholder_path)
            
            return "/images/placeholder.png"
        except Exception as e:
            print(f"创建占位图片失败: {e}")
            return "/images/placeholder.png"
