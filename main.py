import arxiv
from google import genai
import os
from datetime import datetime

def run():
    api_key = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    # 論文の検索（クエリを絞る）
    search = arxiv.Search(
        query='all:"Atomic Layer Etching" OR all:"Neutral Beam Etching"',
        max_results=3,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    
    report = f"# 🔬 半導体最新論文レポート ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n\n"
    
    # Google APIが受け付ける可能性のある「名前」のリスト
    # 2026年時点で最も安定している順に並べています
    model_names = ['gemini-1.5-flash', 'gemini-1.5-flash-latest', 'gemini-2.0-flash']
    
    papers = list(search.results())
    
    for paper in papers:
        prompt = f"以下の論文を読み、技術革新のポイントを日本語で要約してください。\n\nTitle: {paper.title}\nAbstract: {paper.summary}"
        summary_text = ""
        
        # 成功するまでモデル名を切り替えて試行
        for m_name in model_names:
            try:
                response = client.models.generate_content(
                    model=m_name,
                    contents=prompt
                )
                summary_text = response.text
                break # 成功したらループを抜ける
            except Exception as e:
                print(f"Model {m_name} failed: {e}")
                summary_text = f"解析エラー（{m_name}）"
        
        report += f"## {paper.title}\n- **URL**: {paper.entry_id}\n- **AI解析**: \n{summary_text}\n\n---\n"
    
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("Update finished.")

if __name__ == "__main__":
    run()
