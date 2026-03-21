import arxiv
from google import genai
import os
from datetime import datetime

def run():
    api_key = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    # 1. あなたのキーで「今使えるモデル」をリストアップして、動くものを自動選択
    print("Checking available models...")
    available_models = []
    for m in client.models.list():
        # 'generateContent'ができるモデルだけを抽出
        if 'generateContent' in m.supported_variants:
            available_models.append(m.name)
    
    print(f"Available models: {available_models}")
    
    # 優先順位をつけてモデルを選択（flash系は速くて無料枠に強い）
    target_model = 'gemini-1.5-flash' # デフォルト
    for preferred in ['gemini-1.5-flash', 'models/gemini-1.5-flash', 'gemini-2.0-flash']:
        if preferred in available_models:
            target_model = preferred
            break
            
    print(f"Selected model: {target_model}")
    
    # 2. 論文検索
    search = arxiv.Search(
        query='all:"Atomic Layer Etching" OR all:"Neutral Beam Etching"',
        max_results=3,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    
    report = f"# 🔬 半導体最新論文レポート ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n\n"
    report += f"> **使用AIモデル:** `{target_model}`\n\n"
    
    for paper in list(search.results()):
        prompt = f"以下の半導体関連の論文を読み、技術的なポイントを日本語で要約してください。\n\nTitle: {paper.title}\nAbstract: {paper.summary}"
        
        try:
            response = client.models.generate_content(
                model=target_model,
                contents=prompt
            )
            summary = response.text
        except Exception as e:
            summary = f"解析に失敗しました。エラー内容: {str(e)[:100]}"
        
        report += f"## {paper.title}\n- **URL**: {paper.entry_id}\n- **AI解析**: \n{summary}\n\n---\n"
    
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("Success!")

if __name__ == "__main__":
    run()
