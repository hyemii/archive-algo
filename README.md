# archive-algo 🧩

> 매일 2문제씩 코테를 풀고, 블로그에 기록하는 자동화 시스템

## 소개

8년차 Java 백엔드 개발자의 코딩테스트 준비 기록입니다.  
Claude API + GitHub Actions로 문제 출제부터 블로그 포스팅까지 자동화했습니다.

## 흐름

```
매일 오전 9시
→ Claude가 GitHub Issue에 문제 2개 자동 생성
→ solutions/dayNN/DayN_1.java 작성 후 PR 생성
→ Claude가 PR 코멘트로 블로그 글 초안 작성
→ 검토 및 수정 후 PR 머지
→ 티스토리 자동 포스팅
```

## 디렉토리 구조

```
archive-algo/
├── .github/workflows/
│   ├── daily-algo.yml        # 매일 9시 Issue 자동 생성
│   └── review-solution.yml   # PR 감지 → 블로그 초안 작성
├── solutions/
│   ├── day01/
│   │   ├── Day1_1.java
│   │   └── Day1_2.java
│   └── day02/
│       ├── Day2_1.java
│       └── Day2_2.java
├── issue_bot.py              # 문제 생성 봇
└── review_bot.py             # 리뷰 & 블로그 초안 봇
```

## 파일명 규칙

```
solutions/day{NN}/Day{N}_{문제번호}.java

예시)
solutions/day01/Day1_1.java
solutions/day01/Day1_2.java
solutions/day02/Day2_1.java
```

## 블로그

👉 [archive-log.tistory.com](https://archive-log.tistory.com)

## 사용 기술

- Java
- Claude API (Anthropic)
- GitHub Actions
- Selenium (티스토리 자동 포스팅)
