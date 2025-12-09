"""
测试Google Gemini API连接

运行:
    PYTHONPATH=/Users/wangkunyu/develop/TradingAgents:$PYTHONPATH python3 tests/test_gemini_connection.py
"""
import os
import sys

def test_api_key():
    """测试API key是否设置"""
    print("\n" + "="*80)
    print("步骤1: 检查API Key")
    print("="*80)
    
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        print("❌ 错误: GOOGLE_API_KEY 环境变量未设置")
        print("\n请按照以下步骤设置:")
        print("1. 访问 https://aistudio.google.com/")
        print("2. 点击 'Get API key' 创建API key")
        print("3. 运行: export GOOGLE_API_KEY='your_api_key'")
        return False
    
    print(f"✅ API Key已设置: {api_key[:20]}...")
    return True


def test_gemini_import():
    """测试Gemini库是否安装"""
    print("\n" + "="*80)
    print("步骤2: 检查依赖库")
    print("="*80)
    
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        print("✅ langchain-google-genai 已安装")
        return True
    except ImportError as e:
        print(f"❌ 错误: {e}")
        print("\n请运行: pip3 install langchain-google-genai")
        return False


def test_simple_call():
    """测试简单的API调用"""
    print("\n" + "="*80)
    print("步骤3: 测试API调用")
    print("="*80)
    
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        # 创建LLM实例
        print("正在创建Gemini实例...")
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            temperature=0
        )
        
        # 测试调用
        print("正在发送测试请求...")
        response = llm.invoke("Say 'Hello from Gemini!' in one sentence.")
        
        print(f"\n✅ API调用成功!")
        print(f"响应: {response.content}")
        return True
        
    except Exception as e:
        print(f"\n❌ API调用失败: {str(e)}")
        if "API_KEY" in str(e).upper():
            print("\n提示: 请检查API key是否正确")
        return False


def test_gemini_config():
    """测试项目配置"""
    print("\n" + "="*80)
    print("步骤4: 测试项目配置")
    print("="*80)
    
    try:
        from gemini_config import GEMINI_CONFIG
        print("✅ gemini_config.py 配置加载成功")
        print(f"   LLM Provider: {GEMINI_CONFIG['llm_provider']}")
        print(f"   Quick Model: {GEMINI_CONFIG['quick_think_llm']}")
        print(f"   Deep Model: {GEMINI_CONFIG['deep_think_llm']}")
        return True
    except Exception as e:
        print(f"❌ 配置加载失败: {str(e)}")
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*80)
    print("Google Gemini API 连接测试")
    print("="*80)
    
    results = []
    
    # 运行测试
    results.append(("API Key检查", test_api_key()))
    results.append(("依赖库检查", test_gemini_import()))
    results.append(("API调用测试", test_simple_call()))
    results.append(("项目配置测试", test_gemini_config()))
    
    # 打印总结
    print("\n" + "="*80)
    print("测试总结")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        emoji = "✅" if result else "❌"
        status = "通过" if result else "失败"
        print(f"{emoji} {name}: {status}")
    
    print("\n" + "="*80)
    print(f"结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过! Gemini API配置成功!")
        print("\n下一步:")
        print("  运行 DeFi 分析测试:")
        print("  PYTHONPATH=$PWD:$PYTHONPATH python3 examples/test_defi_with_gemini.py")
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查上述错误")
    
    print("="*80 + "\n")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
