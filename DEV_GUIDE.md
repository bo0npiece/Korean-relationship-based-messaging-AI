# 개발 가이드: 주제가 바뀌어도 내가 고칠 수 있게

이 문서 하나로 **"무엇을 바꾸려면 어디를 고치나"**를 찾을 수 있게 정리했습니다.
처음 읽을 때는 1 → 2 → 3장 순서로 읽고, 당일에는 4장(수정 지도)과 8장(체크리스트)을 펴 두세요.

---

## 1. 기획 검토

### 1-1. 심사 기준 대비

| 기준 (배점) | 지금 강점 | 보완할 점 |
|---|---|---|
| 기획 (20) | "외국인 유학생 × 관계별 한국어"라는 타깃이 분명함 | 당일 주제와 연결하는 한 문장이 필요함 (예: 주제가 "소통"이면 그대로, "교육"이면 학습 도구로 포장) |
| 창의 (10) | 관계 메모리, 리허설(역할극), 캡처 해석 | 데모에서 "같은 문장이 상대에 따라 다르게 고쳐지는" 장면을 보여 주기 |
| 기술 (25) | 모델 3종 역할 분담, 2단계 파이프라인(005→007), Structured Outputs, 임베딩 RAG, 캐시·한도 | 실제 API로 아직 검증 안 됨 → **가장 먼저 smoke_test** |
| 디자인 (25) | 게이지, 하이라이트, 전후 비교, 채팅 UI 뼈대 | 기본 화면 수준. 디자인 담당이 `web/style.css` 변수부터 교체 |
| AI 활용 (20) | 기능마다 다른 모델·호출 조합, 토큰 탭으로 사용량 시각화 | 프롬프트 품질이 결과를 좌우 → 프롬프트 담당 시간 확보 |
| 크레딧 | 모든 호출 기록, 캐시, 한도 | "많이 쓸수록 좋은지 / 아낄수록 좋은지" **운영진에게 확인** |

### 1-2. 리스크

1. **주제 불일치**: 당일 주제가 "관계 메시지"와 멀 수 있음 → 2장의 유연성 범위 안에서 바꾸고, 범위를 넘으면 5장 방식으로 기능 추가
2. **응답 속도**: HCX-007은 추론 모델이라 느릴 수 있음. 캡처 해석은 2번 호출이라 더 느림 → 데모 입력은 미리 한 번 실행해 캐시를 채워 두기
3. **데모 중 API 실패**: 네트워크·한도 문제 → `.env`에서 `MOCK_MODE=1`로 바꾸면 즉시 화면 시연 가능 (결과에 `[MOCK]` 표시됨)
4. **규정**: 사전 제작 코드 반입 가능 여부 확인 필요

### 1-3. 유연성 평가: 어디까지 "파일만" 바꿔서 되나

| 바꾸고 싶은 것 | 지금 가능? | 방법 |
|---|---|---|
| 서비스 이름, 타깃, 관계·목적·격식 목록, 시나리오 | ✅ 파일만 | `customize/domain.yaml` |
| AI에게 주는 지시문 | ✅ 파일만 | `customize/prompts/*.md` |
| AI 결과 형식 (필드 추가) | ✅ 파일만 (화면 표시는 JS 수정) | `customize/schemas/*.json` + `web/app.js` |
| 참고 자료 | ✅ 파일만 | `customize/knowledge/*.md` |
| 모델·주소·한도 | ✅ 파일만 | `.env` |
| **새 프롬프트 변수** (`{level}` 같은 것) | ⚠️ 코드 1곳 | `app/services/common.py`의 `base_values()` |
| **temperature, max_tokens** | ⚠️ 코드 | 각 `app/services/*.py`의 호출 인자 |
| **스키마 필드 이름 변경** (예: `revised` → `rewritten`) | ⚠️ 코드 몇 곳 | 6장 "코드가 의존하는 필드" 참고 |
| **완전히 새 기능** (예: 퀴즈) | ❌ 코드 5곳 | 5장 따라 하기 |

### 1-4. 유연성을 더 높이는 개선안 (아직 구현 안 함, 결정 필요)

| 개선안 | 효과 | 작업량 |
|---|---|---|
| A. **domain.yaml `variables:` 자동 주입**: yaml에 적은 값이 모든 프롬프트 `{변수}`로 자동 등록 | 새 변수 추가에 코드 수정 불필요 | 작음 |
| B. **기능별 모델 설정을 domain.yaml로**: `features.coach.temperature` 같은 식 | temperature·max_tokens를 파일로 조절 | 작음 |
| C. **범용 기능 실행기 `/api/run/{기능}`**: 프롬프트+스키마 파일만 추가하면 새 기능 API가 생김 | 당일 새 기능을 코드 없이 추가 | 중간 |
| D. **화면 자동 렌더러**: 모르는 스키마 결과도 화면에 카드로 자동 표시 | C와 짝. 스키마 바꿔도 화면이 안 깨짐 | 중간 |

> 추천: **A → B → C → D** 순서. A와 B는 금방 끝나고 바로 효과가 있습니다.

---

## 2. 전체 구조 한눈에

```
[브라우저 web/]  ──HTTP──▶  [routes/]  ──▶  [services/]  ──▶  [hcx/client.py]  ──▶  HyperCLOVA X
                            입력 검사        로직 조립          유일한 API 창구
                                              │  ▲
                                              ▼  │
                            [customize/]  프롬프트·스키마·도메인·자료  (요청마다 다시 읽음)
                            [memory.py, rehearsal_store.py]  SQLite (data/app.sqlite3)
                            [services/rag.py]  임베딩 검색 (data/rag_index_*.json)
```

| 폴더/파일 | 한 줄 역할 | 당일에 고칠 일 |
|---|---|---|
| `.env` | 키, 모델명, 한도 | 키 넣기, `MOCK_MODE=0` |
| `customize/` | 서비스 성격 | **대부분 여기서 끝** |
| `web/` | 데모 화면 | 디자인, 스키마 바뀌면 표시 부분 |
| `app/services/` | 기능 로직 | 새 변수, 새 기능, 파라미터 |
| `app/routes/` | API 주소와 입력 형식 | 새 기능, 새 입력 필드 |
| `app/hcx/` | HCX 호출 | 거의 없음 (API 사양이 다를 때만) |
| `app/main.py` | 라우터 등록 | 새 기능 추가 시 1줄 |

---

## 3. 요청 하나가 처리되는 과정 (코칭 예시)

`POST /api/coach {"text": "교수님 과제 늦게 내도 돼요?", "relation": "professor", "contact_id": 1}`

| 순서 | 파일 · 함수 | 하는 일 |
|---|---|---|
| 1 | `routes/coach.py` `post_coach()` | `CoachRequest`로 입력 검사 (글자 수 등) |
| 2 | `services/coach.py` `coach()` | 아래 3~6을 순서대로 호출 |
| 3 | `services/common.py` `find_contact()` | contact_id → DB에서 상대 찾기 (없으면 404) |
| 4 | `services/common.py` `prepare()` | ① `base_values()`: domain.yaml에서 관계·목적·격식 꺼내 변수 dict 생성 ② 상대 있으면 `{memory}` 채움 ③ `knowledge.search()`로 `{references}` 채움 |
| 5 | `customize.py` `prompt("coach", **values)` | `prompts/coach.md` 읽고 `{변수}` 채움 |
| 6 | `hcx/client.py` `chat_json()` | HCX-007 Structured Outputs 호출 → JSON 검증 → 사용량 기록 |
| 7 | `services/highlight.py` `locate_spans()` | `issues[].quote`를 원문에서 찾아 `start/end` 추가 |
| 8 | `services/common.py` `remember()` | 상대 있으면 이번 기록 DB 저장 |
| 9 | → 응답 | `{original, scores, issues, revised, summary, references, meta}` |

**다른 기능도 모양이 같습니다.** `prepare()` → `prompt()` → `hcx.chat_json()` → (후처리) → `remember()`.
작성(`compose.py`)은 7번이 없고, 해석(`interpret.py`)은 앞에 `read_image()`가 붙고, 리허설은 대화 중엔 `chat()`·끝날 때 `chat_json()`을 씁니다.

---

## 4. 수정 지도: "이걸 바꾸려면 여기"

### 4-1. 파일만 고치면 되는 것

| 바꾸고 싶은 것 | 파일 | 위치 |
|---|---|---|
| 서비스 이름, 타깃 | `customize/domain.yaml` | `service:` |
| 관계 선택지 추가 | `customize/domain.yaml` | `relations:`에 `- id/label/formality/note` 추가 |
| 목적 선택지 | `customize/domain.yaml` | `purposes:` |
| 격식 단계 | `customize/domain.yaml` | `formality_levels:` (관계의 `formality`가 이 id를 가리킴) |
| 리허설 시나리오 | `customize/domain.yaml` | `scenarios:` (`opening` 쓰면 AI가 먼저 말함) |
| 참고 자료 개수, 기억할 기록 수, 리허설 기억 길이 | `customize/domain.yaml` | `settings:` (`rag_top_k`, `memory_recent`, `rehearsal_window`) |
| AI 지시문 | `customize/prompts/{기능}.md` | 전체. 맨 위 `<!-- -->`는 메모(모델에 안 감) |
| AI 결과에 필드 추가 | `customize/schemas/{기능}.json` | `properties`에 추가, 필수면 `required`에도 |
| 참고 자료 | `customize/knowledge/새파일.md` | `## 제목` 하나 = 검색 단위 하나 |
| 모델 바꾸기 | `.env` | `MODEL_ANALYSIS`, `MODEL_VISION`, `MODEL_LIGHT` |
| 한도 | `.env` | `MAX_LIVE_CALLS`, `TOKEN_STOP_THRESHOLD`, `CACHE_TTL_SECONDS` |
| 색상 | `web/style.css` | 맨 위 `:root { --primary ... }` |

> customize 파일은 **저장하면 바로 반영**됩니다 (서버 재시작 불필요). `.env`와 `.py` 파일은 재시작이 필요합니다 (`start.ps1`은 `--reload`라 `.py`는 자동 재시작).

### 4-2. 코드를 조금 고쳐야 하는 것

| 바꾸고 싶은 것 | 파일 | 할 일 |
|---|---|---|
| 새 프롬프트 변수 `{x}` (모든 기능 공통) | `app/services/common.py` `base_values()` | return dict에 `"x": 값` 추가 |
| 새 변수 (한 기능만) | `app/services/{기능}.py` | `values["x"] = 값`을 `prompt()` 호출 전에 추가 |
| 관계 항목에 새 키 (예: `honorific`) | yaml에 키 추가 + `base_values()`에 `"relation_honorific": rel.get("honorific", EMPTY)` | |
| temperature / max_tokens | `app/services/{기능}.py` | `chat_json(..., temperature=0.3, max_tokens=3000)` |
| 요청에 새 입력 필드 (예: `deadline`) | `app/routes/{기능}.py` Request 클래스 + `services/{기능}.py` 인자 + 변수로 넘기기 | 3곳 |
| 화면에 새 결과 필드 표시 | `web/app.js`의 `runCoach()` 등 | 템플릿 문자열에 `${esc(r.새필드)}` 추가 |
| 기록(메모리)에 남길 내용 | `app/services/{기능}.py`의 `remember(...)` 마지막 인자 | |
| 캐시 끄기 (매번 새 결과) | `chat_json(..., use_cache=False)` 또는 temperature > 0 | |
| 자유 입력 분류 대상 기능 | `app/services/router.py` `FEATURES` + `prompts/route.md` | |

### 4-3. 거의 안 건드리는 것 (API 사양이 다를 때만)

| 상황 | 파일 | 위치 |
|---|---|---|
| API 주소가 다름 | `.env` `CLOVA_BASE_URL` | |
| 경로가 다름 | `app/hcx/client.py` 맨 위 | `CHAT_PATH`, `EMBED_PATH` |
| 토큰 파라미터 이름이 다름 | `app/hcx/client.py` | `COMPLETION_TOKEN_MODELS` (`maxCompletionTokens` 쓰는 모델 목록) |
| 429 재시도 간격 | `app/hcx/client.py` | `RETRY_DELAYS` |
| 스키마 지원 키워드가 다름 | `app/hcx/schema.py` | `SUPPORTED_KEYS` |
| 이미지 크기 제한 | `app/hcx/image.py` | `MAX_BYTES`, `MAX_SIDE` |

---

## 5. 새 기능 추가 따라 하기 (예: "퀴즈")

주제가 "교육"이라 "관계 표현 퀴즈"를 만든다고 가정합니다. 기존 `compose`를 복사하면 됩니다.

**① 프롬프트** `customize/prompts/quiz.md`
```markdown
<!-- 사용 가능 변수: {target} {relation} {formality} {references} {memory} -->
너는 {target}을 위한 한국어 선생님이다. {relation}에게 쓰는 표현으로 퀴즈를 만들어라.

[참고 자료]
{references}
```

**② 스키마** `customize/schemas/quiz.json`
```json
{
  "type": "object",
  "properties": {
    "questions": {
      "type": "array", "minItems": 1, "maxItems": 5,
      "items": {
        "type": "object",
        "properties": {
          "question": {"type": "string"},
          "choices": {"type": "array", "items": {"type": "string"}},
          "answer": {"type": "integer", "minimum": 0, "maximum": 3}
        },
        "required": ["question", "choices", "answer"]
      }
    }
  },
  "required": ["questions"]
}
```

**③ 서비스** `app/services/quiz.py`
```python
"""퀴즈 생성."""
from .common import meta, prepare


async def quiz(core, topic: str, relation: str | None = None) -> dict:
    values, refs = await prepare(core, topic, relation)          # 변수 + 참고 자료
    system = core.customize.prompt("quiz", **values)             # quiz.md 채우기
    result = await core.hcx.chat_json("quiz", system, topic,     # "quiz"는 토큰 탭에 보일 기능명
                                      core.customize.schema("quiz"))
    return {**result.data, "references": refs, "meta": meta(result)}
```

**④ 라우트** `app/routes/quiz.py`
```python
"""POST /api/quiz"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ..core import Core
from ..deps import get_core, require_team_key
from ..services.quiz import quiz

router = APIRouter(prefix="/api", tags=["quiz"], dependencies=[Depends(require_team_key)])


class QuizRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=500)
    relation: str | None = None


@router.post("/quiz")
async def post_quiz(body: QuizRequest, core: Core = Depends(get_core)):
    return await quiz(core, body.topic, body.relation)
```

**⑤ 등록** `app/main.py`
```python
from .routes import coach, contacts, domain, health, messages, quiz, rehearsal, system
...
    app.include_router(quiz.router)
```

**⑥ 확인**: http://127.0.0.1:8000/docs 에 `POST /api/quiz`가 생깁니다. MOCK 모드에서도 스키마대로 가짜 결과가 나옵니다.

**⑦ 화면**: `web/index.html`에 탭 버튼과 `<section id="tab-quiz">` 추가, `web/app.js`에 `runQuiz()` 추가 (기존 `runCompose()` 복사).

**⑧ 테스트** (선택): `tests/test_messages.py`의 `test_compose_mock...`을 복사해 주소만 바꾸기.

---

## 6. 레퍼런스

### 6-1. 프롬프트 변수 전체 목록

| 변수 | 값의 출처 | 쓸 수 있는 프롬프트 |
|---|---|---|
| `{service_name}` | domain.yaml `service.name` | 전부 |
| `{target}` | domain.yaml `service.target` | 전부 |
| `{relation}` | 선택한 관계의 `label` (상대 지정 시 상대의 관계) | 전부 |
| `{relation_note}` | 관계의 `note` | 전부 |
| `{purpose}` | 선택한 목적의 `label` | compose, coach |
| `{formality}` | 관계의 `formality` → formality_levels의 `label - description` | 전부 |
| `{references}` | knowledge 검색 결과 상위 k개 | compose, coach, interpret |
| `{memory}` | 상대 프로필 + 최근 기록 | compose, coach, interpret, rehearsal_role |
| `{ai_role}` `{scenario_title}` `{situation}` `{goal}` | 시나리오 항목 | rehearsal_role, rehearsal_feedback |
| `{features}` | `router.py`의 FEATURES | route |

- 값이 없으면 `(없음)`이 들어갑니다.
- 프롬프트에 **목록에 없는 `{변수}`**를 쓰면 채워지지 않고 글자 그대로 남습니다 (오류는 안 남). → 프롬프트를 고친 뒤 결과가 이상하면 `{...}`가 그대로 갔는지 의심하세요.
- 사용자 입력(메시지 원문)은 변수가 아니라 **user 메시지로 따로** 전달됩니다.

### 6-2. 기능별 사용 파일·모델·파라미터

| 기능 | 프롬프트 | 스키마 | 모델 | temperature | 캐시 |
|---|---|---|---|---|---|
| compose | compose.md | compose.json | HCX-007 | 0.5 | ✗ |
| coach | coach.md | coach.json | HCX-007 | 0 | ✓ |
| interpret | ocr.md → interpret.md | interpret.json | HCX-005 → HCX-007 | 0 | ✓ |
| rehearsal 대화 | rehearsal_role.md | — | HCX-DASH-002 | 0.7 | ✗ |
| rehearsal 종료 | rehearsal_feedback.md | rehearsal_feedback.json | HCX-007 | 0 | ✓ |
| route | route.md | — | HCX-DASH-002 | 0 | ✓ |
| RAG | — | — | 임베딩 v2 | — | ✓ + JSON 파일 |

### 6-3. 코드가 의존하는 스키마 필드 (이름을 바꾸면 같이 고칠 곳)

필드를 **추가**하는 건 자유입니다. 아래 필드의 **이름을 바꾸거나 지우면** 오른쪽도 수정하세요.

| 스키마 | 필드 | 백엔드 의존 | 화면(web/app.js) 의존 |
|---|---|---|---|
| coach.json | `issues[].quote` | `coach.py`, `highlight.py` (하이라이트 위치 계산) | `highlight()`, `runCoach()` |
| coach.json | `revised` | `coach.py` (메모리 기록) | `runCoach()` 전후 비교 |
| coach.json | `scores.*`, `summary`, `issues[].problem/suggestion/severity` | — | `runCoach()` |
| compose.json | `draft` | `compose.py` (메모리 기록) | `runCompose()` |
| compose.json | `notes` | — | `runCompose()` |
| interpret.json | `intent` | `interpret.py` (메모리 기록) | `runInterpret()` |
| interpret.json | `emotion`, `urgency`, `key_points`, `reply_draft` | — | `runInterpret()` |
| rehearsal_feedback.json | `summary` | `rehearsal.py` (메모리 기록) | `endRehearsal()` |
| rehearsal_feedback.json | `overall_score`, `scores.*`, `goal_achieved`, `good_points`, `improvements[]` | — | `endRehearsal()` |

### 6-4. 스키마 작성 규칙 (HCX-007 Structured Outputs)

- 쓸 수 있는 키워드: `type, properties, required, items, enum, anyOf, format, minimum, maximum, minItems, maxItems`
- 그 외 키워드(`pattern`, `description`, `additionalProperties` 등)는 **전송 전에 자동으로 지워집니다** (`app/hcx/schema.py`)
- MOCK 모드 가짜 값 규칙: 숫자는 범위의 70% 지점, 배열은 `minItems`개(최소 1개), enum은 첫 번째 값, 문자열은 `[MOCK] 필드명`

### 6-5. API 요청 형식

| API | 입력 |
|---|---|
| `POST /api/compose` | `{"key_points", "relation"?, "purpose"?, "contact_id"?}` |
| `POST /api/coach` | `{"text", "relation"?, "purpose"?, "contact_id"?}` |
| `POST /api/interpret` | form-data: `text`?, `image`?(파일), `relation`?, `contact_id`? |
| `POST /api/rehearsal/start` | `{"scenario_id", "contact_id"?}` |
| `POST /api/rehearsal/{id}/message` | `{"text"}` |
| `POST /api/rehearsal/{id}/end` | — |
| `POST /api/route` | `{"text"}` |
| `/api/contacts` | GET 목록, POST `{"name", "relation"?, "profile"?}`, PUT·DELETE `/{id}` |

모든 응답에 `meta: {calls: [{model, mock, cached, total_tokens, latency_ms}], total_tokens}`가 붙습니다.

---

## 7. 문제가 생겼을 때

| 증상 | 원인 | 확인할 곳 |
|---|---|---|
| `customize 설정 오류: ... 파일이 없습니다` | 프롬프트/스키마 파일 이름 오타 | `customize/` 파일명 = 코드의 `prompt("이름")` |
| `domain.yaml 형식 오류` | yaml 들여쓰기·콜론 | 탭 대신 스페이스 2칸, `- id:` 정렬 |
| `AI 결과가 지정한 JSON 형식과 다릅니다` | 모델이 스키마를 못 지킴 | 스키마를 단순하게, 프롬프트에 필드 설명 추가 |
| `JSON 출력이 토큰 한도에서 잘렸습니다` | 출력이 너무 김 | 서비스의 `max_tokens` 늘리기, `maxItems` 줄이기 |
| `HCX HTTP 401` / `403` | 키 오류 / 모델 권한 없음 | `.env` 키, 운영진에게 모델 권한 확인 |
| `HCX HTTP 400 (...)` | 요청 형식 오류 | 괄호 안 메시지 확인 → 대부분 스키마나 파라미터 문제 |
| `호출 횟수 한도(MAX_LIVE_CALLS)에 도달` | 한도 초과 | `.env` 값 올리기 (실제 사용량은 콘솔에서도 확인) |
| 프롬프트를 바꿨는데 결과가 같음 | **캐시** | 같은 입력 + temperature 0 → 캐시. `data/hcx_cache.sqlite3` 지우거나 입력을 바꿔 확인 |
| 하이라이트가 안 됨 (`start: null`) | 모델이 원문을 그대로 안 베낌 | 프롬프트에 "quote는 원문 그대로 복사" 강조 |
| 결과에 `{references}` 글자가 그대로 보임 | 변수 이름 오타 | 6-1 목록과 비교 |

**로그 보는 곳**
- 서버 터미널 창: 요청·오류
- `data/usage_log.jsonl`: HCX 호출마다 기능·모델·토큰·지연·오류
- http://127.0.0.1:8000/docs: API를 직접 눌러 보기
- `GET /api/knowledge/search?q=...`: RAG가 무엇을 찾는지

---

## 8. 당일 체크리스트

**주제 공개 직후 (1시간)**
- [ ] 주제와 서비스 연결 문장 정하기 → domain.yaml `service`
- [ ] 5개 기능 중 데모에 쓸 2~3개 고르기 (전부 보여 주려 하지 않기)
- [ ] 새 기능이 필요한지 판단 → 필요하면 5장

**구현 (반나절)**
- [ ] `.env` 키 입력 → `smoke_test.py` 통과
- [ ] `Select-String -Path customize\*, customize\*\*, web\* -Pattern "TODO\(DAY-OF\)"`로 채울 곳 확인
- [ ] domain.yaml: 관계·목적·시나리오 채우기
- [ ] prompts: 기능별 지시문 작성 (프롬프트 담당 원고 붙여 넣기)
- [ ] knowledge: 자료 넣기 → `/api/knowledge/search`로 검색 확인
- [ ] 스키마 필드를 바꿨다면 6-3 표대로 같이 수정

**점검 (2시간)**
- [ ] 대표 입력 3개씩: 잘 되는 것 / 애매한 것 / 실패하는 것
- [ ] 토큰 탭에서 기능별 사용량 확인
- [ ] `pytest -q` 통과 확인

**시연 준비**
- [ ] 시연용 상대 프로필 미리 등록
- [ ] 시연 입력을 한 번씩 미리 실행 (캐시 → 시연 때 빠름)
- [ ] 비상시 `MOCK_MODE=1` 전환 연습

---

## 9. 내가 직접 익혀 두면 좋은 순서

1. `customize/` 파일 고치고 화면에서 결과 바뀌는 것 확인 (코드 0줄)
2. `app/services/compose.py` 읽기 (13줄, 기능 하나의 전체 흐름)
3. `app/services/common.py`의 `base_values()`에 변수 하나 추가해 보기
4. 5장 따라 "퀴즈" 기능 직접 추가해 보기 (연습 후 삭제)
5. `app/hcx/client.py`의 `chat_json()` 읽기 (HCX 요청이 어떻게 생기는지)
