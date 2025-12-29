"""
Prompt配置管理器
负责加载和管理所有的prompt配置文件
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class PromptConfigManager:
    """Prompt配置管理器"""
    
    def __init__(self, config_dir: str = None):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录路径，默认为当前文件所在目录
        """
        if config_dir is None:
            # 默认使用相对于当前文件的目录结构
            current_dir = Path(__file__).parent
            self.config_dir = current_dir / "prompts"
        else:
            self.config_dir = Path(config_dir)
        
        self.configs = {}
        self.load_time = None
        self._load_all_configs()
    
    def _load_all_configs(self):
        """加载所有配置文件"""
        try:
            config_files = {
                'system_prompts': 'system_prompts.json',
                'mock_responses': 'mock_responses.json', 
                'scene_prompts': 'scene_prompts.json',
                'task_prompts': 'task_prompts.json',
                'stream_configs': 'stream_configs.json'
            }
            
            for config_name, filename in config_files.items():
                config_path = self.config_dir / filename
                if config_path.exists():
                    with open(config_path, 'r', encoding='utf-8') as f:
                        self.configs[config_name] = json.load(f)
                    logger.info(f"成功加载配置文件: {filename}")
                else:
                    logger.warning(f"配置文件不存在: {config_path}")
                    self.configs[config_name] = {}
            
            self.load_time = datetime.now()
            logger.info("所有prompt配置文件加载完成")
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
            # 确保至少有空配置可用
            for config_name in config_files.keys():
                if config_name not in self.configs:
                    self.configs[config_name] = {}
    
    def get_system_prompt(self, task_type: str) -> str:
        """
        获取系统提示词
        
        Args:
            task_type: 任务类型
            
        Returns:
            系统提示词，如果找不到则返回默认提示词
        """
        try:
            system_prompts = self.configs.get('system_prompts', {})
            task_key = task_type.upper()
            
            if task_key in system_prompts.get('system_prompts', {}):
                return system_prompts['system_prompts'][task_key]['prompt']
            else:
                # 返回默认提示词
                default_prompt = system_prompts.get('system_prompts', {}).get('DEFAULT', {})
                return default_prompt.get('prompt', '你是一个智能助手，请帮助用户解决问题。')
                
        except Exception as e:
            logger.error(f"获取系统提示词失败: {str(e)}")
            return "你是一个智能助手，请帮助用户解决问题。"
    
    def get_mock_response(self, task_type: str) -> Dict[str, Any]:
        """
        获取模拟响应数据
        
        Args:
            task_type: 任务类型
            
        Returns:
            模拟响应数据
        """
        try:
            mock_responses = self.configs.get('mock_responses', {})
            task_key = task_type.upper()
            
            if task_key in mock_responses.get('mock_responses', {}):
                return mock_responses['mock_responses'][task_key]
            else:
                # 返回默认模拟响应
                default_response = mock_responses.get('mock_responses', {}).get('DEFAULT', {})
                return default_response or {"response": "这是模拟的默认响应内容", "confidence": 0.8}
                
        except Exception as e:
            logger.error(f"获取模拟响应失败: {str(e)}")
            return {"response": "这是模拟的默认响应内容", "confidence": 0.8}
    
    def get_scene_prompt(self, scene_key: str, prompt_type: str = "base", **kwargs) -> str:
        """
        获取场景提示词
        
        Args:
            scene_key: 场景键名
            prompt_type: 提示词类型 (base, stream, non_stream)
            **kwargs: 模板变量
            
        Returns:
            场景提示词
        """
        try:
            scene_prompts = self.configs.get('scene_prompts', {})
            scene_config = scene_prompts.get('scene_prompts', {}).get(scene_key, {})
            
            if not scene_config:
                logger.warning(f"未找到场景配置: {scene_key}")
                return ""
            
            # 获取基础模板
            if prompt_type == "stream":
                template = scene_config.get('templates', {}).get('stream', {}).get('template', '')
            elif prompt_type == "non_stream":
                template = scene_config.get('templates', {}).get('non_stream', {}).get('template', '')
            else:
                template = scene_config.get('template', '')
            
            # 替换模板变量
            if template and kwargs:
                template = template.format(**kwargs)
            
            return template
            
        except Exception as e:
            logger.error(f"获取场景提示词失败: {str(e)}")
            return ""
    
    def get_scene_component(self, scene_key: str, component_type: str, **kwargs) -> str:
        """
        获取场景组件提示词
        
        Args:
            scene_key: 场景键名
            component_type: 组件类型 (base_info, card_info等)
            **kwargs: 模板变量
            
        Returns:
            组件提示词
        """
        try:
            scene_prompts = self.configs.get('scene_prompts', {})
            components = scene_prompts.get('scene_prompts', {}).get(scene_key, {}).get('components', {})
            
            component_config = components.get(component_type, {})
            template = component_config.get('template', '')
            
            # 替换模板变量
            if template and kwargs:
                template = template.format(**kwargs)
            
            return template
            
        except Exception as e:
            logger.error(f"获取场景组件失败: {str(e)}")
            return ""
    
    def get_task_prompt(self, task_name: str, **kwargs) -> str:
        """
        获取任务专用提示词
        
        Args:
            task_name: 任务名称
            **kwargs: 模板变量
            
        Returns:
            任务提示词
        """
        try:
            task_prompts = self.configs.get('task_prompts', {})
            task_config = task_prompts.get(task_name, {})
            
            template = task_config.get('prompt_template', '')
            
            # 替换模板变量
            if template and kwargs:
                template = template.format(**kwargs)
            
            return template
            
        except Exception as e:
            logger.error(f"获取任务提示词失败: {str(e)}")
            return ""
    
    def get_stream_config(self, config_key: str) -> Dict[str, Any]:
        """
        获取流式配置
        
        Args:
            config_key: 配置键名
            
        Returns:
            流式配置
        """
        try:
            stream_configs = self.configs.get('stream_configs', {})
            return stream_configs.get(config_key, {})
            
        except Exception as e:
            logger.error(f"获取流式配置失败: {str(e)}")
            return {}
    
    def get_specialized_scene_prompt(self, scene_key: str, specialized_type: str, **kwargs) -> str:
        """
        获取专用场景提示词
        
        Args:
            scene_key: 场景键名
            specialized_type: 专用类型
            **kwargs: 模板变量
            
        Returns:
            专用场景提示词
        """
        try:
            scene_prompts = self.configs.get('scene_prompts', {})
            specialized = scene_prompts.get('scene_prompts', {}).get(scene_key, {}).get('components', {}).get('specialized_templates', {})
            
            template_config = specialized.get(specialized_type, {})
            template = template_config.get('template', '')
            
            # 替换模板变量
            if template and kwargs:
                template = template.format(**kwargs)
            
            return template
            
        except Exception as e:
            logger.error(f"获取专用场景提示词失败: {str(e)}")
            return ""
    
    def reload_configs(self):
        """重新加载所有配置文件"""
        logger.info("重新加载prompt配置文件")
        self._load_all_configs()
    
    def get_config_info(self) -> Dict[str, Any]:
        """
        获取配置信息
        
        Returns:
            配置信息摘要
        """
        return {
            "config_dir": str(self.config_dir),
            "load_time": self.load_time.isoformat() if self.load_time else None,
            "loaded_configs": list(self.configs.keys()),
            "config_status": {
                name: "loaded" if config else "empty" 
                for name, config in self.configs.items()
            }
        }


# 全局配置管理器实例
prompt_config_manager = PromptConfigManager()