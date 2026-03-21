import arxiv
from google import genai
import os
from datetime import datetime

def run():
    # 2026年最新のSDKを使用
    api_key = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    print("Searching for papers...")
    search = arxiv.Search(
        query="Neutral Beam Etching OR Atomic Layer Etching",
        max_results=3,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    
    report = f"# 🔬 半導体最新論文レポート ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n\n"
    
    # 検索結果をリスト化
    papers = list(search.results())
    
    if not papers:
        report += "本日の新しい論文は見つかりませんでした。\n"
    else:
        for paper in papers:
            print(f"Analyzing: {paper.title}")
            prompt = f"あなたは半導体技術の専門家です。以下の論文を読み、日本語で3つの箇条書きで解説してください。\n\nTitle: {paper.title}\nAbstract: {paper.summary}"
            
            try:
                # 最新の呼び出し方式
                response = client.models.generate_content(
                    model='gemini-1.5-flash',
                    contents=prompt
                )
                report += f"## {paper.title}\n- **URL**: {paper.entry_id}\n- **AI解析**: \n{response.text}\n\n---\n"
            except Exception as e:
                print(f"Error: {e}")
                report += f"## {paper.title}\n- **URL**: {paper.entry_id}\n- **エラー**: 解析中に問題が発生しました。\n\n---\n"
    
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("Done!")

if __name__ == "__main__":
    run()
