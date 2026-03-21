import arxiv
import google.generativeai as genai
import os
from datetime import datetime

# Geminiの設定
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# モデル名を最新版に固定して指定
model = genai.GenerativeModel('gemini-1.5-flash')

def run():
    print("論文の検索を開始します...")
    search = arxiv.Search(
        query="Neutral Beam Etching OR Atomic Layer Etching",
        max_results=3,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    
    report = f"# 🔬 半導体最新論文レポート ({datetime.now().strftime('%Y-%m-%d')})\n\n"
    
    results = list(search.results())
    if not results:
        print("新しい論文は見つかりませんでした。")
        return

    for paper in results:
        print(f"解析中: {paper.title}")
        prompt = f"あなたは半導体技術の専門家です。以下の論文を読み、技術革新のポイントとビジネスへの影響を日本語で3つの箇条書きで解説してください。\n\nTitle: {paper.title}\nAbstract: {paper.summary}"
        
        try:
            response = model.generate_content(prompt)
            report += f"## {paper.title}\n- **URL**: {paper.entry_id}\n- **AI解析**: \n{response.text}\n\n---\n"
        except Exception as e:
            print(f"解析中にエラーが発生しました: {e}")
            report += f"## {paper.title}\n- **URL**: {paper.entry_id}\n- **エラー**: 解析に失敗しました。\n\n---\n"
    
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("レポートを README.md に保存しました！")

if __name__ == "__main__":
    run()
