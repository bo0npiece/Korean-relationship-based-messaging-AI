# customize/ — 당일 교체 영역

코드를 고치지 않고 이 폴더의 파일만 바꿔서 서비스 성격을 바꿉니다. 요청이 올 때마다 다시 읽으므로(Step 3) 서버를 재시작할 필요가 없습니다.

| 경로 | 내용 | 만드는 단계 |
|---|---|---|
| `domain.yaml` | 서비스명, 타깃, 관계·목적 목록, 격식 단계, 리허설 시나리오 | Step 3 |
| `prompts/*.md` | 시스템 프롬프트. `{변수}` 자리를 채우는 방식 | Step 3~ |
| `schemas/*.json` | Structured Outputs용 JSON 스키마 | Step 3~ |
| `knowledge/*.md` | RAG 검색 자료. `## 제목` 단위로 쪼갬 | Step 6 |

<!-- TODO(DAY-OF): 주제가 공개되면 이 폴더의 내용을 교체 -->
