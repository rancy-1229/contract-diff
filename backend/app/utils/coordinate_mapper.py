from typing import List, Dict, Any

class CoordinateMapper:
    def __init__(self):
        pass
    
    def build_char_sequence_map(self, document_data: Dict) -> Dict:
        """构建字符序列到坐标索引的映射 - 步骤3"""
        print("[DEBUG] 开始构建字符序列映射")
        
        char_sequence_map = {}
        char_index = 0
        
        for page in document_data.get("pages", []):
            page_index = page["page_index"]
            
            for block in page.get("blocks", []):
                for line in block.get("lines", []):
                    line_index = line["line_index"]
                    
                    for span in line.get("spans", []):
                        span_text = span["text"]
                        char_start_index = span.get("char_start_index", char_index)
                        
                        # 为每个字符创建映射
                        for i, char in enumerate(span_text):
                            char_key = f"{page_index}_{line_index}_{char_start_index + i}"
                            char_sequence_map[char_key] = {
                                "char": char,
                                "page_index": page_index,
                                "line_index": line_index,
                                "char_index": char_start_index + i,
                                "bbox": span.get("char_bboxes", [span["bbox"]])[i] if i < len(span.get("char_bboxes", [])) else span["bbox"],
                                "font": span.get("font", ""),
                                "size": span.get("size", 12),
                                "color": span.get("color", 0)
                            }
                        
                        char_index += len(span_text)
        
        print(f"[DEBUG] 字符序列映射构建完成，共{len(char_sequence_map)}个字符")
        return char_sequence_map
    
    def _convert_pdf_coords_to_image_coords(self, pdf_coords: List[float], page_height: float = 792.0, scale_factor: float = 2.0) -> List[float]:
        """将PDF坐标转换为图片坐标（基于原始图片像素尺寸）"""
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

    def map_diff_to_coordinates(self, diff_list: List[Dict], char_sequence_maps: Dict[str, Dict]) -> List[Dict]:
        """将差异结果映射回坐标 - 步骤4"""
        print("[DEBUG] 开始映射差异到坐标")
        
        mapped_diffs = []
        
        for diff_item in diff_list:
            mapped_diff = {
                "element_id": diff_item["element_id"],
                "type": diff_item["type"],
                "status": diff_item["status"],
                "page_index": diff_item["page_index"],
                "elements": diff_item["elements"],
                "diff": []
            }
            
            # 映射每个差异组
            for diff_group in diff_item.get("diff", []):
                mapped_group = []
                
                for char_info in diff_group:
                    # 查找字符在映射中的位置
                    char_key = self._find_char_key(char_info, char_sequence_maps)
                    
                    if char_key:
                        mapped_char = char_sequence_maps[char_key].copy()
                        
                        # 转换PDF坐标到图片坐标
                        pdf_bbox = mapped_char.get("bbox", [0, 0, 0, 0])
                        page_height = 792.0  # 默认A4页面高度，实际应该从页面数据获取
                        image_bbox = self._convert_pdf_coords_to_image_coords(pdf_bbox, page_height, 2.0)
                        
                        mapped_char.update({
                            "text": char_info["text"],
                            "doc_index": char_info["doc_index"],
                            "char_polygons": [image_bbox],  # 使用转换后的坐标
                            "bbox": image_bbox  # 更新bbox字段
                        })
                        mapped_group.append(mapped_char)
                    else:
                        # 如果找不到映射，使用原始信息
                        mapped_group.append(char_info)
                
                mapped_diff["diff"].append(mapped_group)
            
            mapped_diffs.append(mapped_diff)
        
        print(f"[DEBUG] 差异坐标映射完成，共{len(mapped_diffs)}个差异")
        return mapped_diffs
    
    def _find_char_key(self, char_info: Dict, char_sequence_maps: Dict[str, Dict]) -> str:
        """查找字符在映射中的键"""
        page_index = char_info.get("page_index", 0)
        line_index = char_info.get("line_index", 0)
        char_index = char_info.get("char_index", 0)
        
        # 尝试精确匹配
        char_key = f"{page_index}_{line_index}_{char_index}"
        if char_key in char_sequence_maps:
            return char_key
        
        # 尝试模糊匹配
        for key, mapped_char in char_sequence_maps.items():
            if (mapped_char.get("page_index", 0) == page_index and 
                mapped_char.get("line_index", 0) == line_index and
                mapped_char.get("char", "") == char_info.get("text", "")):
                return key
        
        return None
