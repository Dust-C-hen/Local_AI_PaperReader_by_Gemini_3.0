import time
import glob
from typing import List, Union
import google.generativeai as genai
import os

# --- 配置区域 ---

# 设置代理（必须加！否则 Python 无法连接 Google）
# 注意：把 7890 改成你 VPN 软件实际的端口号
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

# 建议将 API KEY 放在环境变量中，或者直接在此处填入
API_KEY = "AIza..." # 替换为你的 "AIza..."

# 你的本地论文归纳/整理文件夹路径
KB_FOLDER = "./my_knowledge_base"     

# 注意，这里的模型名需要填model_test.py输出的模型。
MODEL_NAME = "gemini-2.5-flash"         # Pro 模型推理能力更强，适合深度分析

# 配置 Gemini
genai.configure(api_key=API_KEY)

class LocalResearcher:
    def __init__(self, kb_folder):
        self.kb_folder = kb_folder
        self.kb_context = [] # 存储文本内容的列表
        self.kb_files = []   # 存储需要上传的 PDF 文件对象
        
    def _wait_for_files_active(self, files):
        """等待上传的文件状态变为 ACTIVE"""
        print("正在等待文件处理...", end="")
        for name in (f.name for f in files):
            file = genai.get_file(name)
            while file.state.name == "PROCESSING":
                print(".", end="", flush=True)
                time.sleep(2)
                file = genai.get_file(name)
            if file.state.name != "ACTIVE":
                raise Exception(f"文件 {file.name} 处理失败。")
        print(" 就绪！")

    def load_knowledge_base(self):
        """加载本地知识库（支持 txt/md 读取和 pdf 上传）"""
        print(f"正在加载知识库：{self.kb_folder} ...")
        
        # 1. 处理文本类笔记 (txt, md) - 直接读取内容以节省文件上传配额
        text_extensions = ['*.md', '*.txt']
        for ext in text_extensions:
            for file_path in glob.glob(os.path.join(self.kb_folder, ext)):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    filename = os.path.basename(file_path)
                    # 包装成易于模型理解的格式
                    self.kb_context.append(f"--- 参考资料: {filename} ---\n{content}\n")
        
        # 2. 处理 PDF 原文 - 使用 File API 上传
        pdf_files = glob.glob(os.path.join(self.kb_folder, '*.pdf'))
        if pdf_files:
            print(f"检测到 {len(pdf_files)} 个 PDF 文件，正在上传至 Gemini...")
            for pdf_path in pdf_files:
                uploaded_file = genai.upload_file(pdf_path)
                self.kb_files.append(uploaded_file)
            
            # 等待 PDF 处理完成
            self._wait_for_files_active(self.kb_files)

        print(f"知识库加载完毕。包含 {len(self.kb_context)} 篇文本笔记和 {len(self.kb_files)} 个 PDF 文件。")

    def analyze_new_paper(self, new_paper_path):
        """分析新导入的论文"""
        print(f"正在处理新论文：{new_paper_path} ...")
        
        # 上传新论文
        target_file = genai.upload_file(new_paper_path)
        self._wait_for_files_active([target_file])

        # 构建 Prompt
        # 注意：这里我们将知识库作为上下文背景
        model = genai.GenerativeModel(MODEL_NAME)
        
        prompt = """
        你是一位专业的学术研究助手。请基于我提供的【本地知识库】（包含我之前的论文归纳和整理），
        对这篇【新导入的论文】进行深度分析。

        请严格按照以下结构输出分析报告：

        1. **核心内容摘要**：用简练的语言概括新论文解决的问题、方法和结论。
        2. **与知识库的关联性分析**：
           - 这篇新论文与我的知识库中哪些具体的文章或概念有联系？（请明确引用知识库中的文件名或概念）
           - 它是否支持、反驳或扩展了我之前的某些记录？
        3. **创新点与差异**：
           - 相较于我已有的知识储备，这篇论文最大的创新点是什么？
           - 它使用了什么我之前未曾记录过的新方法或新视角？
        4. **研究启示**：
           - 基于我的知识库背景，这篇论文对我的研究方向有什么潜在的启发？

        如果新论文的内容与我的知识库完全无关，请直接指出。
        """

        # 组合输入：Prompt + 文本知识库 + PDF知识库 + 新论文
        # 注意顺序：先给背景，再给目标
        request_content = [prompt] 
        # 添加文本知识
        if self.kb_context:
            request_content.append("以下是我的【本地知识库】文本归纳：\n" + "\n".join(self.kb_context))
        # 添加 PDF 知识
        if self.kb_files:
            request_content.extend(self.kb_files)
        
        request_content.append("以下是【新导入的论文】：")
        request_content.append(target_file)

        print("正在进行 AI 分析（这可能需要几十秒）...")
        response = model.generate_content(request_content)
        
        return response.text

# --- 运行脚本 ---
if __name__ == "__main__":
    # 实例化并加载知识库
    researcher = LocalResearcher(KB_FOLDER)
    researcher.load_knowledge_base()
    
    # 指定新论文路径
    new_paper = "new_paper_to_analyze.pdf" # 替换为你要分析的新文件路径
    
    if os.path.exists(new_paper):
        result = researcher.analyze_new_paper(new_paper)
        print("\n" + "="*30 + " 分析报告 " + "="*30 + "\n")
        print(result)
    else:
        print(f"找不到文件：{new_paper}")