# archive-algo 🧩

> 매일 2문제씩 코테를 풀고, 블로그에 기록하는 자동화 시스템

## 흐름

```
평일 오전 9시
→ Claude가 GitHub Issue에 문제 2개 자동 생성
→ solutions/dayNN/DayN_M.java 템플릿 파일도 자동 생성
→ 풀이 작성 후 PR 생성
→ Claude가 PR 코멘트로 블로그 글 초안 작성
→ 코멘트로 수정 요청 가능
→ PR 머지 → 티스토리 자동 포스팅
```

## 디렉토리 구조

```
archive-algo/
├── .github/workflows/
│   ├── daily-algo.yml         # 평일 9시 Issue + Java 템플릿 자동 생성
│   ├── review-solution.yml    # PR 감지 → 블로그 초안 + 수정 요청 처리
│   └── post-to-tistory.yml    # PR 번호 입력 → 수동 포스팅
├── solutions/
│   ├── day01/
│   │   ├── Day1_1.java
│   │   └── Day1_2.java
│   └── day02/
│       ├── Day2_1.java
│       └── Day2_2.java
├── issue_bot.py
├── review_bot.py
└── README.md
```

## 파일명 규칙

```
solutions/day{NN}/Day{N}_{문제번호}.java

예시)
solutions/day01/Day1_1.java
solutions/day01/Day1_2.java
```

## GitHub Secrets

| Name | 설명 |
|------|------|
| `ALGO_GITHUB_TOKEN` | GitHub Personal Access Token (repo 권한) |
| `ANTHROPIC_API_KEY` | Anthropic API 키 |
| `TISTORY_ID` | 카카오 이메일 |
| `TISTORY_PW` | 카카오 비밀번호 |

## 블로그

👉 [archive-log.tistory.com](https://archive-log.tistory.com)
