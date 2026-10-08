# 한국어 관계 기반 메시지 코치

외국인 유학생이 교수님·선배·알바 사장님 등 상대와의 관계에 맞는 한국어 메시지를 쓰고, 점검하고, 해석하고, 연습하는 서비스입니다. HyperCLOVA X(CLOVA Studio) API만 사용합니다.

> 범용 해커톤 백엔드(`tasks.json` 방식)는 `main` 브랜치에 그대로 있습니다.
>
> **무엇을 바꾸려면 어디를 고치는지는 [DEV_GUIDE.md](DEV_GUIDE.md)를 보세요.**

## 실행 (Windows PowerShell)

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start.ps1
```

- 데모 화면: http://127.0.0.1:8000
- API 문서: http://127.0.0.1:8000/docs

처음 실행하면 `.venv` 생성, 패키지 설치, `.env` 복사가 자동으로 됩니다. 기본은 **MOCK 모드**(실제 호출 없음)입니다.

## HyperCLOVA X 연결

1. CLOVA Studio에서 API 키를 발급받습니다 (해커톤에서는 운영진이 지급하는 키를 사용).
2. `.env`를 엽니다.
   ```
   MOCK_MODE=0
   CLOVA_API_KEY=발급받은_키
   ```
3. 연결 확인: `.venv\Scripts\python.exe scripts\smoke_test.py` (이미지까지: `--image 캡처.png`)
4. 서버를 다시 시작합니다. 화면 오른쪽 위 배지가 "HyperCLOVA X 연결됨"으로 바뀝니다.

모델명이나 주소가 다르게 지급되면 `.env`의 `CLOVA_BASE_URL`, `MODEL_ANALYSIS`, `MODEL_VISION`, `MODEL_LIGHT`를 바꿉니다. API 경로나 파라미터 이름이 바뀌면 [app/hcx/client.py](app/hcx/client.py) 맨 위 상수만 고칩니다.

## 구조

```
app/                  엔진 — 당일엔 거의 안 건드림
  main.py             앱 조립, 라우터·정적 파일 연결
  config.py           .env → Settings
  core.py             공통 부품 묶음 (hcx, customize, knowledge, memory, rehearsals)
  customize.py        customize/ 읽기 (요청마다 다시 읽음)
  hcx/                HyperCLOVA X 호출 창구 — 모든 호출이 client.py를 거침
  services/           기능 로직 (coach, compose, interpret, rehearsal, rag, router)
  routes/             API 라우트
  memory.py           관계 메모리 (SQLite)
  rehearsal_store.py  리허설 세션 (SQLite)
customize/            당일 교체 영역 — 코드 수정 없이 서비스 성격 변경
  domain.yaml         서비스명, 관계·목적·격식, 리허설 시나리오, 엔진 설정값
  prompts/*.md        시스템 프롬프트 ({변수} 자리 채움)
  schemas/*.json      Structured Outputs 스키마
  knowledge/*.md      RAG 자료 ('## 제목' 단위)
web/                  데모 화면 (바닐라 HTML/JS/CSS)
scripts/              start.ps1, smoke_test.py
tests/                pytest
data/                 사용량 로그·캐시·DB (Git 제외)
```

## API

| API | 기능 | 사용 모델 |
|---|---|---|
| `POST /api/compose` | ① 관계·목적·핵심 내용 → 메시지 초안 | HCX-007 (+임베딩) |
| `POST /api/coach` | ② 점수 3종 + 문제 구간(start/end) + 수정본 | HCX-007 (+임베딩) |
| `POST /api/interpret` | ③ 받은 메시지(텍스트/캡처) → 의도·감정·답장 | HCX-005 → HCX-007 |
| `POST /api/rehearsal/start` · `/{id}/message` · `/{id}/end` | ④ 역할극 연습 → 피드백 리포트 | DASH-002 → HCX-007 |
| `/api/contacts` (CRUD), `/api/contacts/{id}/interactions` | ⑤ 상대 프로필과 지난 기록 | — |
| `POST /api/route` | 자유 입력 → 기능 분류 | DASH-002 |
| `GET /api/usage` | 기능별·모델별 토큰, 한도, 최근 호출 | — |
| `GET /api/domain`, `GET /api/knowledge/search` | 화면 선택지, RAG 검색 확인 | — |
| `GET /api/health` | MOCK 여부, 모델 설정 | — |

compose·coach·interpret·rehearsal에 `contact_id`를 넘기면 그 상대의 프로필과 지난 기록이 프롬프트 `{memory}`에 들어가고, 이번 결과가 기록에 추가됩니다.

## 주제 공개 당일

```powershell
Select-String -Path customize\*, customize\*\*, web\* -Pattern "TODO\(DAY-OF\)"
```

위 명령으로 채울 곳을 찾습니다. 프롬프트·스키마·domain.yaml은 저장하면 서버 재시작 없이 바로 반영됩니다. 스키마 필드 이름을 바꾸면 `web/app.js`의 해당 표시 부분도 맞춰야 합니다.

## 크레딧 절약 장치

- `temperature=0` 요청은 응답을 캐시합니다 (`CACHE_TTL_SECONDS`).
- `MAX_LIVE_CALLS`, `TOKEN_STOP_THRESHOLD`에 도달하면 실제 호출을 막습니다.
- 모든 호출은 `data/usage_log.jsonl`에 기능·모델·토큰·지연시간이 기록되고, 화면 "토큰" 탭에 표시됩니다.

## 테스트

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest -q
```
