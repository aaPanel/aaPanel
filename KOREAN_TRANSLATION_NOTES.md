# aaPanel 한국어(kor) 번역 오류 수정 작업 노트

## 이 저장소는 무엇인가요?

[aaPanel/aaPanel](https://github.com/aaPanel/aaPanel) 공식 저장소를 그대로 가져온 뒤(shallow clone),
한국어 언어팩(`BTPanel/static/vite/lang/kor/`)에서 발견한 기계번역 오류와 어색한 표현을 수정한 작업본입니다.

**목적**: 최종적으로 [aaPanel/aaPanel](https://github.com/aaPanel/aaPanel)에 Pull Request로 제출해서
한국어 사용자 전체에게 개선된 번역이 반영되도록 하는 것입니다. 그 전 단계로 이 저장소(개인 Gitea)에서
작업 내용을 정리·관리합니다.

## 라이선스 관련

aaPanel의 `license.txt` 2.2조에 따라 "개인적으로 사용할 경우 저작권 표시를 유지하는 조건 하에
소스코드를 자유롭게 수정할 수 있다"고 명시되어 있으며, 이 작업은 그 범위 안에서 이루어졌습니다.
최종적으로는 공개 배포가 아니라 원 저장소에 기여(PR)하는 것이 목표입니다.

## 작업 완료 (2026-08-25 기준)

`BTPanel/static/vite/lang/kor/` 아래의 **모든 언어팩 파일(총 28개)**을 검수하고 수정했습니다.
(`utils.json`은 검수 결과 수정할 내용이 없어 원본 그대로 유지)

| 파일 | 화면 |
|---|---|
| `login.json` | 로그인 화면 |
| `layout.json` | 좌측 메뉴 / 하단 정보 |
| `account.json` | 계정 관리 |
| `home.json` | 대시보드 |
| `site.json` | 웹사이트 관리 |
| `utils.json` | (공통, 수정 없음) |
| `public.json` | 공통 UI 요소 |
| `password.json` | 비밀번호 관련 |
| `term.json` | 이용약관 |
| `monitor.json` | 모니터링 |
| `ftp.json` | FTP 관리 |
| `plugin.json` | 플러그인 관리 |
| `soft.json` | 소프트웨어 관리 |
| `site-node.json` | Node.js 사이트 |
| `component.json` | 컴포넌트 |
| `ssl.json` | SSL 인증서 |
| `crontab.json` | 예약 작업(크론) |
| `security.json` | 보안 개요 / 네트워크 스캔 |
| `database.json` | 데이터베이스 관리 |
| `wp.json` | WordPress 관리 |
| `mail.json` | 메일 서버 관리 |
| `config.json` | 패널 설정 |
| `docker.json` | Docker 관리 |
| `file.json` | 파일 관리 |
| `index.json` | 메인 화면 및 부가 기능(Node/Python/Go 프로젝트, AI 어시스턴트, 노드 관리 등) |
| `logs.json` | 로그 화면 |
| `waf.json` | WAF 방화벽 (가장 문제가 많았던 파일) |

**총 900개 이상 문구 수정.** (모든 커밋은 `git log`로 확인 가능)

참고로 `BTPanel/static/vite/lang/all/kor/` 아래에 있는 별도의 구형(레거시) 번역 시스템은
현재 실제로 서비스되지 않는 것으로 확인되어 이번 작업 범위에서 제외했습니다.

## 어떤 문제들이 있었나요?

기존 번역은 기계번역을 검수 없이 그대로 반영한 것으로 보이며, 아래와 같은 심각한 오류들이 있었습니다.

### 1. 완전한 오역 (단어를 문맥과 무관하게 직역)
| 원래 번역 | 실제 의미 | 원인 |
|---|---|---|
| 그물 | 네트워크(Network) | "net"을 물고기 잡는 그물로 오역 |
| 명확한 기억 | 메모리 비우기(Clear Memory) | "Clear"(명확한) + "Memory"(기억)로 단어별 직역 |
| 작곡가를 실행하세요 | Composer 실행 (PHP 패키지 매니저) | Composer를 음악 작곡가로 오역 |
| 상표 | 브랜드(인증서 발급기관) | "Brand"를 "상표"(Trademark)로 오역 |
| 힘 HTTPS | HTTPS 강제 적용 (Force HTTPS) | "Force"를 물리적 "힘"으로 오역 |
| 저축 | 저장(Save) | "Save"를 금전적 "저축"으로 오역 |
| 주사 | 인젝션(SQL Injection) | "Injection"을 의료용 "주사"로 오역 |
| 성냥 | 일치(Match) | "Match"를 성냥개비로 오역 |
| 교통 통제 | 트래픽 제한 | "Traffic"을 자동차 "교통"으로 오역 |
| 송금 도메인 | 전달되는 도메인 | "forwarded"를 금융 "송금"으로 오역 |
| 바람직한 것의 리스트 | 화이트리스트(Whitelist) | "White"를 "바람직한"으로 의역 |
| 팬 도메인 | (다중) 도메인 자동 통합 | "Multi/Fan-out"류 표현을 "팬(fan)"으로 오역 추정 |
| DENEY ACCESS | 접근 제한 삭제 | 영어 그대로 방치 + 오타(DENY→DENEY) |

### 2. 명령문으로 잘못 번역된 표(라벨)
디스크 I/O 통계표처럼 단순 항목명이어야 할 곳이 사용자에게 명령하는 문장으로 번역되어 있었습니다.
- "바이트를 읽으십시오" → "읽기 바이트"
- "대기를 작성하세요" → "쓰기 대기"
- "병합 카운트를 읽기" → "읽기 병합 횟수"

### 3. 논리가 반대로 번역된 경우
- 리버스 프록시 규칙 삭제 확인 메시지가 "규칙이 완전히 **유효해진다**"로 되어 있었음
  (삭제하는데 유효해진다는 것은 논리적으로 모순 — "완전히 사라진다"가 맞음)

### 4. nginx 설정 예시 코드 안에 번역어가 섞여 실제 문법이 깨진 경우
```
# 수정 전 (실행 불가능한 깨진 예시)
다시 작성 ^/blog/(. *) $/$ 1 휴식;

# 수정 후 (정상 nginx 문법)
rewrite ^/blog/(.*)$ /$1 break;
```

### 5. 영어가 그대로 방치된 곳
`Update`, `SetupTabs`, `validation`, `Batch`(리디렉션 활성화/비활성화), `404 Redirect` 설정 섹션 등
여러 곳에 문장 전체가 번역 없이 영어로 남아있던 것을 다수 발견해서 번역했습니다.

### 6. 띄어쓰기·문법 오류
"다시시작"→"다시 시작", "재설치 하시겠습니까"→"재설치하시겠습니까", "설장"(오타)→"설정" 등
한국어 맞춤법 오류가 전체적으로 매우 많았습니다.

### 7. 브랜드 표기 불일치
"Aapanel" → "aaPanel"로 통일 (공식 표기법)

## 불확실해서 원문 그대로 남겨둔 곳

아래는 명백히 어색하지만, 원본 영어/중국어 문자열 없이 추측하면 오히려 더 틀릴 위험이 있어
수정하지 않고 표시만 해두었습니다. 원저장소 관리자나 원문 확인이 가능한 분의 확인이 필요합니다.

- `site.json` → `Proxy.index_22`: `"대사"`
- `site.json` → `Label.index_49, 51, 52`: `"효과 : 의지"`, `"~을 위한"`, `"게다가"`

## 다음 단계

1. ~~남은 언어팩 파일 수정~~ (완료, 2026-08-25)
2. [aaPanel/aaPanel](https://github.com/aaPanel/aaPanel)에 Pull Request 제출
   (선례: [독일어 번역 PR #1](https://github.com/aaPanel/aaPanel/pull/1))
   - GitHub 계정 준비 필요 (PR 작성자 본인 계정으로)
   - aaPanel/aaPanel을 GitHub에서 fork → 이 저장소의 변경 내용을 fork에 반영 → PR 생성
