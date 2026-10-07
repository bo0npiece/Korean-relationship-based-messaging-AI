# 한국어 관계 기반 메시지 코치 — 백엔드

외국인 유학생이 교수님·선배·알바 사장님 등 상대와의 관계에 맞는 한국어 메시지를 쓰고 코칭받는 서비스의 백엔드입니다. HyperCLOVA X(CLOVA Studio) API만 사용합니다.

> 범용 해커톤 백엔드(`tasks.json` 방식)는 `main` 브랜치에 그대로 있습니다. 이 브랜치(`feature/message-coach`)에서 새 구조로 재구성 중입니다.

## 구조

```
app/            엔진 — 당일엔 거의 안 건드림
  config.py     .env → Settings
  deps.py       공통 의존성 (설정 꺼내기, 팀 키 검사)
  main.py       FastAPI 앱 조립
  routes/       API 라우트
  hcx/          HCX 호출 창구 (Step 2)
  services/     기능별 로직 (Step 4~)
customize/      당일 교체 영역 — 파일만 바꿔서 서비스 성격 변경
scripts/        실행 스크립트
tests/          pytest
data/           로그·DB (Git 제외)
```

## 실행 (Windows PowerShell)

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start.ps1
```

처음 실행하면 `.venv` 생성, 패키지 설치, `.env` 복사가 자동으로 됩니다. 브라우저에서 http://127.0.0.1:8000/docs 를 엽니다.

실제 API를 호출하려면 `.env`에 `CLOVA_API_KEY`를 넣고 `MOCK_MODE=0`으로 바꿉니다. 키가 비어 있으면 `MOCK_MODE` 값과 상관없이 MOCK으로 동작합니다.

## 테스트

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest -q
```
