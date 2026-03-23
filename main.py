import arxiv
from google import genai
import os
from datetime import datetime
import html
import re
from pathlib import Path


DATE_DIR_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def get_archive_dates(archive_dir: Path) -> list[str]:
    if not archive_dir.exists():
        return []
    dates: list[str] = []
    for child in archive_dir.iterdir():
        if child.is_dir() and DATE_DIR_RE.match(child.name):
            dates.append(child.name)
    dates.sort(reverse=True)
    return dates


def build_card_html(p: dict) -> str:
    title = html.escape(str(p["title"]))
    url_raw = str(p["url"])
    url = html.escape(url_raw, quote=True)
    summary = html.escape(str(p["summary"]))

    # URL文字列も画面に表示しつつ、クリックでも飛べるようにしてます。
    return f"""<article class="card">
  <h2 class="card__title">{title}</h2>
  <div class="card__meta">
    <a class="card__link" href="{url}" target="_blank" rel="noopener noreferrer">arXivを開く</a>
    <p class="card__url">
      <span class="card__url-label">URL</span>:
      <a class="card__url-link" href="{url}" target="_blank" rel="noopener noreferrer">{html.escape(url_raw)}</a>
    </p>
  </div>
  <details class="card__details" open>
    <summary class="card__details-summary">AI解析（要約）</summary>
    <div class="card__summary">{summary}</div>
  </details>
</article>"""


def build_archive_page_html(papers: list[dict], date_str: str, generated_at: str, css_href: str) -> str:
    if papers:
        cards_html = "\n".join(build_card_html(p) for p in papers)
        cards_section = f"""<section class="grid" aria-label="論文一覧">
  {cards_html}
</section>"""
    else:
        cards_section = """<section class="empty">
  <h2 class="empty__title">この日は新しい論文がありませんでした</h2>
  <p class="empty__text">次回の更新をお待ちください。</p>
</section>"""

    return f"""<!doctype html>
<html lang="ja">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>半導体最新論文 - {html.escape(date_str)}</title>
    <link rel="stylesheet" href="{css_href}" />
  </head>
  <body>
    <header class="site-header">
      <div class="container">
        <a class="back-link" href="../index.html">← トップへ</a>
        <h1 class="title">🔬 {html.escape(date_str)} の半導体最新論文</h1>
        <p class="subtitle">生成日時: {html.escape(generated_at)} / 新規: {len(papers)}件</p>
      </div>
    </header>

    <main class="container">
      {cards_section}
    </main>

    <footer class="site-footer">
      <div class="container">
        <small>emi-news-agent</small>
      </div>
    </footer>
  </body>
</html>"""


def build_root_index_html(
    today_papers: list[dict],
    generated_at: str,
    archive_dates: list[str],
) -> str:
    if today_papers:
        cards_html = "\n".join(build_card_html(p) for p in today_papers)
        today_section = f"""<section class="grid" aria-label="今日の論文一覧">
  {cards_html}
</section>"""
    else:
        today_section = """<section class="empty">
  <h2 class="empty__title">今日は新しい論文がありませんでした</h2>
  <p class="empty__text">過去の日付から確認できます。</p>
</section>"""

    if archive_dates:
        archive_items = "\n".join(
            f"""<a class="archive-item" href="archive/{d}/index.html">{d}</a>"""
            for d in archive_dates
        )
    else:
        archive_items = """<p class="empty__text">アーカイブはまだありません。</p>"""

    return f"""<!doctype html>
<html lang="ja">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>半導体最新論文レポート</title>
    <link rel="stylesheet" href="styles.css" />
  </head>
  <body>
    <header class="site-header">
      <div class="container">
        <h1 class="title">🔬 半導体最新論文レポート</h1>
        <p class="subtitle">生成日時: {html.escape(generated_at)} / 新規: {len(today_papers)}件</p>
      </div>
    </header>

    <main class="container">
      {today_section}

      <section class="archive-section" aria-label="過去の日付">
        <h2 class="section-title">過去のアーカイブ（例: 2026-03-22）</h2>
        <div class="archive-list">
          {archive_items}
        </div>
      </section>
    </main>

    <footer class="site-footer">
      <div class="container">
        <small>emi-news-agent</small>
      </div>
    </footer>
  </body>
</html>"""

def run():
    api_key = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    # 1. 履歴ファイルの読み込み（過去に読んだ論文を思い出す）
    history_file = "history.txt"
    history_path = Path(history_file)
    if history_path.exists():
        with open(history_file, "r", encoding="utf-8") as f:
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

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    date_str = datetime.now().strftime("%Y-%m-%d")

    archive_dir = Path("archive") / date_str
    archive_dir.mkdir(parents=True, exist_ok=True)

    # 4. 日付ごとのページを生成
    archive_index_html = build_archive_page_html(new_papers, date_str, generated_at, "../styles.css")
    with open(archive_dir / "index.html", "w", encoding="utf-8") as f:
        f.write(archive_index_html)

    # 5. ルートのトップページを生成（過去アーカイブへの導線）
    archive_dates = get_archive_dates(Path("archive"))
    index_html = build_root_index_html(new_papers, generated_at, archive_dates)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(index_html)

    if not new_papers:
        print("今日は新しい論文がありませんでした（アーカイブページは作成済み）。")
        return

    # 6. 新しい履歴を保存
    with open(history_file, "w", encoding="utf-8") as f:
        f.write("\n".join(processed_ids))
        
    print("🎉 index.html / archive と履歴の更新が完了しました！")

if __name__ == "__main__":
    run()
