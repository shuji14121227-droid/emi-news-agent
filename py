import arxiv
import google.generativeai as genai
import os
from datetime import datetime

# Geminiの設定
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash') # 無料で速いモデル

def run():
    search = arxiv.Search(
        query="Neutral Beam Etching OR Atomic Layer Etching",
        max_results=3,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    
    report = f"# 🔬 半導体最新論文レポート ({datetime.now().strftime('%Y-%m-%d')})\n\n"
    
    for paper in search.results():
        # Geminiに解析を依頼
        prompt = f"あなたは半導体技術の専門家です。以下の論文を読み、技術革新のポイントとビジネスへの影響を日本語で解説してください。\n\nTitle: {paper.title}\nAbstract: {paper.summary}"
        response = model.generate_content(prompt)
        
        report += f"## {paper.title}\n- **URL**: {paper.entry_id}\n- **Geminiの解析**: \n{response.text}\n\n---\n"
    
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(report)

if __name__ == "__main__":
    run()
