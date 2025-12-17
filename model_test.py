import google.generativeai as genai
import os

# ================= 1. 这里填你的代理 =================
# 确保端口号（比如 7890）和你 VPN 软件里的一致
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

# ================= 2. 这里填你的真实 Key =================
# 必须把 AIza... 这一长串换成你之前申请到的那个！
API_KEY = "AIza...."

genai.configure(api_key=API_KEY)

print("\n====== 开始查询可用模型 ======")
try:
    for m in genai.list_models():
        # 打印出所有支持文本生成的模型
        if 'generateContent' in m.supported_generation_methods:
            print(f"发现模型: {m.name}")
    print("====== 查询结束 ======\n")
except Exception as e:
    print(f"发生错误: {e}")