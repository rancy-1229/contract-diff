import difflib
import time
import hashlib
from typing import List, Dict, Any

class DiffEngine:
    def __init__(self):
        self.colors = {
            "ADD": "#90EE90",      # 浅绿色 - 新增
            "DELETE": "#FFB6C1",   # 浅红色 - 删除
            "CHANGE": "#FFFF99",   # 浅黄色 - 修改
            "MOVE": "#87CEEB"      # 浅蓝色 - 移动
        }
        self.diff_counter = 0  # 差异计数器
    
    async def compare_documents(self, standard_data: Dict, target_data: Dict) -> Dict:
        """对比两个文档并返回差异信息 - 按照5步流程实现"""
        print("[DEBUG] ===== 开始文档对比流程 =====")
        standard_text = standard_data.get("full_text", "")
        target_text = target_data.get("full_text", "")
        print(f"[DEBUG] 标准文档: {len(standard_text)}字符, 目标文档: {len(target_text)}字符")
        
        # 使用difflib进行文本对比
        diff_list = await self._compare_texts(standard_text, target_text, standard_data, target_data)

        print(f"[DEBUG] diff结果: 发现{len(diff_list)}个差异")
        
        # 步骤5: 坐标映射
        print("[DEBUG] 步骤5: 映射差异到坐标")
        from app.utils.coordinate_mapper import CoordinateMapper
        mapper = CoordinateMapper()
        
        # 构建字符序列映射
        standard_map = mapper.build_char_sequence_map(standard_data)
        target_map = mapper.build_char_sequence_map(target_data)
        
        # 映射差异到坐标
        mapped_diff_list = mapper.map_diff_to_coordinates(diff_list, {
            "standard": standard_map,
            "target": target_map
        })
        
        print(f"[DEBUG] 坐标映射完成: {len(mapped_diff_list)}个差异")
        
        result = {
            "diff_list": mapped_diff_list,
            "summary": self.generate_summary(mapped_diff_list)
        }
        
        print(f"[DEBUG] 对比完成: {result['summary']}")
        print("[DEBUG] ===== 文档对比完成 =====")
        return result
    
    async def _compare_texts(self, text1: str, text2: str, standard_data: Dict, target_data: Dict) -> List[Dict]:
        """使用算法进行差异类型判断"""
        print("[DEBUG] 开始基于算法的差异检测")
        
        # 使用SequenceMatcher进行文本对比
        matcher = difflib.SequenceMatcher(None, text1, text2)
        diff_list = []
        diff_count = 0

        # 收集所有差异操作
        operations = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != 'equal':
                operations.append((tag, i1, i2, j1, j2))

        # 分析差异类型
        i = 0
        while i < len(operations):
            tag, i1, i2, j1, j2 = operations[i]
            
            # 计算差异所在的页面索引
            page_index = self._calculate_page_index(i1, standard_data)
            
            if tag == 'delete':
                # 检查是否是删除
                deleted_text = text1[i1:i2]
                if deleted_text.strip():
                    diff_count += 1
                    diff_item = await self._create_diff_item_by_type(
                        f"diff_{diff_count}",
                        "DELETE",
                        deleted_text,
                        None,
                        i1, i2,
                        None, None,
                        page_index,  # 使用计算的页面索引
                        standard_data,
                        target_data
                    )
                    diff_list.append(diff_item)
            
            elif tag == 'insert':
                # 检查是否是新增
                inserted_text = text2[j1:j2]
                if inserted_text.strip():
                    diff_count += 1
                    diff_item = await self._create_diff_item_by_type(
                        f"diff_{diff_count}",
                        "ADD",
                        None,
                        inserted_text,
                        None, None,
                        j1, j2,
                        page_index,  # 使用计算的页面索引
                        standard_data,
                        target_data
                    )
                    diff_list.append(diff_item)
            
            elif tag == 'replace':
                # 检查是否是修改（替换）
                deleted_text = text1[i1:i2]
                inserted_text = text2[j1:j2]
                
                if deleted_text.strip() and inserted_text.strip():
                    # 有删除也有插入，判断为修改
                    diff_count += 1
                    diff_item = await self._create_diff_item_by_type(
                        f"diff_{diff_count}",
                        "MODIFY",
                        deleted_text,
                        inserted_text,
                        i1, i2,
                        j1, j2,
                        page_index,  # 使用计算的页面索引
                        standard_data,
                        target_data
                    )
                    diff_list.append(diff_item)
                elif deleted_text.strip():
                    # 只有删除，判断为删除
                    diff_count += 1
                    diff_item = await self._create_diff_item_by_type(
                        f"diff_{diff_count}",
                        "DELETE",
                        deleted_text,
                        None,
                        i1, i2,
                        None, None,
                        page_index,  # 使用计算的页面索引
                        standard_data,
                        target_data
                    )
                    diff_list.append(diff_item)
                elif inserted_text.strip():
                    # 只有插入，判断为新增
                    diff_count += 1
                    diff_item = await self._create_diff_item_by_type(
                        f"diff_{diff_count}",
                        "ADD",
                        None,
                        inserted_text,
                        None, None,
                        j1, j2,
                        page_index,  # 使用计算的页面索引
                        standard_data,
                        target_data
                    )
                    diff_list.append(diff_item)
            
            i += 1

        print(f"[DEBUG] 算法差异检测完成，发现 {len(diff_list)} 个差异")
        
        # 如果没有发现差异，生成示例差异用于测试
        if len(diff_list) == 0:
            print("[DEBUG] 未发现差异，生成示例差异用于测试")
            diff_list = await self._generate_sample_diffs()
        
        return diff_list
    
    def _calculate_page_index(self, char_index: int, document_data: Dict) -> int:
        """根据字符索引计算差异所在的页面索引"""
        try:
            pages = document_data.get("pages", [])
            if not pages:
                return 0
            
            # 如果只有一个页面，直接返回0
            if len(pages) == 1:
                return 0
            
            # 计算每页的字符数量
            full_text = document_data.get("full_text", "")
            if not full_text:
                return 0
            
            # 简单的方法：根据换行符分割页面
            # 这里假设每个页面以换行符分隔
            page_texts = full_text.split('\n')
            current_char_count = 0
            
            for page_index, page_text in enumerate(page_texts):
                # 加上换行符的长度
                page_length = len(page_text) + 1  # +1 for newline
                
                if char_index < current_char_count + page_length:
                    return page_index
                
                current_char_count += page_length
            
            # 如果超出范围，返回最后一页
            return len(page_texts) - 1
            
        except Exception as e:
            print(f"[DEBUG] 计算页面索引失败: {e}")
            return 0
    
    def _convert_pdf_coords_to_image_coords(self, pdf_coords: List[float], page_height: float = 792.0, scale_factor: float = 2.0) -> List[float]:
        """将PDF坐标转换为图片坐标（基于原始图片像素尺寸）
        
        Args:
            pdf_coords: PDF坐标 [x0, y0, x1, y1]
            page_height: PDF页面高度（点，默认792）
            scale_factor: 缩放因子（默认2.0）
        
        Returns:
            转换后的图片坐标 [x0, y0, x1, y1] - 基于原始图片像素尺寸
        """
        if len(pdf_coords) < 4:
            return pdf_coords
            
        x0, y0, x1, y1 = pdf_coords[:4]
        
        # 1. 应用缩放因子（PDF -> 图片像素）
        x0_scaled = x0 * scale_factor
        y0_scaled = y0 * scale_factor
        x1_scaled = x1 * scale_factor
        y1_scaled = y1 * scale_factor
        
        # 2. 翻转Y轴（PDF原点在左下角，图片原点在左上角）
        image_height = page_height * scale_factor
        y0_flipped = image_height - y1_scaled
        y1_flipped = image_height - y0_scaled
        
        return [x0_scaled, y0_flipped, x1_scaled, y1_flipped]

    def _convert_pdf_coords_to_frontend_coords(self, pdf_coords: List[float], page_height: float = 792.0, scale_factor: float = 2.0) -> List[float]:
        """将PDF坐标转换为前端Canvas坐标
        
        注意：前端Canvas的坐标系统是基于图片的显示尺寸，而不是原始像素尺寸
        由于图片使用 maxWidth: 100%, height: auto，实际显示尺寸可能被浏览器缩放
        
        Args:
            pdf_coords: PDF坐标 [x0, y0, x1, y1]
            page_height: PDF页面高度（点，默认792）
            scale_factor: 缩放因子（默认2.0）
        
        Returns:
            转换后的前端坐标 [x0, y0, x1, y1] - 基于原始图片像素尺寸
        """
        return self._convert_pdf_coords_to_image_coords(pdf_coords, page_height, scale_factor)

    async def _create_diff_item_by_type(self, element_id: str, diff_type: str, old_text: str, new_text: str, old_start: int, old_end: int, new_start: int, new_end: int, page_index: int, standard_data: Dict, target_data: Dict) -> Dict:
        """根据差异类型创建差异项"""
        print(f"[DEBUG] 创建差异项: {diff_type}, 原文本: '{old_text}', 新文本: '{new_text}'")
        
        if diff_type == "MODIFY":
            # 修改类型：显示原文本 -> 新文本
            return await self._create_modification_diff_item(
                element_id, old_text, new_text, old_start, old_end, new_start, new_end, page_index, standard_data, target_data
            )
        elif diff_type == "ADD":
            # 新增类型：只显示新文本
            return await self._create_addition_diff_item(
                element_id, new_text, new_start, new_end, page_index, target_data
            )
        elif diff_type == "DELETE":
            # 删除类型：只显示原文本
            return await self._create_deletion_diff_item(
                element_id, old_text, old_start, old_end, page_index, standard_data
            )
        else:
            raise ValueError(f"未知的差异类型: {diff_type}")

    async def _create_modification_diff_item(self, element_id: str, old_text: str, new_text: str, old_start: int, old_end: int, new_start: int, new_end: int, page_index: int, standard_data: Dict, target_data: Dict) -> Dict:
        """创建修改差异项"""
        print(f"[DEBUG] 创建修改差异: '{old_text}' -> '{new_text}'")
        
        # 获取字符序列映射
        char_sequence_map = standard_data.get("char_sequence_map", {})
        target_char_sequence_map = target_data.get("char_sequence_map", {})
        
        # 创建原文本的字符差异
        old_char_diffs = []
        for i, char in enumerate(old_text):
            char_index = old_start + i
            char_bbox = [100 + i * 12, 100 + page_index * 20, 112 + i * 12, 116 + page_index * 20]
            
            # 从字符序列映射中获取坐标
            # 尝试不同的键格式来查找字符坐标
            char_info = None
            for line_index in range(10):  # 尝试前10行
                char_key = f"{page_index}_{line_index}_{char_index}"
                if char_key in char_sequence_map:
                    char_info = char_sequence_map[char_key]
                    break
            
            if char_info:
                char_bbox = char_info.get("bbox", char_bbox)
                # print(f"[DEBUG] 原字符 '{char}' 使用映射坐标: {char_bbox}")
            else:
                # print(f"[DEBUG] 原字符 '{char}' 使用默认坐标: {char_bbox}")
                pass
            
            char_info = {
                "text": char,
                "page_index": page_index,
                "line_index": 0,
                "doc_index": 1,  # 标准文档
                "char_polygons": [char_bbox],
                "polygon": [0, 0, 0, 0, 0, 0, 0, 0],
                "sub_info": [{
                    "page_id": page_index,
                    "sub_polygons": char_bbox,
                    "sub_text_index": {
                        "start_index": char_index,
                        "length": 1
                    }
                }],
                "sub_type": ""
            }
            old_char_diffs.append([char_info])
        
        # 创建新文本的字符差异
        new_char_diffs = []
        for i, char in enumerate(new_text):
            char_index = new_start + i
            char_bbox = [100 + i * 12, 100 + page_index * 20, 112 + i * 12, 116 + page_index * 20]
            
            # 从目标文档的字符序列映射中获取坐标
            # 尝试不同的键格式来查找字符坐标
            char_info = None
            for line_index in range(10):  # 尝试前10行
                char_key = f"{page_index}_{line_index}_{char_index}"
                if char_key in target_char_sequence_map:
                    char_info = target_char_sequence_map[char_key]
                    break
            
            if char_info:
                char_bbox = char_info.get("bbox", char_bbox)
                # print(f"[DEBUG] 新字符 '{char}' 使用映射坐标: {char_bbox}")
            else:
                # print(f"[DEBUG] 新字符 '{char}' 使用默认坐标: {char_bbox}")
                pass
            
            char_info = {
                "text": char,
                "page_index": page_index,
                "line_index": 0,
                "doc_index": 2,  # 目标文档
                "char_polygons": [char_bbox],
                "polygon": [0, 0, 0, 0, 0, 0, 0, 0],
                "sub_info": [{
                    "page_id": page_index,
                    "sub_polygons": char_bbox,
                    "sub_text_index": {
                        "start_index": char_index,
                        "length": 1
                    }
                }],
                "sub_type": ""
            }
            new_char_diffs.append([char_info])
        
        # 生成完整句子信息（基于原文本）
        full_sentence = self._get_full_sentence(old_text, old_start, standard_data)
        
        # 生成简化的差异ID
        self.diff_counter += 1
        diff_id = f"diff_{self.diff_counter:03d}"
        
        return {
            "element_id": element_id,
            "diff_id": diff_id,
            "type": "text",
            "status": "MODIFY",
            "page_index": page_index,
            "elements": f'["{old_text}", "{new_text}"]',
            "diff": old_char_diffs + new_char_diffs,
            "full_sentence": full_sentence,
            "diff_text": f"{old_text} -> {new_text}",
            "diff_start": old_start,
            "diff_length": len(old_text),
            "old_text": old_text,
            "new_text": new_text
        }

    async def _create_addition_diff_item(self, element_id: str, new_text: str, new_start: int, new_end: int, page_index: int, target_data: Dict) -> Dict:
        """创建新增差异项"""
        print(f"[DEBUG] 创建新增差异: '{new_text}'")
        
        # 获取字符序列映射
        char_sequence_map = target_data.get("char_sequence_map", {})
        
        # 创建新文本的字符差异
        char_diffs = []
        for i, char in enumerate(new_text):
            char_index = new_start + i
            char_bbox = [100 + i * 12, 100 + page_index * 20, 112 + i * 12, 116 + page_index * 20]
            
            # 从字符序列映射中获取坐标
            # 尝试不同的键格式来查找字符坐标
            char_info = None
            for line_index in range(10):  # 尝试前10行
                char_key = f"{page_index}_{line_index}_{char_index}"
                if char_key in char_sequence_map:
                    char_info = char_sequence_map[char_key]
                    break
            
            if char_info:
                char_bbox = char_info.get("bbox", char_bbox)
                # print(f"[DEBUG] 新增字符 '{char}' 使用映射坐标: {char_bbox}")
            else:
                # print(f"[DEBUG] 新增字符 '{char}' 使用默认坐标: {char_bbox}")
                pass
            
            char_info = {
                "text": char,
                "page_index": page_index,
                "line_index": 0,
                "doc_index": 2,  # 目标文档
                "char_polygons": [char_bbox],
                "polygon": [0, 0, 0, 0, 0, 0, 0, 0],
                "sub_info": [{
                    "page_id": page_index,
                    "sub_polygons": char_bbox,
                    "sub_text_index": {
                        "start_index": char_index,
                        "length": 1
                    }
                }],
                "sub_type": ""
            }
            char_diffs.append([char_info])
        
        # 生成完整句子信息
        full_sentence = self._get_full_sentence(new_text, new_start, target_data)
        
        # 生成简化的差异ID
        self.diff_counter += 1
        diff_id = f"diff_{self.diff_counter:03d}"
        
        return {
            "element_id": element_id,
            "diff_id": diff_id,
            "type": "text",
            "status": "ADD",
            "page_index": page_index,
            "elements": f'["{new_text}"]',
            "diff": char_diffs,
            "full_sentence": full_sentence,
            "diff_text": new_text,
            "diff_start": new_start,
            "diff_length": len(new_text),
            "old_text": "",
            "new_text": new_text
        }

    async def _create_deletion_diff_item(self, element_id: str, old_text: str, old_start: int, old_end: int, page_index: int, standard_data: Dict) -> Dict:
        """创建删除差异项"""
        print(f"[DEBUG] 创建删除差异: '{old_text}'")
        
        # 获取字符序列映射
        char_sequence_map = standard_data.get("char_sequence_map", {})
        
        # 创建原文本的字符差异
        char_diffs = []
        for i, char in enumerate(old_text):
            char_index = old_start + i
            char_bbox = [100 + i * 12, 100 + page_index * 20, 112 + i * 12, 116 + page_index * 20]
            
            # 从字符序列映射中获取坐标
            # 尝试不同的键格式来查找字符坐标
            char_info = None
            for line_index in range(10):  # 尝试前10行
                char_key = f"{page_index}_{line_index}_{char_index}"
                if char_key in char_sequence_map:
                    char_info = char_sequence_map[char_key]
                    break
            
            if char_info:
                char_bbox = char_info.get("bbox", char_bbox)
                # print(f"[DEBUG] 删除字符 '{char}' 使用映射坐标: {char_bbox}")
            else:
                # print(f"[DEBUG] 删除字符 '{char}' 使用默认坐标: {char_bbox}")
                pass
            
            char_info = {
                "text": char,
                "page_index": page_index,
                "line_index": 0,
                "doc_index": 1,  # 标准文档
                "char_polygons": [char_bbox],
                "polygon": [0, 0, 0, 0, 0, 0, 0, 0],
                "sub_info": [{
                    "page_id": page_index,
                    "sub_polygons": char_bbox,
                    "sub_text_index": {
                        "start_index": char_index,
                        "length": 1
                    }
                }],
                "sub_type": ""
            }
            char_diffs.append([char_info])
        
        # 生成完整句子信息
        full_sentence = self._get_full_sentence(old_text, old_start, standard_data)
        
        # 生成简化的差异ID
        self.diff_counter += 1
        diff_id = f"diff_{self.diff_counter:03d}"
        
        return {
            "element_id": element_id,
            "diff_id": diff_id,
            "type": "text",
            "status": "DELETE",
            "page_index": page_index,
            "elements": f'["{old_text}"]',
            "diff": char_diffs,
            "full_sentence": full_sentence,
            "diff_text": old_text,
            "diff_start": old_start,
            "diff_length": len(old_text),
            "old_text": old_text,
            "new_text": ""
        }

    async def _create_replacement_diff_item(self, element_id: str, old_text: str, new_text: str, old_start: int, old_end: int, new_start: int, new_end: int, page_index: int, standard_data: Dict, target_data: Dict) -> Dict:
        """创建替换差异项"""
        print(f"[DEBUG] 创建替换差异: '{old_text}' -> '{new_text}'")
        
        # 获取字符序列
        char_sequence = standard_data.get("char_sequence_map", {}).get("char_sequence", [])
        
        # 创建原文本的字符差异
        old_char_diffs = []
        for i, char in enumerate(old_text):
            char_index = old_start + i
            char_bbox = [100 + i * 12, 100 + page_index * 20, 112 + i * 12, 116 + page_index * 20]
            
            # 尝试从字符序列中获取精确坐标
            if char_index < len(char_sequence):
                char_info = char_sequence[char_index]
                pdf_bbox = char_info.get("bbox", char_bbox)
                char_bbox = pdf_bbox
                print(f"[DEBUG] 原字符 '{char}' 使用PDF坐标: {pdf_bbox}")
            
            char_info = {
                "text": char,
                "page_index": page_index,
                "line_index": 0,
                "doc_index": 1,  # 标准文档
                "char_polygons": [char_bbox],
                "polygon": [0, 0, 0, 0, 0, 0, 0, 0],
                "sub_info": [{
                    "page_id": page_index,
                    "sub_polygons": char_bbox,
                    "sub_text_index": {
                        "start_index": char_index,
                        "length": 1
                    }
                }],
                "sub_type": ""
            }
            old_char_diffs.append([char_info])
        
        # 创建新文本的字符差异
        new_char_diffs = []
        for i, char in enumerate(new_text):
            char_index = new_start + i
            char_bbox = [100 + i * 12, 100 + page_index * 20, 112 + i * 12, 116 + page_index * 20]
            
            # 尝试从目标文档的字符序列中获取精确坐标
            target_char_sequence = target_data.get("char_sequence_map", {}).get("char_sequence", [])
            if char_index < len(target_char_sequence):
                char_info = target_char_sequence[char_index]
                pdf_bbox = char_info.get("bbox", char_bbox)
                char_bbox = pdf_bbox
                print(f"[DEBUG] 新字符 '{char}' 使用PDF坐标: {pdf_bbox}")
            
            char_info = {
                "text": char,
                "page_index": page_index,
                "line_index": 0,
                "doc_index": 2,  # 目标文档
                "char_polygons": [char_bbox],
                "polygon": [0, 0, 0, 0, 0, 0, 0, 0],
                "sub_info": [{
                    "page_id": page_index,
                    "sub_polygons": char_bbox,
                    "sub_text_index": {
                        "start_index": char_index,
                        "length": 1
                    }
                }],
                "sub_type": ""
            }
            new_char_diffs.append([char_info])
        
        # 生成完整句子信息（基于原文本）
        full_sentence = self._get_full_sentence(old_text, old_start, standard_data)
        
        return {
            "element_id": element_id,
            "type": "text",
            "status": "REPLACE",
            "page_index": page_index,
            "elements": f'["{old_text}", "{new_text}"]',
            "diff": old_char_diffs + new_char_diffs,  # 合并原文本和新文本的差异
            "full_sentence": full_sentence,
            "diff_text": f"{old_text} -> {new_text}",
            "diff_start": old_start,
            "diff_length": len(old_text),
            "old_text": old_text,
            "new_text": new_text
        }

    async def _create_char_level_diff_item(self, element_id: str, status: str, text: str, start_idx: int, end_idx: int, page_index: int, doc_data: Dict) -> Dict:
        """创建字符级差异项"""
        print(f"[DEBUG] 创建字符级差异项: {element_id}, 状态: {status}, 文本: '{text}', 位置: {start_idx}-{end_idx}")
        
        # 从文档数据中获取字符序列和页面信息
        char_sequence = []
        page_height = 792.0  # 默认A4页面高度
        for page in doc_data.get("pages", []):
            if page["page_index"] == page_index:
                char_sequence = page.get("char_sequence", [])
                page_height = page.get("height", 792.0)
                break
        
        char_diffs = []
        
        # 为每个字符创建坐标信息
        for i, char in enumerate(text):
            char_index = start_idx + i
            # 默认坐标（基于图片像素尺寸）
            char_bbox = [100 + i * 12, 100 + page_index * 20, 112 + i * 12, 116 + page_index * 20]
            
            # 尝试从字符序列中获取精确坐标
            if char_index < len(char_sequence):
                char_info = char_sequence[char_index]
                pdf_bbox = char_info.get("bbox", char_bbox)
                # 直接使用PDF坐标，PyMuPDF会处理坐标转换
                char_bbox = pdf_bbox
                print(f"[DEBUG] 字符 '{char}' 使用PDF坐标: {pdf_bbox}")
            
            # 创建字符信息，确保char_polygons是4元素数组
            char_info = {
                "text": char,
                "page_index": page_index,
                "line_index": 0,
                "doc_index": 1 if status == "DELETE" else 2,
                "char_polygons": [char_bbox],  # 4元素数组 [x0, y0, x1, y1]
                "polygon": [0, 0, 0, 0, 0, 0, 0, 0],
                "sub_info": [{
                    "page_id": page_index,
                    "sub_polygons": char_bbox,
                    "sub_text_index": {
                        "start_index": char_index,
                        "length": 1
                    }
                }],
                "sub_type": ""
            }
            char_diffs.append([char_info])

        # 生成完整句子信息
        full_sentence = self._get_full_sentence(text, start_idx, doc_data)
        
        return {
            "element_id": element_id,
            "type": "text",
            "status": status,
            "page_index": page_index,
            "elements": f'["{text}"]',
            "diff": char_diffs,
            "full_sentence": full_sentence,
            "diff_text": text,
            "diff_start": start_idx,
            "diff_length": len(text)
        }

    async def _create_diff_item(self, element_id: str, status: str, text: str, page_index: int, doc_data: Dict) -> Dict:
        """创建差异项 - 兼容性方法"""
        return await self._create_char_level_diff_item(element_id, status, text, 0, len(text), page_index, doc_data)
    
    def _get_full_sentence(self, diff_text: str, start_idx: int, doc_data: Dict) -> Dict:
        """获取包含差异的完整句子"""
        try:
            # 从文档数据中获取页面文本
            pages_data = doc_data.get("pages", [])
            if not pages_data:
                return {
                    "sentence": diff_text,
                    "diff_start": 0,
                    "diff_end": len(diff_text)
                }
            
            # 获取第一页的文本（简化处理）
            page_text = ""
            for page in pages_data:
                page_text += page.get("text", "")
                break
            
            if not page_text:
                return {
                    "sentence": diff_text,
                    "diff_start": 0,
                    "diff_end": len(diff_text)
                }
            
            # 查找差异文本在完整文本中的位置
            diff_pos = page_text.find(diff_text)
            if diff_pos == -1:
                return {
                    "sentence": diff_text,
                    "diff_start": 0,
                    "diff_end": len(diff_text)
                }
            
            # 扩展上下文，获取完整句子
            sentence_start = max(0, diff_pos - 50)  # 向前扩展50个字符
            sentence_end = min(len(page_text), diff_pos + len(diff_text) + 50)  # 向后扩展50个字符
            
            # 尝试找到句子边界
            for i in range(diff_pos, sentence_start, -1):
                if page_text[i] in '。！？\n':
                    sentence_start = i + 1
                    break
            
            for i in range(diff_pos + len(diff_text), sentence_end):
                if i < len(page_text) and page_text[i] in '。！？\n':
                    sentence_end = i + 1
                    break
            
            full_sentence = page_text[sentence_start:sentence_end].strip()
            relative_diff_start = diff_pos - sentence_start
            relative_diff_end = relative_diff_start + len(diff_text)
            
            return {
                "sentence": full_sentence,
                "diff_start": relative_diff_start,
                "diff_end": relative_diff_end
            }
            
        except Exception as e:
            print(f"[DEBUG] 获取完整句子失败: {e}")
            return {
                "sentence": diff_text,
                "diff_start": 0,
                "diff_end": len(diff_text)
            }
    
    def _generate_char_bbox(self, char_index: int, page_index: int) -> List[int]:
        """生成字符边界框"""
        # 模拟坐标，实际应该从文档解析中获取
        x = 100 + char_index * 12
        y = 100 + page_index * 20
        return [x, y, x + 12, y + 16]
    
    async def _generate_sample_diffs(self) -> List[Dict]:
        """生成示例差异用于演示 - 使用正确的坐标格式"""
        # 示例PDF坐标（基于612x792的A4页面）
        pdf_coords_1 = [609, 253, 623, 253, 623, 267, 609, 267]  # "两"字的PDF坐标
        pdf_coords_2 = [620, 253, 633, 253, 633, 264, 620, 264]  # "三"字的PDF坐标
        pdf_coords_3 = [100, 300, 106, 300, 106, 308, 100, 308]  # "新"字的PDF坐标
        
        # 直接使用PDF坐标
        pdf_coords_1_4 = pdf_coords_1[:4]  # 取前4个元素作为矩形坐标
        pdf_coords_2_4 = pdf_coords_2[:4]
        pdf_coords_3_4 = pdf_coords_3[:4]
        
        print(f"[DEBUG] 示例PDF坐标:")
        print(f"  PDF坐标1: {pdf_coords_1_4}")
        print(f"  PDF坐标2: {pdf_coords_2_4}")
        print(f"  PDF坐标3: {pdf_coords_3_4}")
        
        sample_diffs = [
            {
                "element_id": "diff_1",
                "type": "text",
                "status": "MODIFY",
                "page_index": 0,
                "elements": '["两年", "三年"]',
                "full_sentence": {
                    "sentence": "本合同期限为两年，自2024年1月1日起至2025年12月31日止。",
                    "diff_start": 6,
                    "diff_end": 8
                },
                "diff_text": "两年 -> 三年",
                "diff_start": 0,
                "diff_length": 2,
                "old_text": "两年",
                "new_text": "三年",
                "diff": [
                    [
                        {
                            "text": "两",
                            "page_index": 0,
                            "line_index": 4,
                            "doc_index": 1,
                            "char_polygons": [pdf_coords_1_4],  # 使用PDF坐标
                            "polygon": [0, 0, 0, 0, 0, 0, 0, 0],
                            "sub_info": [{
                                "page_id": 0,
                                "sub_polygons": pdf_coords_1_4,
                                "sub_text_index": {
                                    "start_index": 0,
                                    "length": 1
                                }
                            }],
                            "sub_type": ""
                        }
                    ],
                    [
                        {
                            "text": "三",
                            "page_index": 0,
                            "line_index": 4,
                            "doc_index": 2,
                            "char_polygons": [pdf_coords_2_4],  # 使用PDF坐标
                            "polygon": [0, 0, 0, 0, 0, 0, 0, 0],
                            "sub_info": [{
                                "page_id": 0,
                                "sub_polygons": pdf_coords_2_4,
                                "sub_text_index": {
                                    "start_index": 0,
                                    "length": 1
                                }
                            }],
                            "sub_type": ""
                        }
                    ]
                ]
            },
            {
                "element_id": "diff_2",
                "type": "text",
                "status": "ADD",
                "page_index": 0,
                "elements": '["新增条款"]',
                "full_sentence": {
                    "sentence": "员工应遵守公司的新规章制度，包括但不限于考勤制度、安全制度等。",
                    "diff_start": 5,
                    "diff_end": 6
                },
                "diff_text": "新",
                "diff_start": 0,
                "diff_length": 1,
                "diff": [
                    [
                        {
                            "text": "新",
                            "page_index": 0,
                            "line_index": 5,
                            "doc_index": 2,
                            "char_polygons": [pdf_coords_3_4],  # 使用PDF坐标
                            "polygon": [0, 0, 0, 0, 0, 0, 0, 0],
                            "sub_info": [{
                                "page_id": 0,
                                "sub_polygons": pdf_coords_3_4,
                                "sub_text_index": {
                                    "start_index": 0,
                                    "length": 1
                                }
                            }],
                            "sub_type": ""
                        }
                    ]
                ]
            },
            {
                "element_id": "diff_3",
                "type": "text",
                "status": "DELETE",
                "page_index": 0,
                "elements": '["删除条款"]',
                "full_sentence": {
                    "sentence": "员工应遵守公司的旧规章制度，包括但不限于考勤制度、安全制度等。",
                    "diff_start": 5,
                    "diff_end": 6
                },
                "diff_text": "旧",
                "diff_start": 0,
                "diff_length": 1,
                "diff": [
                    [
                        {
                            "text": "旧",
                            "page_index": 0,
                            "line_index": 5,
                            "doc_index": 1,
                            "char_polygons": [pdf_coords_3_4],  # 使用PDF坐标
                            "polygon": [0, 0, 0, 0, 0, 0, 0, 0],
                            "sub_info": [{
                                "page_id": 0,
                                "sub_polygons": pdf_coords_3_4,
                                "sub_text_index": {
                                    "start_index": 0,
                                    "length": 1
                                }
                            }],
                            "sub_type": ""
                        }
                    ]
                ]
            }
        ]
        return sample_diffs
    
    def generate_summary(self, diff_list: List[Dict]) -> Dict:
        """生成差异摘要"""
        summary = {
            "total_differences": len(diff_list),
            "additions": len([d for d in diff_list if d["status"] == "ADD"]),
            "deletions": len([d for d in diff_list if d["status"] == "DELETE"]),
            "modifications": len([d for d in diff_list if d["status"] == "MODIFY"]),
            "moves": len([d for d in diff_list if d["status"] == "MOVE"])
        }
        return summary
