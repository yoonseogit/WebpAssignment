# CoinSight

웹프로그래밍 기말 프로젝트

CoinSight는 업비트 공개 API를 활용해 KRW 마켓의 변동성 순위를 제공하고, 사용자가 등록한 관심 종목을 OpenAI API로 요약 분석하는 웹 서비스입니다. 분석 결과는 투자 조언이 아니라 학습용 데이터 요약입니다.

## 프로젝트 개요

- 서비스명: CoinSight
- 주제: 업비트 변동성 기반 관심 코인 GPT 요약 분석 서비스
- GitHub 저장소: https://github.com/yoonseogit/WebpAssignment
- 배포 방식: Docker 기반 Render 배포
- 핵심 기술: React, FastAPI, PostgreSQL, Docker, Nginx, GitHub Actions

## 주요 기능

### 1. 로그인 및 회원가입

- 이메일과 비밀번호 기반 회원가입
- 비밀번호 해시 저장
- JWT 기반 인증
- 회원별 관심 종목 관리

### 2. 업비트 변동성 순위

- 업비트 공개 API에서 KRW 마켓 전체 종목 조회
- 현재가, 고가, 저가, 24시간 거래대금 표시
- 변동성 계산:

```text
변동성 = (고가 - 저가) / 현재가 * 100
```

- 변동성, 등락률, 거래대금 기준 정렬
- 종목명 및 마켓 코드 검색

### 3. 관심 종목 관리

- 로그인한 사용자가 관심 종목 등록
- 회원별 관심 종목 DB 저장
- 관심 종목 최대 5개 제한
- 중복 등록 방지
- 관심 종목 삭제 가능

### 4. GPT 요약 분석

- 관심 종목의 최근 일봉 데이터를 조회
- OpenAI API로 종목별 요약 분석 생성
- 분석 내용:
  - 최근 가격 흐름
  - 추세
  - 변동성 수준
  - 리스크 참고 문구
- 분석 결과를 DB에 캐싱
- OpenAI API 키가 없는 경우 로컬 계산 기반 요약 제공

### 5. Web Storage 활용

localStorage:

- 다크모드/라이트모드
- 검색어
- 정렬 기준

sessionStorage:

- 마지막 GPT 분석 결과 임시 저장

## 과제 조건 충족 내용

### GitHub Actions CI/CD

- `.github/workflows/ci-cd.yml` 구성
- 백엔드 문법 검사
- 프론트엔드 빌드
- Docker 이미지 빌드
- main 브랜치 push 시 Render deploy hook 호출 가능

### Docker

- 루트 `Dockerfile`로 단일 배포 이미지 생성
- 프론트엔드 빌드
- 백엔드 FastAPI 실행
- Nginx 포함

### Nginx

- React 정적 파일 서빙
- `/api` 요청을 FastAPI 서버로 프록시
- SPA 라우팅 지원

### DBMS

- PostgreSQL 사용
- 저장 데이터:
  - 회원 정보
  - 관심 종목
  - GPT 분석 캐시

### Web Storage

- localStorage와 sessionStorage를 모두 사용
- 새로고침 후 사용자 설정 유지 확인 가능

## 시스템 구조

```text
사용자 브라우저
        |
        v
      Nginx
   /        \
React      /api 프록시
정적 파일       |
               v
            FastAPI
        /      |       \
   PostgreSQL  Upbit   OpenAI API
```

## 기술 스택

Frontend:

- React
- Vite
- Recharts
- lucide-react

Backend:

- FastAPI
- SQLAlchemy
- JWT
- passlib bcrypt

Database:

- PostgreSQL

Infra:

- Docker
- Docker Compose
- Nginx
- GitHub Actions
- Render

External APIs:

- Upbit Quotation API
- OpenAI Responses API

## 로컬 실행 방법

```bash
docker compose up --build
```

접속:

```text
http://localhost:8080
```

종료:

```bash
docker compose down
```

## 환경 변수

```text
JWT_SECRET=replace-with-a-long-random-secret
DATABASE_URL=postgresql://coinsight:coinsight@db:5432/coinsight
MAX_FAVORITE_MARKETS=5
ANALYSIS_CACHE_MINUTES=30
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
```

## PostgreSQL 접속 정보

로컬 실행 시 PostgreSQL 클라이언트에서 아래 정보로 접속할 수 있습니다.

```text
Host: localhost
Port: 5432
Database: coinsight
Username: coinsight
Password: coinsight
```

확인할 주요 테이블:

- `users`
- `favorite_markets`
- `analysis_cache`

## 배포 방법

### 1. GitHub 저장소 업로드

```bash
git init
git add .
git commit -m "Initial CoinSight project"
git branch -M main
git remote add origin https://github.com/yoonseogit/WebpAssignment.git
git push -u origin main
```

### 2. Render PostgreSQL 생성

Render에서 PostgreSQL 서비스를 생성한 뒤 Database URL을 복사합니다.

### 3. Render Web Service 생성

- New Web Service 선택
- GitHub 저장소 연결
- Environment: Docker
- Dockerfile Path: `./Dockerfile`
- Branch: `main`

### 4. Render 환경 변수 설정

```text
DATABASE_URL=Render PostgreSQL Database URL
JWT_SECRET=긴 랜덤 문자열
MAX_FAVORITE_MARKETS=5
ANALYSIS_CACHE_MINUTES=30
OPENAI_API_KEY=OpenAI API Key
OPENAI_MODEL=gpt-4.1-mini
```

### 5. GitHub Actions 배포 Hook 설정

Render Web Service의 Deploy Hook URL을 GitHub Actions Secret에 등록합니다.

```text
Secret name: RENDER_DEPLOY_HOOK_URL
Secret value: Render Deploy Hook URL
```

이후 main 브랜치에 push하면 GitHub Actions가 실행되고, 성공 시 Render 배포가 자동으로 트리거됩니다.

## CI/CD 시연 방법

관심 종목 최대 개수를 5개에서 7개로 변경하면서 CI/CD를 시연할 수 있습니다.

수정 위치:

```python
# backend/app/config.py
MAX_FAVORITE_MARKETS = int(os.getenv("MAX_FAVORITE_MARKETS", "5"))
```

시연 흐름:

1. 배포된 사이트에서 관심 종목 최대 5개 제한 확인
2. 제한값을 7로 수정
3. Git commit 및 push
4. GitHub Actions 실행 확인
5. Render 자동 배포 확인
6. 배포 URL 새로고침
7. 관심 종목 최대 7개 제한 반영 확인

## 발표 영상 구성

1. 서비스 소개
2. 회원가입 및 로그인
3. 업비트 변동성 순위 확인
4. 검색 및 정렬 기능 시연
5. 관심 종목 추가 및 최대 5개 제한 확인
6. GPT 요약 분석 실행
7. PostgreSQL 테이블 및 데이터 확인
8. localStorage/sessionStorage 동작 확인
9. Docker, Nginx, DBMS 구조 설명
10. GitHub Actions와 Render를 이용한 CI/CD 시연

## 주의 사항

- 본 서비스의 분석 결과는 투자 조언이 아닙니다.
- OpenAI API 키가 없으면 로컬 계산 기반 요약이 표시됩니다.
- 업비트 공개 API 응답 상태에 따라 데이터 갱신이 지연될 수 있습니다.
