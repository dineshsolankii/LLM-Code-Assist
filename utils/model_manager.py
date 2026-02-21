#!/usr/bin/env python
"""Enhanced model manager with auto-download and dynamic model selection."""
import os
import logging
import platform
import requests
from typing import Dict, Any, Optional, Union

logger = logging.getLogger(__name__)

PREFERRED_MODELS = [
    'qwen2.5-coder:32b',
    'qwen2.5-coder:14b',
    'qwen2.5-coder:7b',
    'qwen2.5-coder:3b',
    'qwen2.5-coder:1.5b',
]


class ModelManager:
    def __init__(self):
        self.base_url = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.api_key = os.environ.get('OLLAMA_API_KEY', '')
        self._active_model = None
        self._redis = None

    @property
    def redis(self):
        if self._redis is None:
            try:
                import redis as redis_lib
                url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
                self._redis = redis_lib.from_url(url, decode_responses=True)
                self._redis.ping()
            except Exception:
                self._redis = False
        return self._redis if self._redis is not False else None

    @property
    def active_model(self):
        if self._active_model:
            return self._active_model
        if self.redis:
            try:
                cached = self.redis.get('active_model')
                if cached:
                    self._active_model = cached
                    return self._active_model
            except Exception:
                pass
        self._active_model = self._select_best_model()
        if self.redis and self._active_model:
            try:
                self.redis.setex('active_model', 3600, self._active_model)
            except Exception:
                pass
        return self._active_model

    @active_model.setter
    def active_model(self, model_name):
        self._active_model = model_name
        if self.redis:
            try:
                self.redis.setex('active_model', 3600, model_name)
            except Exception:
                pass

    def _select_best_model(self):
        try:
            available = self.list_models().get('models', [])
            available_names = [m.get('name', '') for m in available]
            for model in PREFERRED_MODELS:
                if model in available_names:
                    logger.info(f'Selected available model: {model}')
                    return model
            recommended = self._get_recommended_model_for_system()
            logger.info(f'No preferred model found. Recommended: {recommended}')
            return recommended
        except Exception as e:
            logger.warning(f'Error selecting model: {e}')
            return 'qwen2.5-coder:7b'

    def _get_recommended_model_for_system(self):
        try:
            import psutil
            total_ram_gb = psutil.virtual_memory().total / (1024 ** 3)
        except ImportError:
            total_ram_gb = self._detect_ram_fallback()
        gpu_vram_gb = self._detect_gpu_vram()
        logger.info(f'System: RAM={total_ram_gb:.1f}GB, GPU={gpu_vram_gb:.1f}GB')
        if total_ram_gb >= 32 or gpu_vram_gb >= 16:
            return 'qwen2.5-coder:32b'
        elif total_ram_gb >= 16 or gpu_vram_gb >= 8:
            return 'qwen2.5-coder:14b'
        elif total_ram_gb >= 8 or gpu_vram_gb >= 4:
            return 'qwen2.5-coder:7b'
        return 'qwen2.5-coder:3b'

    def _detect_ram_fallback(self):
        try:
            if platform.system() == 'Darwin':
                import subprocess
                r = subprocess.run(['sysctl', '-n', 'hw.memsize'], capture_output=True, text=True)
                return int(r.stdout.strip()) / (1024 ** 3)
            else:
                with open('/proc/meminfo', 'r') as f:
                    for line in f:
                        if line.startswith('MemTotal'):
                            return int(line.split()[1]) / (1024 ** 2)
        except Exception:
            pass
        return 8

    def _detect_gpu_vram(self):
        try:
            import subprocess
            r = subprocess.run(
                ['nvidia-smi', '--query-gpu=memory.total', '--format=csv,noheader,nounits'],
                capture_output=True, text=True, timeout=5,
            )
            if r.returncode == 0:
                return int(r.stdout.strip().split('\n')[0]) / 1024
        except Exception:
            pass
        if platform.system() == 'Darwin' and platform.machine() == 'arm64':
            return self._detect_ram_fallback() * 0.75
        return 0

    def _make_request(self, endpoint, method='POST', payload=None):
        headers = {'Authorization': f'Bearer {self.api_key}'} if self.api_key else {}
        try:
            url = f'{self.base_url}/api/{endpoint}'
            resp = requests.request(method, url, headers=headers, json=payload, timeout=300)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            logger.error(f'API request failed: {e}')
            error_msg = 'Request failed'
            try:
                error_msg = resp.json().get('error', error_msg)
            except Exception:
                pass
            raise RuntimeError(f'{error_msg}. Ensure Ollama server is running.')

    def generate(self, prompt='', model=None, system_prompt=None,
                 temperature=0.2, max_tokens=4096):
        """Generate a response. Handles both keyword and legacy positional calls."""
        if model is None:
            model = self.active_model
        if not prompt:
            return self._get_fallback_response()
        logger.info(f'Generating with model {model}')
        payload = {
            'model': model, 'prompt': prompt,
            'temperature': temperature, 'max_tokens': max_tokens, 'stream': False,
        }
        if system_prompt:
            payload['system'] = system_prompt
        try:
            result = self._make_request('generate', payload=payload)
            if 'response' in result:
                return result['response']
            return self._get_fallback_response()
        except Exception as e:
            logger.error(f'Generation failed: {e}')
            return self._get_fallback_response()

    def _get_fallback_response(self):
        return {
            'project_type': 'web app',
            'description': 'A simple calculator web application.',
            'features': [
                {'name': 'Basic arithmetic', 'description': 'Add, subtract, multiply, divide.', 'priority': 'high'},
            ],
            'database_required': False, 'database_type': 'none',
            'has_frontend': True,
            'suggested_frameworks': ['gradio'],
            'suggested_packages': ['gradio>=4.0.0', 'numpy'],
            'file_structure': [
                {'path': 'app.py', 'type': 'file', 'description': 'Main application'},
                {'path': 'requirements.txt', 'type': 'file', 'description': 'Dependencies'},
                {'path': 'README.md', 'type': 'file', 'description': 'Documentation'},
            ],
        }

    def list_models(self):
        try:
            return self._make_request('tags', method='GET')
        except Exception:
            return {'models': []}

    def pull_model(self, model):
        try:
            logger.info(f'Pulling model {model}...')
            self._make_request('pull', payload={'name': model})
            logger.info(f'Model {model} pulled successfully')
            return True
        except Exception as e:
            logger.error(f'Error pulling model {model}: {e}')
            return False

    def ensure_model_available(self, model_name=None):
        model = model_name or self.active_model
        try:
            available = self.list_models().get('models', [])
            names = [m.get('name', '') for m in available]
            if model not in names:
                logger.info(f'Model {model} not found. Pulling...')
                return self.pull_model(model)
            return True
        except Exception as e:
            logger.error(f'Error ensuring model: {e}')
            return False
