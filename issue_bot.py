"""
매일 코테 문제 2개를 GitHub Issues로 자동 등록
+ solutions/dayNN/DayN_M.java 템플릿 파일 자동 생성
"""

import os
import re
import base64
import requests
import anthropic
from datetime import datetime

GITHUB_TOKEN = os.environ["ALGO_GITHUB_TOKEN"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
GITHUB_REPO = "hyemii/archive-algo"

GITHUB_API = "https://api.github.com"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


# ──────────────────────────────────────────
# 1. 오늘 Day 번호 계산
# ──────────────────────────────────────────

def get_today_day() -> int:
    response = requests.get(
        f"{GITHUB_API}/repos/{GITHUB_REPO}/issues",
        headers=HEADERS,
        params={"state": "all", "per_page": 100}
    )
    data = response.json()
    if not isinstance(data, list):
        return 1
    return (len(data) // 2) + 1


# ──────────────────────────────────────────
# 2. 기존 출제 주제 수집 (중복 방지)
# ──────────────────────────────────────────

def get_used_topics() -> list[str]:
    response = requests.get(
        f"{GITHUB_API}/repos/{GITHUB_REPO}/issues",
        headers=HEADERS,
        params={"state": "all", "per_page": 100}
    )
    data = response.json()
    if not isinstance(data, list):
        print(f"⚠️ Issues API 응답 오류: {data}")
        return []
    topics = []
    for issue in data:
        if not isinstance(issue, dict):
            continue
        match = re.search(r"\*\*알고리즘 유형\*\*: (.+)", issue.get("body", "") or "")
        if match:
            topics.append(match.group(1).strip())
    return topics


# ──────────────────────────────────────────
# 3. Claude로 문제 생성
# ──────────────────────────────────────────

def generate_problem(day: int, problem_num: int, used_topics: list[str]) -> dict:
    used_str = "\n".join(f"- {t}" for t in used_topics) if used_topics else "없음"

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"""
당신은 코딩테스트 전문 출제자입니다.

대상: 8년차 Java 백엔드 개발자 (코테 준비 중)
난이도: 중급
언어: Java

이미 출제된 주제 (중복 금지):
{used_str}

아래 형식을 정확히 지켜 문제 1개를 만들어주세요.
설명 없이 형식만:

[주제]
알고리즘 유형 한 줄 (예: 스택/단조스택)

[제목]
[코테] 문제제목 - 핵심기법

[문제설명]
2~3줄 이내

[입력조건]
- 조건1
- 조건2

[출력조건]
- 조건1

[예제1]
입력:
출력:
설명:

[예제2]
입력:
출력:
설명:
"""
        }]
    )
    return parse_problem(message.content[0].text, day, problem_num)


def parse_problem(raw: str, day: int, problem_num: int) -> dict:
    sections = {}
    current = None
    buffer = []

    for line in raw.strip().split("\n"):
        if line.startswith("[") and line.endswith("]"):
            if current and buffer:
                sections[current] = "\n".join(buffer).strip()
            current = line[1:-1]
            buffer = []
        elif line.strip():
            buffer.append(line.strip())
    if current and buffer:
        sections[current] = "\n".join(buffer).strip()

    today = datetime.now().strftime("%Y.%m.%d")
    title = sections.get("제목", f"[코테] Day {day} - Problem {problem_num}")
    topic = sections.get("주제", "")

    body = f"""**알고리즘 유형**: {topic}

---

## 📌 문제 설명

{sections.get("문제설명", "")}

## 🔢 입력 조건

{sections.get("입력조건", "")}

## 📤 출력 조건

{sections.get("출력조건", "")}

## 🧪 예제

```
{sections.get("예제1", "")}

{sections.get("예제2", "")}
```

---

> Day {day} - Problem {problem_num} | {today}
"""

    return {
        "title": title,
        "body": body,
        "topic": topic,
        "labels": ["코테", f"Day-{day}"]
    }


# ──────────────────────────────────────────
# 4. GitHub Issue 등록
# ──────────────────────────────────────────

def ensure_label(name: str):
    requests.post(
        f"{GITHUB_API}/repos/{GITHUB_REPO}/labels",
        headers=HEADERS,
        json={"name": name, "color": "0075ca"}
    )


def create_issue(problem: dict):
    for label in problem["labels"]:
        ensure_label(label)

    response = requests.post(
        f"{GITHUB_API}/repos/{GITHUB_REPO}/issues",
        headers=HEADERS,
        json={
            "title": problem["title"],
            "body": problem["body"],
            "labels": problem["labels"]
        }
    )

    if response.status_code == 201:
        print(f"✅ Issue 생성: {response.json()['html_url']}")
    else:
        print(f"❌ Issue 생성 실패: {response.status_code} {response.text}")


# ──────────────────────────────────────────
# 5. Java 템플릿 파일 자동 생성
# ──────────────────────────────────────────

def create_java_template(day: int, problem_num: int, problem: dict):
    day_str = str(day).zfill(2)
    class_name = f"Day{day}_{problem_num}"
    file_path = f"solutions/day{day_str}/{class_name}.java"

    java_content = f"""// {problem['title']}
// Day {day} - Problem {problem_num} | {datetime.now().strftime("%Y.%m.%d")}
// 알고리즘 유형: {problem['topic']}

import java.util.*;

public class {class_name} {{
    public static void main(String[] args) {{
        Scanner scanner = new Scanner(System.in);

        // TODO: 풀이 작성

        scanner.close();
    }}
}}
"""

    encoded = base64.b64encode(java_content.encode("utf-8")).decode("utf-8")

    response = requests.put(
        f"{GITHUB_API}/repos/{GITHUB_REPO}/contents/{file_path}",
        headers=HEADERS,
        json={
            "message": f"feat: Day {day} Problem {problem_num} 풀이 템플릿 추가",
            "content": encoded
        }
    )

    if response.status_code in (200, 201):
        print(f"✅ Java 템플릿 생성: {file_path}")
    else:
        print(f"❌ Java 파일 생성 실패: {response.status_code} {response.text}")


# ──────────────────────────────────────────
# 6. 메인 실행
# ──────────────────────────────────────────

def run():
    day = get_today_day()
    used_topics = get_used_topics()
    today = datetime.now().strftime("%Y.%m.%d")

    print(f"\n{'='*50}")
    print(f"🚀 Day {day} 문제 생성 시작 ({today})")
    print(f"{'='*50}\n")

    for i in range(1, 3):
        print(f"📝 문제 {i} 생성 중...")
        problem = generate_problem(day, i, used_topics)
        used_topics.append(problem["topic"])
        create_issue(problem)
        create_java_template(day, i, problem)
        print()

    print(f"🏁 완료! https://github.com/{GITHUB_REPO}/issues")


if __name__ == "__main__":
    run()