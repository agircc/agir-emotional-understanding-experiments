#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
from dotenv import load_dotenv

def main():
    """检查环境配置并提供诊断信息"""
    print("环境检查工具")
    print("=============")
    
    # 检查 Python 版本
    print(f"Python 版本: {sys.version}")
    
    # 检查 OPENAI_API_KEY
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        masked_key = api_key[:5] + "*" * (len(api_key) - 9) + api_key[-4:]
        print(f"OPENAI_API_KEY: {masked_key} (有效)")
    else:
        print("OPENAI_API_KEY: 未设置 (请在 .env 文件中设置)")
    
    # 检查可能影响 OpenAI 客户端的环境变量
    proxy_vars = ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 
                  'OPENAI_PROXY', 'openai_proxy']
    
    found_proxies = False
    print("\n可能影响 OpenAI 客户端的代理设置:")
    for var in proxy_vars:
        if var in os.environ:
            found_proxies = True
            print(f"  - {var}: {os.environ[var]}")
    
    if not found_proxies:
        print("  未发现代理设置")
    
    # 如果发现代理设置，提供建议
    if found_proxies:
        print("\n检测到代理设置可能导致 OpenAI 客户端初始化问题。建议:")
        print("1. 临时解决方案: 在运行代码前清除这些变量")
        print("   例如: unset HTTP_PROXY HTTPS_PROXY")
        print("2. 在代码中显式处理代理设置 (已在 main.py 中实现)")
    
    print("\n依赖检查:")
    try:
        import openai
        print(f"  openai 版本: {openai.__version__}")
    except ImportError:
        print("  openai 库未安装")
    
    try:
        import tqdm
        print(f"  tqdm 版本: {tqdm.__version__}")
    except ImportError:
        print("  tqdm 库未安装")

if __name__ == "__main__":
    main() 