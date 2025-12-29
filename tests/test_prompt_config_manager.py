"""
测试prompt配置管理器
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, mock_open
from app.configs.prompt_config_manager import PromptConfigManager


class TestPromptConfigManager:
    """测试PromptConfigManager类"""
    
    def test_initialization_success(self):
        """测试成功初始化配置管理器"""
        # 创建测试配置数据 - 匹配实际实现结构
        mock_configs = {
            'system_prompts.json': {
                'system_prompts': {
                    'PROFILE_ANALYSIS': {'prompt': 'Test profile analysis prompt'},
                    'DEFAULT': {'prompt': 'Default system prompt'}
                }
            },
            'mock_responses.json': {
                'mock_responses': {
                    'PROFILE_ANALYSIS': {'test': 'data'}
                }
            },
            'scene_prompts.json': {
                'scene_prompts': {
                    'conversation_suggestions': {
                        'template': 'Test conversation template'
                    }
                }
            },
            'task_prompts.json': {
                'PROFILE_ANALYSIS': {
                    'prompt_template': 'Task template for {task_name}'
                }
            },
            'stream_configs.json': {
                'PROFILE_ANALYSIS': {
                    'chunk_size': 100,
                    'delay_ms': 50
                }
            }
        }
        
        # 模拟文件读取
        def mock_file_open(filename, *args, **kwargs):
            filename_key = Path(filename).name
            if filename_key in mock_configs:
                return mock_open(read_data=json.dumps(mock_configs[filename_key]))()
            return mock_open(read_data='{}')()
        
        with patch('builtins.open', side_effect=mock_file_open):
            with patch('pathlib.Path.exists', return_value=True):
                manager = PromptConfigManager()
                
                # 验证配置已加载
                assert 'system_prompts' in manager.configs
                assert 'mock_responses' in manager.configs
                assert 'scene_prompts' in manager.configs
                assert 'task_prompts' in manager.configs
                assert 'stream_configs' in manager.configs
    
    def test_get_system_prompt(self):
        """测试获取系统提示词"""
        manager = PromptConfigManager()
        manager.configs['system_prompts'] = {
            'system_prompts': {
                'PROFILE_ANALYSIS': {'prompt': 'Test profile analysis prompt'}
            }
        }
        
        prompt = manager.get_system_prompt('PROFILE_ANALYSIS')
        assert prompt == 'Test profile analysis prompt'
    
    def test_get_system_prompt_default(self):
        """测试获取不存在的系统提示词时返回默认值"""
        manager = PromptConfigManager()
        manager.configs['system_prompts'] = {
            'system_prompts': {
                'DEFAULT': {'prompt': 'Default system prompt'}
            }
        }
        
        prompt = manager.get_system_prompt('NON_EXISTENT')
        assert prompt == 'Default system prompt'
    
    def test_get_mock_response(self):
        """测试获取模拟响应"""
        manager = PromptConfigManager()
        manager.configs['mock_responses'] = {
            'mock_responses': {
                'PROFILE_ANALYSIS': {'test': 'data'}
            }
        }
        
        response = manager.get_mock_response('PROFILE_ANALYSIS')
        assert response == {'test': 'data'}
    
    def test_get_mock_response_default(self):
        """测试获取不存在的模拟响应时返回默认值"""
        manager = PromptConfigManager()
        manager.configs['mock_responses'] = {
            'mock_responses': {
                'DEFAULT': {'default': 'response'}
            }
        }
        
        response = manager.get_mock_response('NON_EXISTENT')
        assert response == {'default': 'response'}
    
    def test_get_scene_prompt(self):
        """测试获取场景提示词"""
        manager = PromptConfigManager()
        manager.configs['scene_prompts'] = {
            'scene_prompts': {
                'conversation_suggestions': {
                    'template': 'Test conversation template'
                }
            }
        }
        
        prompt = manager.get_scene_prompt('conversation_suggestions', 'default')
        assert prompt == 'Test conversation template'
    
    def test_get_task_prompt(self):
        """测试获取任务提示词"""
        manager = PromptConfigManager()
        manager.configs['task_prompts'] = {
            'PROFILE_ANALYSIS': {
                'prompt_template': 'Task template for {name}'
            }
        }
        
        template = manager.get_task_prompt('PROFILE_ANALYSIS', name='profile analysis')
        assert template == 'Task template for profile analysis'
    
    def test_get_stream_config(self):
        """测试获取流式配置"""
        manager = PromptConfigManager()
        manager.configs['stream_configs'] = {
            'PROFILE_ANALYSIS': {
                'chunk_size': 100,
                'delay_ms': 50
            }
        }
        
        config = manager.get_stream_config('PROFILE_ANALYSIS')
        assert config['chunk_size'] == 100
        assert config['delay_ms'] == 50
    
    def test_get_specialized_scene_prompt(self):
        """测试获取专用场景提示词"""
        manager = PromptConfigManager()
        manager.configs['scene_prompts'] = {
            'scene_prompts': {
                'conversation_suggestions': {
                    'components': {
                        'specialized_templates': {
                            'detailed': {
                                'template': 'Detailed conversation template'
                            }
                        }
                    }
                }
            }
        }
        
        prompt = manager.get_specialized_scene_prompt('conversation_suggestions', 'detailed')
        assert prompt == 'Detailed conversation template'
    
    def test_reload_configs(self):
        """测试重新加载配置"""
        manager = PromptConfigManager()
        original_time = manager.load_time
        
        # 模拟重新加载
        with patch('builtins.open', mock_open(read_data='{}')):
            with patch('pathlib.Path.exists', return_value=True):
                manager.reload_configs()
                
                # 验证重新加载时间已更新
                assert manager.load_time != original_time
    
    def test_get_config_info(self):
        """测试获取配置信息"""
        from datetime import datetime
        manager = PromptConfigManager()
        manager.load_time = datetime.now()
        manager.configs = {
            'system_prompts': {'key': 'value'},
            'mock_responses': {'key': 'value'}
        }
        
        info = manager.get_config_info()
        assert 'load_time' in info
        assert info['loaded_configs'] == ['system_prompts', 'mock_responses']
        assert 'system_prompts' in info['config_status']
        assert 'mock_responses' in info['config_status']
    
    def test_missing_config_file(self):
        """测试配置文件缺失时的处理"""
        with patch('pathlib.Path.exists', return_value=False):
            manager = PromptConfigManager()
            
            # 验证空配置已创建
            assert manager.configs['system_prompts'] == {}
            assert manager.configs['mock_responses'] == {}
    
    def test_invalid_json_handling(self):
        """测试无效JSON文件的处理"""
        with patch('builtins.open', mock_open(read_data='invalid json')):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('json.load', side_effect=json.JSONDecodeError('Invalid', '', 0)):
                    manager = PromptConfigManager()
                    
                    # 验证错误处理
                    assert manager.configs['system_prompts'] == {}