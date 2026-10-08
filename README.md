# 한국어 관계 기반 메시지 코치 — 백엔드

외국인 유학생이 교수님·선배·알바 사장님 등 상대와의 관계에 맞는 한국어 메시지를 쓰고, 점검하고, 해석하고, 연습하도록 돕는 **API 서버**입니다. HyperCLOVA X(CLOVA Studio) API만 사용합니다.

이 브랜치(`backend-only`)는 화면이 없는 백엔드 전용입니다. 프론트는 팀에서 `/api/*`를 직접 호출해 연결합니다.

> - 데모 화면(바닐라 HTML/JS)이 있는 버전은 `feature/message-coach` 브랜치에 있습니다.
> - 범용 해커톤 백엔드(`tasks.json` 방식)는 `main` 브랜치에 있습니다.
> - 무엇을 바꾸려면 어디를 고치는지는 [DEV_GUIDE.md](DEV_GUIDE.md)를 보세요.

## 실행 (Windows PowerShell)

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start.ps1
```

- API 문서(Swagger): http://127.0.0.1:8000/docs (`/`로 들어가도 여기로 이동)

처음 실행하면 `.venv` 생성, 패키지 설치, `.env` 복사가 자동으로 됩니다. 기본은 **MOCK 모드**(실제 호출 없음)입니다.

## HyperCLOVA X 연결

1. CLOVA Studio에서 API 키를 발급받습니다 (해커톤에서는 운영진이 지급하는 키를 사용).
2. `.env`를 엽니다.
   ```
   MOCK_MODE=0
   CLOVA_API_KEY=발급받은_키
   ```
3. 연결 확인: `.venv\Scripts\python.exe scripts\smoke_test.py` (이미지까지: `--image 캡처.png`)
4. 서버를 다시 시작합니다. `GET /api/health`의 `mock`이 `false`면 실제 호출 모드입니다.

모델명이나 주소가 다르게 지급되면 `.env`의 `CLOVA_BASE_URL`, `MODEL_ANALYSIS`, `MODEL_VISION`, `MODEL_LIGHT`를 바꿉니다. API 경로나 파라미터 이름이 바뀌면 [app/hcx/client.py](app/hcx/client.py) 맨 위 상수만 고칩니다.

## 프론트에서 연결하기

1. 프론트 개발 서버 주소를 `.env`의 `CORS_ORIGINS`에 넣습니다 (쉼표로 구분, 기본값 `http://localhost:3000,http://localhost:5173`).
2. `.env`에 `TEAM_API_KEY`를 설정했다면, 모든 `/api/*` 요청에 `X-Team-Key` 헤더로 같은 값을 보냅니다 (`/api/health` 제외). 비워 두면 검사하지 않습니다.
3. 오류는 항상 `{"detail": "사람이 읽을 수 있는 메시지"}` 형태입니다 (422 입력 오류, 404 없는 상대·세션, 429·5xx HCX 오류).
4. AI를 호출하는 모든 응답에는 `meta: {calls: [{model, mock, cached, total_tokens, latency_ms}], total_tokens}`가 붙습니다.

```js
const API = "http://127.0.0.1:8000";

const res = await fetch(`${API}/api/coach`, {
  method: "POST",
  headers: { "Content-Type": "application/json" /*, "X-Team-Key": "..." */ },
  body: JSON.stringify({ text: "교수님 내일 과제 좀 늦게 내도 돼요?", relation: "professor" }),
});
const data = await res.json();
if (!res.ok) throw new Error(data.detail);
// data.scores, data.issues[].start/end (원문 하이라이트 위치), data.revised

// 캡처 해석은 form-data
const form = new FormData();
form.append("image", fileInput.files[0]);
form.append("relation", "professor");
const interpret = await (await fetch(`${API}/api/interpret`, { method: "POST", body: form })).json();
```

## API

| API | 기능 | 주요 응답 필드 | 사용 모델 |
|---|---|---|---|
| `POST /api/compose` | ① 관계·목적·핵심 내용 → 메시지 초안 | `draft`, `notes` | HCX-007 (+임베딩) |
| `POST /api/coach` | ② 내 메시지 점검 | `scores`, `issues[]`(`quote`, `start`, `end`, …), `revised`, `summary` | HCX-007 (+임베딩) |
| `POST /api/interpret` | ③ 받은 메시지(텍스트/캡처) 해석 | `extracted_text`, `intent`, `emotion`, `urgency`, `key_points`, `reply_draft` | HCX-005 → HCX-007 |
| `POST /api/rehearsal/start` · `/{id}/message` · `/{id}/end`, `GET /{id}` | ④ 역할극 연습 → 피드백 리포트 | `session_id`, `reply`, `report` | DASH-002 → HCX-007 |
| `/api/contacts` (CRUD), `/{id}/interactions` | ⑤ 상대 프로필과 지난 기록 | — | — |
| `POST /api/route` | 자유 입력 → 기능 분류 | `feature` | DASH-002 |
| `GET /api/usage` | 기능별·모델별 토큰, 한도, 최근 호출 | — | — |
| `GET /api/domain` | 프론트 선택지 (관계·목적·시나리오) | — | — |
| `GET /api/knowledge/search` | 참고 자료 검색 확인 | — | 임베딩 |
| `GET /api/health` | MOCK 여부, 모델 설정 | — | — |

요청 형식은 [DEV_GUIDE.md](DEV_GUIDE.md) 6-5장이나 `/docs`에서 확인합니다. compose·coach·interpret·rehearsal에 `contact_id`를 넘기면 그 상대의 프로필과 지난 기록이 프롬프트 `{memory}`에 들어가고, 이번 결과가 기록에 추가됩니다.

## 기능별로 떼어 쓰기

**기능 이름 하나가 모든 파일 이름에 똑같이 쓰입니다.** 기능 하나를 가져가거나 빼려면 그 이름의 파일만 찾으면 됩니다.

| 기능 | 라우트 | 서비스 | 프롬프트 · 스키마 (`customize/`) | 테스트 |
|---|---|---|---|---|
| ① compose | `routes/compose.py` | `services/compose.py` | `prompts/compose.md`, `schemas/compose.json` | `test_compose.py` |
| ② coach | `routes/coach.py` | `services/coach.py`, `services/coach_highlight.py` | `prompts/coach.md`, `schemas/coach.json` | `test_coach.py` |
| ③ interpret | `routes/interpret.py` | `services/interpret.py` | `prompts/interpret_ocr.md`, `prompts/interpret.md`, `schemas/interpret.json` | `test_interpret.py` |
| ④ rehearsal | `routes/rehearsal.py` | `services/rehearsal.py`, `stores/rehearsal_store.py` | `prompts/rehearsal_role.md`, `prompts/rehearsal_feedback.md`, `schemas/rehearsal_feedback.json` | `test_rehearsal.py` |
| ⑤ contacts | `routes/contacts.py` | `stores/contact_store.py` | — | `test_contacts.py` |
| route | `routes/route.py` | `services/route.py` | `prompts/route.md` | `test_route.py` |
| usage | `routes/usage.py` | (`hcx/usage.py`) | — | `test_usage.py` |
| knowledge | `routes/knowledge.py` | `services/knowledge.py` | `knowledge/*.md` | `test_knowledge.py` |

**모든 기능이 같이 쓰는 부품** (기능을 가져갈 때 함께 가져가야 함):

| 파일 | 역할 |
|---|---|
| `app/hcx/` | HyperCLOVA X 호출 창구 (MOCK, 캐시, 한도, 사용량 기록) |
| `app/services/shared.py` | `build_prompt_values()` 프롬프트 변수 + 참고 자료 + 메모리, `find_contact()`, `save_interaction()`, `call_meta()` |
| `app/customize.py` | `customize/` 읽기 (요청마다 다시 읽음) |
| `app/core.py`, `app/deps.py`, `app/config.py` | 부품 묶음, 라우트 공통 의존성, `.env` 설정 |
| `customize/domain.yaml` | 서비스명, 관계·목적·격식, 리허설 시나리오, 엔진 설정값 |

**기능 하나를 빼려면**: [app/main.py](app/main.py)에서 그 기능의 `include_router` 줄을 지우고, 위 표의 같은 이름 파일을 삭제합니다. `contacts`를 빼면 다른 기능의 `contact_id`도 쓸 수 없고, `knowledge`를 빼면 `shared.py`의 참고 자료 검색도 함께 정리해야 합니다.

## 구조

```
app/
  main.py             앱 조립, 라우터 연결
  config.py           .env → Settings
  core.py             공통 부품 묶음 (hcx, customize, knowledge, contacts, rehearsals)
  deps.py             라우트 공통 의존성 (X-Team-Key 검사)
  customize.py        customize/ 읽기
  hcx/                HyperCLOVA X 호출 창구 — 모든 호출이 client.py를 거침
  routes/             API 라우트 (파일 하나 = 기능 하나)
  services/           기능 로직 (파일 하나 = 기능 하나) + shared.py
  stores/             SQLite 저장소 (contact_store, rehearsal_store)
customize/            당일 교체 영역 — 코드 수정 없이 서비스 성격 변경
  domain.yaml         서비스명, 관계·목적·격식, 리허설 시나리오, 엔진 설정값
  prompts/*.md        시스템 프롬프트 ({변수} 자리 채움)
  schemas/*.json      Structured Outputs 스키마
  knowledge/*.md      참고 자료 ('## 제목' 단위)
scripts/              start.ps1, smoke_test.py
tests/                pytest (파일 이름 = 기능 이름)
data/                 사용량 로그·캐시·DB (Git 제외)
```

## 주제 공개 당일

```powershell
Select-String -Path customize\*, customize\*\* -Pattern "TODO\(DAY-OF\)"
```

위 명령으로 채울 곳을 찾습니다. 프롬프트·스키마·domain.yaml은 저장하면 서버 재시작 없이 바로 반영됩니다. 스키마 필드 이름을 바꾸면 응답 JSON의 필드 이름도 바뀌므로 프론트도 맞춰야 합니다.

## 크레딧 절약 장치

- `temperature=0` 요청은 응답을 캐시합니다 (`CACHE_TTL_SECONDS`).
- `MAX_LIVE_CALLS`, `TOKEN_STOP_THRESHOLD`에 도달하면 실제 호출을 막습니다.
- 모든 호출은 `data/usage_log.jsonl`에 기능·모델·토큰·지연시간이 기록되고, `GET /api/usage`로 볼 수 있습니다.

## 테스트

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest -q
```
