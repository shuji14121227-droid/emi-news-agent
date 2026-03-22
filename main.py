import arxiv
from google import genai
import os
from datetime import datetime

def run():
    api_key = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    # 1. 履歴ファイルの読み込み（過去に読んだ論文を思い出す）
    history_file = "history.txt"
    if os.path.exists(history_file):
        with open(history_file, "r") as f:
            processed_ids = set(f.read().splitlines())
    else:
        processed_ids = set()

    # 2. 論文検索（最新5件を取得）
    search = arxiv.Search(
        query='all:"Atomic Layer Etching" OR all:"Neutral Beam Etching"',
        max_results=5,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    
    new_papers = []
    
    # 3. 新しい論文の抽出とAI要約
    for paper in list(search.results()):
        # すでに履歴（processed_ids）にあるURLならスキップ
        if paper.entry_id in processed_ids:
            print(f"スキップ (要約済み): {paper.title}")
            continue
            
        print(f"新規論文を発見: {paper.title}")
        prompt = f"以下の半導体論文を日本語で専門的に要約して：\n\nTitle: {paper.title}\nAbstract: {paper.summary}"
        summary = ""
        error_msg = ""
        
        # 2026年最新モデルで要約に挑戦
        for model_name in ['gemini-3.0-flash', 'gemini-2.5-flash', 'gemini-3.1-flash']:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                if response.text:
                    summary = response.text
                    break
            except Exception as e:
                error_msg += f"({model_name}失敗: {e}) "
                
        if not summary:
            summary = f"⚠️要約できませんでした。原因👉 {error_msg}"
        
        # 新しい論文リストと、履歴リストの両方に追加
        new_papers.append({
            "title": paper.title,
            "url": paper.entry_id,
            "summary": summary
        })
        processed_ids.add(paper.entry_id)

    # 4. レポートの更新（新しい論文がある時のみ実行）
    if not new_papers:
        print("今日は新しい論文がありませんでした。")
        return

    report = f"# 🔬 半導体最新論文レポート ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n\n"
    for p in new_papers:
        report += f"## {p['title']}\n- **URL**: {p['url']}\n- **AI解析**: \n{p['summary']}\n\n---\n"
    
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(report)

    # 5. 新しい履歴を保存
    with open(history_file, "w") as f:
        f.write("\n".join(processed_ids))
        
    print("🎉 レポートと履歴の更新が完了しました！")

if __name__ == "__main__":
    run()
