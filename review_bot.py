"""
PR에 커밋된 Java 풀이를 감지하고
Claude가 블로그 글 초안을 PR 코멘트로 작성합니다.
PR 코멘트로 수정 요청 시 자동 답글.
PR 머지 시 티스토리 자동 포스팅.
"""

import os
import re
import time
import requests
import anthropic
from datetime import datetime

GITHUB_TOKEN = os.environ["ALGO_GITHUB_TOKEN"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
TISTORY_ID = os.environ.get("TISTORY_ID", "")
TISTORY_PW = os.environ.get("TISTORY_PW", "")
BLOG_ADDRESS = "archive-log"
GITHUB_REPO = "hyemii/archive-algo"
EVENT_NAME = os.environ.get("EVENT_NAME", "workflow_dispatch")
COMMENT_BODY = os.environ.get("COMMENT_BODY", "")
COMMENT_PR_NUMBER = os.environ.get("COMMENT_PR_NUMBER", "")
PR_MERGED = os.environ.get("PR_MERGED", "false")
MERGED_PR_NUMBER = os.environ.get("MERGED_PR_NUMBER", "")

GITHUB_API = "https://api.github.com"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}
BOT_TAG = "<!-- bot-comment -->"  # 봇 코멘트 식별 태그 (무한루프 방지)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


# ──────────────────────────────────────────
# 1. PR 정보 수집
# ──────────────────────────────────────────
 
def get_open_prs() -> list[dict]:
    response = requests.get(
        f"{GITHUB_API}/repos/{GITHUB_REPO}/pulls",
        headers=HEADERS,
        params={"state": "open"}
    )
    return response.json()
 
 
def get_pr_java_files(pr_number: int) -> list[dict]:
    response = requests.get(
        f"{GITHUB_API}/repos/{GITHUB_REPO}/pulls/{pr_number}/files",
        headers=HEADERS
    )
    files = []
    for f in response.json():
        if f["filename"].startswith("solutions/") and f["filename"].endswith(".java"):
            files.append({
                "filename": f["filename"],
                "raw_url": f["raw_url"]
            })
    return files
 
 
def get_file_content(raw_url: str) -> str:
    response = requests.get(raw_url, headers=HEADERS)
    return response.text
 
 
def parse_file_info(filepath: str) -> dict:
    """solutions/day01/Day1_1.java → day=1, problem_num=1"""
    match = re.search(r"day(\d+)/Day(\d+)_(\d+)\.java", filepath)
    if not match:
        return {}
    return {
        "day": int(match.group(1)),
        "problem_num": int(match.group(3))
    }
 
 
# ──────────────────────────────────────────
# 2. 연관 Issue 찾기
# ──────────────────────────────────────────
 
def find_issue(day: int, problem_num: int) -> dict:
    response = requests.get(
        f"{GITHUB_API}/repos/{GITHUB_REPO}/issues",
        headers=HEADERS,
        params={"state": "all", "labels": f"Day-{day}", "per_page": 100}
    )
    for issue in response.json():
        if "pull_request" in issue:
            continue
        if f"Problem {problem_num}" in issue.get("body", "") or \
           f"Problem {problem_num}" in issue.get("title", ""):
            return issue
    return {}
 
 
# ──────────────────────────────────────────
# 3. PR 코멘트 목록 조회
# ──────────────────────────────────────────
 
def get_pr_comments(pr_number: int) -> list[dict]:
    response = requests.get(
        f"{GITHUB_API}/repos/{GITHUB_REPO}/issues/{pr_number}/comments",
        headers=HEADERS
    )
    return response.json()
 
 
def find_draft_comment(comments: list[dict]) -> dict:
    """봇이 작성한 블로그 초안 코멘트 찾기"""
    for c in comments:
        if BOT_TAG in c.get("body", "") and "블로그 글" in c.get("body", ""):
            return c
    return {}
 
 
# ──────────────────────────────────────────
# 4. Claude로 블로그 글 초안 생성
# ──────────────────────────────────────────
 
def generate_blog_draft(code: str, issue: dict) -> str:
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2500,
        messages=[{
            "role": "user",
            "content": f"""
당신은 8년차 Java 백엔드 개발자의 코테 풀이를 리뷰하고 블로그 글을 작성하는 어시스턴트입니다.
 
아래 형식을 정확히 따르세요. 마크다운이 아닌 **HTML 형식**으로 작성해주세요.
티스토리 기본 에디터에 바로 붙여넣을 수 있는 HTML이어야 합니다.
 
[제목]
<제목>
[코테] 문제제목 - 핵심기법
(예: [코테] 괄호 판별 - Stack에서 ArrayDeque로 성능 개선하기)
 
[본문]
<h2>📌 문제 설명</h2>
<p>(문제 내용)</p>
 
🔢 입력 조건
<ul>
  <li>(조건1)</li>
</ul>
 
📤 출력 조건
<ul>
  <li>(조건1)</li>
</ul>
 
🧪 예제 입력 / 출력
<pre><code>(예제)</code></pre>
 
<h2>✍️ 직접 구현한 코드 (초기 버전)</h2>
<pre><code class="language-java">(풀이 코드 그대로)</code></pre>
 
<h2>❗ 개선 포인트</h2>
<p>(현재 코드의 문제점과 개선 방향 3~5줄)</p>
 
<h2>✨ 개선된 코드 (리팩토링 버전)</h2>
<pre><code class="language-java">(리팩토링된 코드)</code></pre>
 
<h2>💡 정리</h2>
<table style="border-collapse: collapse; width: 100%; height: 114px;" border="1" data-ke-align="alignLeft" data-ke-style="style12">
  <thead>
    <tr style="height: 19px;">
      <th style="text-align: center; height: 19px;">항목</th>
      <th style="text-align: center; height: 19px;">개선 전</th>
      <th style="text-align: center; height: 19px;">개선 후</th>
    </tr>
  </thead>
  <tbody>
    <tr style="height: 19px;">
      <td style="text-align: center; height: 19px;">(항목)</td>
      <td style="text-align: center; height: 19px;">(개선 전)</td>
      <td style="text-align: center; height: 19px;">(개선 후)</td>
    </tr>
  </tbody>
</table>
 
[태그]
<태그>
tag1,tag2,tag3
 
---
 
문제 내용 (Issue):
{issue.get("body", "")}
 
제출한 풀이 코드:
{code}
"""
        }]
    )
    return message.content[0].text
 
 
# ──────────────────────────────────────────
# 5. 코멘트 수정 요청 처리
# ──────────────────────────────────────────
 
def handle_comment_request(pr_number: int, user_request: str):
    print(f"💬 수정 요청 감지: {user_request}")
 
    comments = get_pr_comments(pr_number)
    draft_comment = find_draft_comment(comments)
 
    if not draft_comment:
        print("⚠️ 기존 초안 코멘트 없음")
        return
 
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2500,
        messages=[{
            "role": "user",
            "content": f"""
아래는 기존 블로그 글 초안입니다:
 
{draft_comment["body"]}
 
사용자의 수정 요청:
{user_request}
 
수정 요청 사항을 반영해서 해당 섹션만 수정해주세요.
전체 초안을 다시 작성하지 말고, 수정된 부분만 보여주세요.
"""
        }]
    )
 
    reply_body = f"""{BOT_TAG}
## 🔄 수정본
 
> 요청: {user_request}
 
---
 
{message.content[0].text}
 
---
* revised by Claude *
"""
    post_pr_comment(pr_number, reply_body)
 
 
# ──────────────────────────────────────────
# 6. PR 코멘트 등록
# ──────────────────────────────────────────
 
def post_pr_comment(pr_number: int, body: str):
    response = requests.post(
        f"{GITHUB_API}/repos/{GITHUB_REPO}/issues/{pr_number}/comments",
        headers=HEADERS,
        json={"body": body}
    )
    if response.status_code == 201:
        print(f"✅ PR #{pr_number} 코멘트 등록 완료")
    else:
        print(f"❌ 코멘트 등록 실패: {response.status_code}")
 
 
def format_pr_comment(draft: str, day: int, problem_num: int) -> str:
    return f"""{BOT_TAG}
## 🤖 블로그 글 초안 - Day {day} Problem {problem_num}
 
> 아래 초안을 검토해주세요.
> 수정이 필요하면 코멘트로 요청해주세요. (예: "개선 포인트 다시 써줘")
> 최종 확인 후 PR을 머지하면 티스토리에 자동 포스팅됩니다.
 
---
 
{draft}
 
---
* generated by Claude *
"""
 

# ──────────────────────────────────────────
# 7. 티스토리 자동 포스팅
# ──────────────────────────────────────────

def get_final_draft(pr_number: int) -> str:
    """수정본 있으면 마지막 수정본, 없으면 최초 초안 반환"""
    comments = get_pr_comments(pr_number)
 
    revised = [c for c in comments if BOT_TAG in c.get("body", "") and "🔄 수정본" in c.get("body", "")]
    if revised:
        return revised[-1]["body"]
 
    draft = find_draft_comment(comments)
    return draft.get("body", "")


def extract_post_content(draft: str) -> dict:
    """초안에서 제목, 본문, 태그 추출"""
 
    # ── 제목 추출 ──
    # 패턴1: <제목> 섹션
    m = re.search(r"\*\*제목\*\*:?\s*(.+)", draft)
    if m:
        title = m.group(1).strip()
    else:
        # 패턴2: ---\n\n[코테] 제목 (PR #5 형식)
        m = re.search(r"(\[코테\][^\n]+)", draft)
        if m:
            title = m.group(1).strip()
        else:
            # 패턴3: 블로그 글 초안 헤더
            m = re.search(r"블로그 글 초안 - (.+)", draft)
            title = m.group(1).strip() if m else "코테 풀이"
 
    # ── 본문 추출 ──
    # 패턴1: [본문] ~ [태그]
    m = re.search(r"\*\*본문\*\*\s*\n(.*?)\n\s*\*\*태그\*\*", draft, re.DOTALL)
    if m:
        content = m.group(1).strip()
    else:
        # 패턴2: --- 사이
        m = re.search(r"---\n\n(.*?)\n\n---", draft, re.DOTALL)
        content = m.group(1).strip() if m else draft
 
    # ── 태그 추출 ──
    raw_tags = ""
    # 패턴1: <태그> 섹션
    m = re.search(r"\*\*태그\*\*:?\s*(.+)", draft)
    if m:
        raw_tags = m.group(1).strip()
    else:
        # 패턴2: ---\n*generated* 바로 앞 줄 (PR #5 형식)
            m = re.search(r"\n([^\n]+)\n\n---\n\*generated", draft)
            if m:
                raw_tags = m.group(1).strip()
 
    tags = [t.strip().strip("`") for t in raw_tags.split(",") if t.strip()] if raw_tags else []
 
    print(f"   [파싱] 제목: {title}")
    print(f"   [파싱] 태그: {tags}")
    print(f"   [파싱] 본문 앞 100자: {content[:100]}")
 
    return {"title": title, "content": content, "tags": tags}
 

def post_to_tistory(post: dict):
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-setuid-sandbox")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 15)

    try:
        # 로그인
        driver.get("https://www.tistory.com/auth/login")
        wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "link_kakao_id"))).click()
        time.sleep(1)
        wait.until(EC.presence_of_element_located((By.ID, "loginId--1"))).send_keys(TISTORY_ID)
        driver.find_element(By.ID, "password--2").send_keys(TISTORY_PW)
        driver.find_element(By.CLASS_NAME, "btn_g.highlight.submit").click()
        time.sleep(1)
 
        print("✅ 티스토리 로그인 성공")
 
        # 로그인 후 메인 창으로 포커스 전환
        driver.switch_to.window(driver.window_handles[0])
        time.sleep(1)

        # 글쓰기
        print("📄 글쓰기 페이지 이동 중...")
        driver.get(f"https://{BLOG_ADDRESS}.tistory.com/manage/newpost")

        # 임시저장 알럿 처리
        try:
            WebDriverWait(driver, 5).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            print(f"   알럿 감지: {alert.text[:30]}... → 무시하고 새 글 작성")
            alert.dismiss()  # 취소 = 새 글 작성
            time.sleep(1)
        except:
            pass

        print(f"   현재 URL: {driver.current_url}")

        # 카테고리 선택
        driver.find_element(By.ID, "category-btn").click()
        list = driver.find_elements(By.ID, "category-list")
        list[0].find_elements(By.TAG_NAME, "div")[3].click()
        time.sleep(1)

        # 제목 입력
        print("   제목 입력 중...")
        driver.find_element(By.CLASS_NAME, "textarea_tit").send_keys(post["title"])
        time.sleep(1)

        # 본문
        driver.switch_to.frame("editor-tistory_ifr")
        body = driver.find_element(By.TAG_NAME, "body")
        driver.execute_script("arguments[0].innerHTML = arguments[1]", body, post["content"])
        driver.switch_to.default_content()
        time.sleep(1)

        # 태그
        try:
            tag_input = driver.find_element(By.ID, "tagText")
            for tag in post["tags"]:
                tag_input.send_keys(tag + ",")
                time.sleep(0.3)
            print("   태그 입력 완료")
        except:
            print("   태그 입력 스킵")

        # 발행
        print("   발행 버튼 클릭 중...")
        wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "btn-publish"))).click()
        time.sleep(2)
        try:
            wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "btn-primary"))).click()
        except:
            pass

        print(f"✅ 티스토리 포스팅 완료: {post['title']}")

    except Exception as e:
        import traceback
        print(f"❌ 티스토리 포스팅 실패: {e}")
        print(traceback.format_exc())
    finally:
        driver.quit()


def handle_pr_merged(pr_number: int):
    print(f"🎉 PR #{pr_number} 머지 → 티스토리 포스팅 시작")

    draft = get_final_draft(pr_number)
    if not draft:
        print("⚠️ 초안 없음 → 포스팅 생략")
        return

    post = extract_post_content(draft)
    print(f"   제목: {post['title']}")
    post_to_tistory(post)


# ──────────────────────────────────────────
# 8. 메인 실행
# ──────────────────────────────────────────

def run():
    print(f"\n{'='*50}")
    print(f"🚀 리뷰 봇 시작 (event: {EVENT_NAME})")
    print(f"{'='*50}\n")

    # PR 머지 → 티스토리 포스팅
    if PR_MERGED == "true" and MERGED_PR_NUMBER:
        handle_pr_merged(int(MERGED_PR_NUMBER))
        return

    # 코멘트 수정 요청 처리
    if EVENT_NAME == "issue_comment" and COMMENT_BODY and COMMENT_PR_NUMBER:
        handle_comment_request(int(COMMENT_PR_NUMBER), COMMENT_BODY)
        return

    # PR 초안 생성
    prs = get_open_prs()
    if not prs:
        print("오픈된 PR 없음")
        return

    for pr in prs:
        pr_number = pr["number"]
        print(f"📋 PR #{pr_number}: {pr['title']}")

        java_files = get_pr_java_files(pr_number)
        if not java_files:
            print("   Java 파일 없음 → 스킵\n")
            continue

        comments = get_pr_comments(pr_number)
        if find_draft_comment(comments):
            print("   이미 초안 있음 → 스킵\n")
            continue

        for file_info in java_files:
            info = parse_file_info(file_info["filename"])
            if not info:
                continue

            day, problem_num = info["day"], info["problem_num"]
            print(f"   📝 Day {day} - Problem {problem_num} 처리 중...")

            code = get_file_content(file_info["raw_url"])
            issue = find_issue(day, problem_num)

            if not issue:
                print(f"   ⚠️ 연관 Issue 없음")
                continue

            draft = generate_blog_draft(code, issue)
            comment = format_pr_comment(draft, day, problem_num)
            post_pr_comment(pr_number, comment)

        print()

    print("🏁 완료")


if __name__ == "__main__":
    run()