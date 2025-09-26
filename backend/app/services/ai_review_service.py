"""
AI审查差异服务
"""

import os
import hashlib
import time
import json
import httpx
from typing import Dict, List, Optional
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class AIReviewService:
    """AI审查差异服务"""
    
    def __init__(self):
        """初始化AI审查服务"""
        self.base_url = settings.ARK_BASE_URL
        self.api_key = settings.ARK_API_KEY
        self.model = settings.ARK_MODEL
        self.client = httpx.AsyncClient(timeout=300.0)
    
    def generate_diff_id(self, diff_data: Dict) -> str:
        """生成差异唯一标识"""
        # 优先使用element_id，如果没有则使用diff_id，最后生成一个
        return diff_data.get('element_id') or diff_data.get('diff_id') or f"diff_{int(time.time())}"
    
    def extract_paragraph_context(self, diff_data: Dict, standard_doc_content: Dict = None, target_doc_content: Dict = None) -> Dict:
        """提取差异的段落级上下文"""
        try:
            # 首先尝试从diff字段中提取文本和位置信息
            diff = diff_data.get('diff', [])
            if diff and len(diff) >= 2:
                old_text = ''
                new_text = ''
                old_start_index = None
                new_start_index = None
                
                if diff[0] and len(diff[0]) > 0:
                    old_item = diff[0][0]
                    old_text = old_item.get('text', '')
                    if 'sub_info' in old_item and old_item['sub_info']:
                        old_start_index = old_item['sub_info'][0].get('sub_text_index', {}).get('start_index')
                
                if diff[1] and len(diff[1]) > 0:
                    new_item = diff[1][0]
                    new_text = new_item.get('text', '')
                    if 'sub_info' in new_item and new_item['sub_info']:
                        new_start_index = new_item['sub_info'][0].get('sub_text_index', {}).get('start_index')
                
                # 尝试从文档内容中提取段落级上下文
                if old_start_index is not None and standard_doc_content:
                    old_context = self._extract_context_around_position(standard_doc_content, old_start_index)
                else:
                    old_context = old_text
                
                if new_start_index is not None and target_doc_content:
                    new_context = self._extract_context_around_position(target_doc_content, new_start_index)
                else:
                    new_context = new_text
                
                if old_context or new_context:
                    return {
                        'sentence': f"原条款：{old_context}，修改为：{new_context}",
                        'standard_text': old_context,
                        'target_text': new_context,
                        'char_diff': f"{old_text} → {new_text}"
                    }
            
            # 如果没有diff字段，尝试从elements字段提取
            elements = diff_data.get('elements', '')
            if elements:
                try:
                    import json
                    elements_list = json.loads(elements)
                    if len(elements_list) >= 2:
                        return {
                            'sentence': f"原条款：{elements_list[0]}，修改为：{elements_list[1]}",
                            'standard_text': elements_list[0],
                            'target_text': elements_list[1],
                            'char_diff': f"{elements_list[0]} → {elements_list[1]}"
                        }
                except:
                    pass
            
            # 检查是否有full_sentence字段
            full_sentence = diff_data.get('full_sentence', {})
            if full_sentence:
                sentence = full_sentence.get('sentence', '')
                standard_text = full_sentence.get('standard_text', '')
                target_text = full_sentence.get('target_text', '')
                
                if sentence and len(sentence) > 10:
                    return {
                        'sentence': sentence,
                        'standard_text': standard_text or sentence,
                        'target_text': target_text or sentence,
                        'char_diff': ''
                    }
            
            # 最后的备选方案
            old_text = diff_data.get('old_text', '')
            new_text = diff_data.get('new_text', '')
            
            if old_text or new_text:
                return {
                    'sentence': f"原条款：{old_text}，修改为：{new_text}",
                    'standard_text': old_text,
                    'target_text': new_text,
                    'char_diff': f"{old_text} → {new_text}"
                }
            
        except Exception as e:
            logger.error(f"提取段落上下文失败: {str(e)}")
        
        return {
            'sentence': '无法提取条款内容',
            'standard_text': '',
            'target_text': '',
            'char_diff': ''
        }
    
    def _extract_context_around_position(self, doc_content: Dict, position: int, context_size: int = 200) -> str:
        """从文档内容中提取指定位置周围的上下文"""
        try:
            full_text = doc_content.get('full_text', '')
            if not full_text or position is None:
                return ''
            
            # 确保位置在有效范围内
            position = max(0, min(position, len(full_text) - 1))
            
            # 向前查找句号或段落边界
            start_pos = position
            for i in range(context_size):
                if start_pos <= 0:
                    break
                if full_text[start_pos] in '。\n':
                    start_pos += 1
                    break
                start_pos -= 1
            
            # 向后查找句号或段落边界
            end_pos = position
            for i in range(context_size):
                if end_pos >= len(full_text):
                    break
                if full_text[end_pos] in '。\n':
                    end_pos += 1
                    break
                end_pos += 1
            
            # 提取上下文
            context = full_text[start_pos:end_pos].strip()
            
            # 如果上下文太短，尝试扩展
            if len(context) < 50:
                start_pos = max(0, position - 100)
                end_pos = min(len(full_text), position + 100)
                context = full_text[start_pos:end_pos].strip()
            
            return context
            
        except Exception as e:
            logger.error(f"提取位置上下文失败: {str(e)}")
            return ''
    
    async def review_diff(self, diff_data: Dict, standard_doc_content: Dict = None, target_doc_content: Dict = None) -> Dict:
        """审查单个差异"""
        try:
            # 生成差异ID
            diff_id = self.generate_diff_id(diff_data)
            
            # 提取段落级上下文
            context_info = self.extract_paragraph_context(diff_data, standard_doc_content, target_doc_content)
            standard_text = context_info['standard_text']
            target_text = context_info['target_text']
            char_diff = context_info.get('char_diff', '')
            
            if not standard_text or not target_text:
                return {
                    'diff_id': diff_id,
                    'error': '无法提取有效的条款内容'
                }
            
            # 构建提示词
            prompt = f"""你是合同审查专家，请分析以下合同条款差异并给出风险评估和修改建议。

标准条款：
{standard_text}

目标条款：
{target_text}

字符级差异：{char_diff}

请从以下角度分析：
1. 风险级别（高/中/低）
2. 是否符合法律规定（如劳动合同法/合同法）
3. 审查意见或修改建议
4. 差异ID：{diff_id}

请按照以下格式输出：
风险级别：[高/中/低]
法律合规：[符合/不符合/部分符合]
审查意见：[详细的风险评估和修改建议]
差异ID：{diff_id}"""
            
            # 调用AI模型
            review_content = await self._call_ai_api(prompt)
            
            # 解析AI返回结果
            review_result = self.parse_ai_response(review_content, diff_id)
            
            return {
                'diff_id': diff_id,
                'standard_text': standard_text,
                'target_text': target_text,
                'char_diff': char_diff,
                'review_result': review_result
            }
            
        except Exception as e:
            logger.error(f"AI审查失败: {str(e)}")
            return {
                'diff_id': self.generate_diff_id(diff_data),
                'error': f'AI审查失败: {str(e)}'
            }
    
    def parse_ai_response(self, response: str, diff_id: str) -> Dict:
        """解析AI返回的审查结果"""
        try:
            lines = response.strip().split('\n')
            result = {
                'risk_level': '中',
                'legal_compliance': '符合',
                'review_opinion': '暂无审查意见',
                'suggestions': '',
                'raw_response': response
            }
            
            for line in lines:
                line = line.strip()
                if line.startswith('风险级别：'):
                    result['risk_level'] = line.replace('风险级别：', '').strip()
                elif line.startswith('法律合规：'):
                    result['legal_compliance'] = line.replace('法律合规：', '').strip()
                elif line.startswith('审查意见：'):
                    result['review_opinion'] = line.replace('审查意见：', '').strip()
                elif line.startswith('修改建议：'):
                    result['suggestions'] = line.replace('修改建议：', '').strip()
            
            return result
            
        except Exception as e:
            logger.error(f"解析AI响应失败: {str(e)}")
            return {
                'risk_level': '中',
                'legal_compliance': '符合',
                'review_opinion': f'解析失败: {str(e)}',
                'suggestions': '',
                'raw_response': response
            }
    
    async def review_multiple_diffs(self, diff_list: List[Dict], standard_doc_content: Dict = None, target_doc_content: Dict = None) -> List[Dict]:
        """批量审查多个差异 - 一次性发送给AI模型"""
        try:
            print(f"[DEBUG] AI审查服务开始: diff_list长度={len(diff_list)}")
            if not diff_list:
                print(f"[DEBUG] diff_list为空，返回空结果")
                return []
            
            print(f"[DEBUG] API Key存在: {bool(self.api_key)}, Model存在: {bool(self.model)}")
            if not self.api_key or not self.model:
                logger.error("AI审查服务未正确初始化")
                print(f"[DEBUG] AI审查服务未正确初始化，返回默认结果")
                return self._create_default_results(diff_list)
            
            # 构建批量审查的提示词
            prompt_parts = [
                "你是合同审查专家，请分析以下合同条款差异并给出风险评估和修改建议。\n"
            ]
            
            # 为每个差异构建内容
            for i, diff_data in enumerate(diff_list, 1):
                diff_id = self.generate_diff_id(diff_data)
                context_info = self.extract_paragraph_context(diff_data, standard_doc_content, target_doc_content)
                standard_text = context_info['standard_text']
                target_text = context_info['target_text']
                char_diff = context_info.get('char_diff', '')
                
                if standard_text or target_text:
                    prompt_parts.append(f"差异 {diff_id}:")
                    prompt_parts.append(f"标准条款：{standard_text}")
                    prompt_parts.append(f"目标条款：{target_text}")
                    if char_diff:
                        prompt_parts.append(f"字符级差异：{char_diff}")
                    prompt_parts.append("")  # 空行分隔
            
            prompt_parts.append("请为每个差异输出以下信息：")
            prompt_parts.append("1. 差异ID")
            prompt_parts.append("2. 风险级别（高/中/低）")
            prompt_parts.append("3. 法律合规性（符合/不符合/部分符合）")
            prompt_parts.append("4. 审查意见和修改建议")
            prompt_parts.append("")
            prompt_parts.append("请严格按照以下JSON格式输出，不要包含任何其他文字：")
            prompt_parts.append('{"reviews": [{"diff_id": "diff_xxx", "risk_level": "高/中/低", "compliance": "符合/不符合/部分符合", "review_suggestions": "详细意见"}]}')
            
            # 调用AI模型
            try:
                print(f"[DEBUG] 开始调用AI API...")
                ai_response = await self._call_ai_api("\n".join(prompt_parts))
                print(f"[DEBUG] AI API返回响应长度: {len(ai_response) if ai_response else 0}")
                print(f"[DEBUG] AI API响应内容: {ai_response[:500]}...")  # 只显示前500个字符
                
                results = self.parse_batch_ai_response(ai_response, diff_list)
                print(f"[DEBUG] 解析后的结果数量: {len(results)}")
                return results
            except Exception as e:
                logger.error(f"AI API调用失败: {str(e)}")
                print(f"[DEBUG] AI API调用失败: {str(e)}")
                raise e
            
        except Exception as e:
            logger.error(f"批量AI审查失败: {str(e)}")
            # 如果批量失败，返回默认结果
            return self._create_default_results(diff_list)
    
    def parse_batch_ai_response(self, response: str, diff_list: List[Dict]) -> List[Dict]:
        """解析批量AI返回的审查结果"""
        try:
            # 尝试解析JSON格式
            import json
            
            # 清理响应文本，提取JSON部分
            response_clean = response.strip()
            if response_clean.startswith('```json'):
                response_clean = response_clean[7:]
            if response_clean.endswith('```'):
                response_clean = response_clean[:-3]
            
            # 尝试找到JSON对象
            start_idx = response_clean.find('{')
            end_idx = response_clean.rfind('}') + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = response_clean[start_idx:end_idx]
                data = json.loads(json_str)
                
                if 'reviews' in data and isinstance(data['reviews'], list):
                    results = []
                    for review in data['reviews']:
                        results.append({
                            'diff_id': review.get('diff_id', ''),
                            'risk_level': review.get('risk_level', '中'),
                            'compliance': review.get('compliance', '符合'),
                            'review_suggestions': review.get('review_suggestions', '暂无审查意见'),
                            'raw_ai_response': response
                        })
                    
                    # 确保所有差异都有结果
                    for diff_data in diff_list:
                        diff_id = diff_data.get('diff_id')
                        if not any(r['diff_id'] == diff_id for r in results):
                            results.append({
                                'diff_id': diff_id,
                                'risk_level': '中',
                                'compliance': '符合',
                                'review_suggestions': 'AI审查失败，请手动审查',
                                'raw_ai_response': '解析失败'
                            })
                    
                    return results
            
            # 如果JSON解析失败，回退到文本解析
            logger.warning("JSON解析失败，回退到文本解析")
            return self._parse_text_response(response, diff_list)
            
        except Exception as e:
            logger.error(f"解析批量AI响应失败: {str(e)}")
            # 返回默认结果
            results = []
            for diff_data in diff_list:
                results.append({
                    'diff_id': diff_data.get('diff_id', ''),
                    'risk_level': '中',
                    'compliance': '符合',
                    'review_suggestions': f'解析失败: {str(e)}',
                    'raw_ai_response': response
                })
            return results
    
    def _parse_text_response(self, response: str, diff_list: List[Dict]) -> List[Dict]:
        """解析文本格式的AI响应（备用方法）"""
        try:
            results = []
            sections = response.split('---')
            
            for section in sections:
                if not section.strip():
                    continue
                    
                lines = section.strip().split('\n')
                result = {
                    'diff_id': '',
                    'risk_level': '中',
                    'compliance': '符合',
                    'review_suggestions': '暂无审查意见',
                    'raw_ai_response': section.strip()
                }
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('差异ID:'):
                        result['diff_id'] = line.replace('差异ID:', '').strip()
                    elif line.startswith('风险级别:'):
                        result['risk_level'] = line.replace('风险级别:', '').strip()
                    elif line.startswith('法律合规:'):
                        result['compliance'] = line.replace('法律合规:', '').strip()
                    elif line.startswith('审查意见:'):
                        result['review_suggestions'] = line.replace('审查意见:', '').strip()
                
                if result['diff_id']:
                    results.append(result)
            
            # 确保所有差异都有结果
            for diff_data in diff_list:
                diff_id = diff_data.get('diff_id')
                if not any(r['diff_id'] == diff_id for r in results):
                    results.append({
                        'diff_id': diff_id,
                        'risk_level': '中',
                        'compliance': '符合',
                        'review_suggestions': 'AI审查失败，请手动审查',
                        'raw_ai_response': '解析失败'
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"文本解析也失败: {str(e)}")
            return []
    
    async def _call_ai_api(self, prompt: str) -> str:
        """直接调用AI API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "你是合同审查专家，请分析以下合同条款差异并给出风险评估和修改建议。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 2000
        }
        
        # 重试机制
        max_retries = 3
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                # 确保URL格式正确
                url = self.base_url.rstrip('/') + '/chat/completions'
                print(f"[DEBUG] 尝试第 {attempt + 1} 次调用AI API: {url}")
                print(f"[DEBUG] 请求数据大小: {len(str(data))} 字符")
                
                response = await self.client.post(
                    url,
                    headers=headers,
                    json=data
                )
                print(f"[DEBUG] AI API响应状态码: {response.status_code}")
                
                response.raise_for_status()
                
                result = response.json()
                print(f"[DEBUG] AI API返回JSON解析成功")
                return result["choices"][0]["message"]["content"]
            except Exception as e:
                last_exception = e
                print(f"[DEBUG] AI API调用第 {attempt + 1} 次失败: {str(e)}")
                if attempt == max_retries - 1:
                    # 最后一次尝试失败，记录错误并抛出异常
                    error_msg = str(e) if str(e) else f"Unknown error: {type(e).__name__}"
                    logger.error(f"HTTP API调用失败: {error_msg}")
                    logger.error(f"URL: {url}")
                    logger.error(f"Headers: {headers}")
                    logger.error(f"Data: {data}")
                    # 如果是HTTP错误，尝试获取响应内容
                    if hasattr(e, 'response') and e.response:
                        try:
                            logger.error(f"Response status: {e.response.status_code}")
                            logger.error(f"Response content: {e.response.text}")
                        except:
                            pass
                    print(f"[DEBUG] AI API调用最终失败: {error_msg}")
                    raise Exception(f"AI API调用失败: {error_msg}")
                else:
                    # 等待一段时间后重试
                    print(f"[DEBUG] 等待 {2 ** attempt} 秒后重试...")
                    import asyncio
                    await asyncio.sleep(2 ** attempt)  # 指数退避
    
    def _create_default_results(self, diff_list: List[Dict]) -> List[Dict]:
        """创建默认的审查结果"""
        results = []
        for diff_data in diff_list:
            results.append({
                'diff_id': diff_data.get('diff_id', ''),
                'risk_level': '中',
                'compliance': '符合',
                'review_suggestions': 'AI审查服务未正确初始化，请检查配置',
                'raw_ai_response': '服务初始化失败'
            })
        return results

# 创建全局实例
ai_review_service = AIReviewService()
