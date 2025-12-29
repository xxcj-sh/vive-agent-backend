"""
测试prompt配置管理器 - 实际配置测试
"""

import pytest
from app.configs.prompt_config_manager import PromptConfigManager


class TestPromptConfigManagerReal:
    """使用真实配置文件测试PromptConfigManager类"""
    
    def test_initialization_with_real_configs(self):
        """测试使用真实配置文件初始化"""
        manager = PromptConfigManager()
        
        # 验证配置已加载
        assert 'system_prompts' in manager.configs
        assert 'mock_responses' in manager.configs
        assert 'scene_prompts' in manager.configs
        assert 'task_prompts' in manager.configs
        assert 'stream_configs' in manager.configs
        
        # 验证配置不为空
        assert len(manager.configs['system_prompts']) > 0
        assert len(manager.configs['mock_responses']) > 0
        assert len(manager.configs['scene_prompts']) > 0
        assert len(manager.configs['task_prompts']) > 0
        assert len(manager.configs['stream_configs']) > 0
    
    def test_get_system_prompt_real(self):
        """测试获取真实的系统提示词"""
        manager = PromptConfigManager()
        
        # 测试获取PROFILE_ANALYSIS系统提示词
        prompt = manager.get_system_prompt('PROFILE_ANALYSIS')
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        # 检查是否包含关键词
        assert ('用户资料分析' in prompt or 
                '画像分析' in prompt or 
                'profile' in prompt.lower() or
                '用户画像' in prompt)
        
        # 测试获取DEFAULT系统提示词
        default_prompt = manager.get_system_prompt('DEFAULT')
        assert isinstance(default_prompt, str)
        assert len(default_prompt) > 0
    
    def test_get_mock_response_real(self):
        """测试获取真实的模拟响应"""
        manager = PromptConfigManager()
        
        # 测试获取PROFILE_ANALYSIS模拟响应
        response = manager.get_mock_response('PROFILE_ANALYSIS')
        assert isinstance(response, dict)
        assert len(response) > 0
        
        # 测试获取DEFAULT模拟响应
        default_response = manager.get_mock_response('DEFAULT')
        assert isinstance(default_response, dict)
        assert len(default_response) > 0
    
    def test_get_scene_prompt_real(self):
        """测试获取真实的场景提示词"""
        manager = PromptConfigManager()
        
        # 测试获取对话建议场景提示词
        prompt = manager.get_scene_prompt('conversation_suggestions', 'default')
        assert isinstance(prompt, str)
        # 可以为空，因为配置中可能没有默认模板
    
    def test_get_task_prompt_real(self):
        """测试获取真实的任务提示词"""
        manager = PromptConfigManager()
        
        # 测试获取PROFILE_ANALYSIS任务提示词
        prompt = manager.get_task_prompt('PROFILE_ANALYSIS')
        assert isinstance(prompt, str)
        # 可以为空，因为配置中可能没有任务模板
    
    def test_get_stream_config_real(self):
        """测试获取真实的流式配置"""
        manager = PromptConfigManager()
        
        # 测试获取PROFILE_ANALYSIS流式配置
        config = manager.get_stream_config('PROFILE_ANALYSIS')
        assert isinstance(config, dict)
        # 流式配置可能为空，如果不存在的话
        if config:  # 如果配置存在
            assert 'chunk_size' in config
            assert 'delay_ms' in config
            assert isinstance(config['chunk_size'], int)
            assert isinstance(config['delay_ms'], int)
    
    def test_get_specialized_scene_prompt_real(self):
        """测试获取真实的专用场景提示词"""
        manager = PromptConfigManager()
        
        # 测试获取对话建议的详细模板
        prompt = manager.get_specialized_scene_prompt('conversation_suggestions', 'detailed')
        assert isinstance(prompt, str)
        # 可以为空，因为配置中可能没有详细模板
    
    def test_get_config_info_real(self):
        """测试获取配置信息"""
        manager = PromptConfigManager()
        
        info = manager.get_config_info()
        assert isinstance(info, dict)
        assert 'load_time' in info
        assert 'config_dir' in info
        assert 'config_status' in info
        assert 'loaded_configs' in info
        assert isinstance(info['load_time'], str)
        assert isinstance(info['config_dir'], str)
        assert isinstance(info['config_status'], dict)
        assert isinstance(info['loaded_configs'], list)
        assert len(info['loaded_configs']) > 0
    
    def test_reload_configs_real(self):
        """测试重新加载配置"""
        import time
        manager = PromptConfigManager()
        original_time = manager.load_time
        
        # 等待一小段时间确保时间戳会改变
        time.sleep(0.01)
        
        # 重新加载配置
        manager.reload_configs()
        
        # 验证重新加载时间已更新
        assert manager.load_time != original_time
    
    def test_all_task_types_covered(self):
        """测试所有任务类型都有对应的配置"""
        from app.models.llm_usage_log import LLMTaskType
        manager = PromptConfigManager()
        
        # 检查所有枚举值
        for task_type in LLMTaskType:
            # 系统提示词
            system_prompt = manager.get_system_prompt(task_type.name)
            assert isinstance(system_prompt, str)
            
            # 模拟响应
            mock_response = manager.get_mock_response(task_type.name)
            assert isinstance(mock_response, dict)
            
            # 流式配置
            stream_config = manager.get_stream_config(task_type.name)
            assert isinstance(stream_config, dict)
            
            # 任务提示词
            task_prompt = manager.get_task_prompt(task_type.name)
            assert isinstance(task_prompt, str)
    
    def test_error_handling(self):
        """测试错误处理"""
        manager = PromptConfigManager()
        
        # 测试不存在的任务类型
        non_existent_prompt = manager.get_system_prompt('NON_EXISTENT_TASK')
        assert isinstance(non_existent_prompt, str)
        assert len(non_existent_prompt) > 0  # 应该返回DEFAULT提示词
        
        # 测试不存在的场景
        non_existent_scene = manager.get_scene_prompt('non_existent_scene', 'default')
        assert isinstance(non_existent_scene, str)
        
        # 测试不存在的流式配置
        non_existent_stream = manager.get_stream_config('NON_EXISTENT_TASK')
        assert isinstance(non_existent_stream, dict)
        # 流式配置可能为空，如果不存在的话
        if non_existent_stream:  # 如果配置存在
            assert 'chunk_size' in non_existent_stream
            assert 'delay_ms' in non_existent_stream