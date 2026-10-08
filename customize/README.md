# customize/ — 당일 교체 영역

코드를 고치지 않고 이 폴더의 파일만 바꿔서 서비스 성격을 바꿉니다. 요청이 올 때마다 다시 읽으므로(Step 3) 서버를 재시작할 필요가 없습니다.

| 경로 | 내용 | 만드는 단계 |
|---|---|---|
| `domain.yaml` | 서비스명, 타깃, 관계·목적 목록, 격식 단계, 리허설 시나리오, 엔진 설정값 | Step 3 |
| `prompts/*.md` | 시스템 프롬프트. `{변수}` 자리를 채우는 방식. 맨 위 `<!-- -->` 주석은 모델에 안 보냄 | Step 3~ |
| `schemas/*.json` | Structured Outputs용 JSON 스키마 | Step 3~ |
| `knowledge/*.md` | RAG 검색 자료. `## 제목` 단위로 쪼갬. `_`로 시작하는 파일은 제외 | Step 6 |

| 기능 | 프롬프트 | 스키마 |
|---|---|---|
| ① 작성 | `compose.md` | `compose.json` |
| ② 코칭 | `coach.md` | `coach.json` |
| ③ 해석 | `interpret_ocr.md`(캡처 읽기) → `interpret.md` | `interpret.json` |
| ④ 리허설 | `rehearsal_role.md`(대화) → `rehearsal_feedback.md`(평가) | `rehearsal_feedback.json` |
| 자유 입력 분류 | `route.md` | — |

<!-- TODO(DAY-OF): 주제가 공개되면 이 폴더의 내용을 교체 -->
