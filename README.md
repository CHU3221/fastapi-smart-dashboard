# FastAPI Smart Dashboard

로컬 환경에서 동작하는 프라이버시 중심의 개인용 통합 알림 대시보드입니다.  
iCal, IMAP, YouTube RSS, 치지직 라이브 감시 등을 하나의 화면에서 관리할 수 있습니다.

![Dashboard Preview](https://raw.githubusercontent.com/CHU3221/fastapi-smart-dashboard/main/docs/dashboard-preview.png)

---

## 소개

이 프로젝트는 사용자가 일상적인 일정 및 필수 알림을 한눈에 파악할 수 있도록 설계된 로컬 기반 대시보드입니다.

외부 클라우드 서비스 의존도를 최소화하고, 홈 서버 및 개인 환경에서 빠르고 직관적으로 사용할 수 있도록 개발되었습니다.

주요 목표:

- Local-first 환경
- Privacy-focused 구조
- 실시간 알림 통합
- 간단한 설치 및 커스터마이징
- 브라우저 기반 접근성

---

## 목차

1. [주요 특징](#주요-특징)
2. [사용 기술](#사용-기술)
3. [실행 방법](#실행-방법)
4. [사용 방법](#사용-방법)
5. [SmartDashboard-Extension](#smartdashboard-extension)
6. [API 가이드](#api-가이드)
7. [개발자 가이드](#개발자-가이드)
8. [Known Issues](#Known-Issues)
9. [Credits & Open Source Licenses](#credits--open-source-licenses)

---

## 주요 특징

- 모든 데이터 로컬 저장 (SQLite 기반)
- 외부 클라우드 의존 최소화
- 실시간 알림 허브 통합
- YouTube RSS 감시
- 치지직 라이브 상태 감시
- Gmail / IMAP 알림 연동
- 타일 기반 UI 커스터마이징
- FastAPI 기반 비동기 백엔드
- 브라우저 기반 접근 지원

---

## 사용 기술

### Backend

- Python 3.11+
- FastAPI
- SQLite3
- httpx
- uvicorn

### Frontend

- Vanilla HTML
- CSS
- JavaScript

### Infra (배포 환경)

- `/backend`
  - Rocky Linux
  - Podman / Docker
  - 컨테이너 기반 실행

- `/app-desktop`
  - Windows / macOS
  - Standalone 실행 지원
  - `localhost:7600`

---

## 실행 방법

### 1. 컨테이너 환경 (`/backend`)

Podman 또는 Docker가 설치된 Linux 서버 환경에서 실행합니다.

```bash
cd backend

podman build -t smart-dashboard .

podman run -d \
  --name dashboard \
  -p 7600:7600 \
  -v $(pwd)/src:/src:Z \
  smart-dashboard
````

실행 후:

```text
http://SERVER_IP:7600
```

으로 접속합니다.

---

### 2. 데스크톱 환경 (`/app-desktop`)

Windows/macOS 환경에서 Python을 이용해 직접 실행하거나, 독립형 실행 파일(`.exe`)로 빌드하여 사용할 수 있습니다.

#### A. 소스 코드로 직접 실행
1. 필요한 라이브러리 설치:
   ```bash
   cd app-desktop
   pip install -r requirements.txt
  ```

2. 앱 실행:
  ```bash
  python main.py

  ```

3. 웹 브라우저에서 `http://localhost:7600`으로 접속합니다.

#### B. 실행 파일(.exe)로 빌드하여 사용 (Windows)

매번 터미널을 열기 번거롭다면, 단일 실행 파일로 만들어 사용할 수 있습니다.

1. **자동 빌드:** 폴더 내 제공된 `build_exe.bat` 파일을 실행하거나, 아래 명령어를 터미널에 입력합니다.
```bash
python -m PyInstaller --onefile --add-data "static;static" main.py

```
2. **결과물 확인:** 빌드가 완료되면 `dist` 폴더 안에 `main.exe` 파일이 생성됩니다.
3. **참고:** 빌드를 위해서는 Python 환경에 `pyinstaller` 및 관련 패키지가 설치되어 있어야 합니다.

---

## 사용 방법

대시보드 웹 페이지에서 각 타일을 클릭하여 환경설정을 변경할 수 있습니다.

현재 지원 기능:

### 시계

* 폰트 변경
* 색상 변경
* 콜론 / 한글 구분자 변경
* 12시간 / 24시간 형식 전환

### 날씨

* OpenWeatherMap API 연동
* 도시 지정 지원
* 예: `Seoul`, `Pohang`

### 캘린더

* iCal URL 연동
* 키워드 기반 자동 색상 라벨링

### 실시간 알림

* 치지직 방송 상태 감시
* YouTube 업로드 감시
* Gmail / IMAP 알림 연동

---

## SmartDashboard-Extension

브라우저 하단 오버레이 형태의 전용 내비게이션 확장 프로그램입니다.

### 작동 원리

버튼 클릭 시 브라우저에 열려 있는 탭들의 URL 패턴과 페이지 제목(Title)을 검사합니다.
조건에 맞는 탭이 존재하면 해당 탭으로 즉시 Focus 이동하며,
존재하지 않을 경우 아무 동작도 수행하지 않습니다.

### 지원 탭 라우팅

* SmartDashboard (사용자 지정 주소 기반)
* Discord (`discord.com`)
* Chzzk (`chzzk.naver.com`)
* YouTube (`youtube.com`)
* YouTube Music (`music.youtube.com`)

### 설치 및 설정 방법

이 확장 프로그램은 크롬 웹 스토어에 등록되지 않은 로컬 확장 프로그램이므로, 개발자 모드를 통해 설치해야 합니다.

**Step 1. 확장 프로그램 로드하기**
1. 크롬 브라우저 주소창에 `chrome://extensions/`를 입력하여 **확장 프로그램 관리 페이지**로 이동합니다.
2. 우측 상단의 **'개발자 모드(Developer mode)'** 스위치를 켭니다.
3. 좌측 상단의 **'압축해제된 확장 프로그램을 로드합니다(Load unpacked)'** 버튼을 클릭합니다.
4. 프로젝트 폴더 내의 `extension` 폴더를 선택하여 업로드합니다.

**Step 2. 대시보드 주소 연동하기 (필수)**
1. 브라우저 우측 상단의 퍼즐 조각 아이콘을 클릭하여 **'Smart Dashboard Controller'**를 찾습니다.
2. 해당 아이콘을 **우클릭**한 뒤 **[옵션]** 메뉴를 클릭합니다.
3. 설정 창이 열리면 본인이 구축한 대시보드의 접속 주소를 포트와 함께 입력합니다. 
   *(예: 로컬 PC 실행 시 `localhost:7600`, 홈 서버 실행 시 `192.168.1.200:7600` 등)*
4. **[저장하기]** 버튼을 누른 후, 대시보드 페이지로 돌아가 새로고침(F5)을 하면 하단에 오버레이 리모컨이 활성화됩니다.

---

## API 가이드

네트워크 내 다른 장치에서 Smart Dashboard로 알림을 전송할 수 있습니다.

### 기본 정보

| 항목           | 값                                       |
| ------------ | --------------------------------------- |
| Endpoint     | `http://[DASHBOARD_IP]:7600/api/notify` |
| Method       | `POST`                                  |
| Content-Type | `application/json`                      |

---

### Request Payload

수신된 `message`의 HTML 태그는 프론트엔드에서 그대로 렌더링됩니다.

| 필드명            | 타입     | 필수 여부 | 기본값       | 설명            |
| -------------- | ------ | ----- | --------- | ------------- |
| `source`       | String | 필수    | -         | 알림 카테고리       |
| `message`      | String | 필수    | -         | HTML 지원 알림 본문 |
| `border_color` | String | 선택    | UI 설정값    | 좌측 강조선 색상     |
| `bg_color`     | String | 선택    | `#1a1a1a` | 배경 색상         |

---

### cURL Example

```bash
curl -X POST http://[DASHBOARD_IP]:7600/api/notify \
-H "Content-Type: application/json" \
-d '{
  "source": "NAS_ALERT",
  "message": "🔥 <b>온도 경고</b>: CPU 온도가 <span style=\"color:#ff4444;font-weight:bold;\">85도</span>를 초과했습니다!",
  "border_color": "#FF0000",
  "bg_color": "#330000"
}'
```

---

## 개발자 가이드

> 이 API는 홈 네트워크 내부 사용을 전제로 설계되었습니다.
> 인터넷에 직접 포트포워딩하여 노출하는 것은 권장하지 않습니다.

### HTML 렌더링 주의

`message` 필드는 HTML 렌더링을 지원합니다.

따라서:

* 열린 태그는 반드시 닫아야 하며
* 잘못된 HTML 구조는 UI 깨짐을 유발할 수 있습니다.

---

### 데이터 저장 구조

전송된 알림은 내부 SQLite 데이터베이스(`dashboard.db`)에 저장됩니다.

* 전체 알림 영구 저장
* 화면에는 최신 15건 표시

---

### 확장 가능 API

다음 API 또한 동일한 방식으로 제어 가능합니다.

* `/api/channels`
* `/api/config`

---

## Known Issues

### YouTube 채널 감시 이슈 (26.05.08 ~ 26.05.10)

YouTube 서버의 Bot 차단으로 감시 대상 채널의 새로운 동영상 업로드의 감지가 어려운 상황입니다. (정상화 됨)

---

## Credits & Open Source Licenses

이 프로젝트는 다양한 오픈소스 프로젝트와 크리에이터들의 도움을 받아 제작되었습니다.

### Notification Sound

* Sound Effect by RingtoneGuy from Pixabay

### SmartDashboard-Extension

* Dashboard icon by chehuna from Flaticon

### Backend Framework

* FastAPI (MIT License)

### Core Libraries

* uvicorn (BSD 3-Clause)
* httpx (BSD 3-Clause)
* pydantic (MIT License)
* icalendar (BSD 2-Clause)
* recurring_ical_events (LGPL-3.0)

