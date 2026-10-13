# 동화 애니메이션 자동 제작 (3~8세)

동화 대본(JSON) 하나로 한국어·영어 애니메이션 영상, 썸네일, 자막, 유튜브 메타데이터를 만들고 업로드합니다.

```
stories/NNN_이름.json  →  render.py  →  out/NNN_이름_{ko,en}.mp4 / _thumb.jpg / .srt / .json  →  youtube.py upload
```

## 설치

```bash
bash setup.sh
```

## 제작

```bash
python3 render.py stories/001_toto_rainbow_umbrella.json            # 한국어 + 영어, 1080p
python3 render.py STORY --lang ko --res 1280x720 --preview 20        # 빠른 미리보기
```

음성: `GOOGLE_TTS_API_KEY`가 있으면 Google Cloud TTS(자연스러운 음성), 없으면 espeak-ng(미리보기용 기계음)를 씁니다.

## 업로드 준비 (최초 1회)

1. Google Cloud 콘솔에서 프로젝트를 만들고 **YouTube Data API v3**와 **Cloud Text-to-Speech API**를 켭니다.
2. OAuth 동의 화면을 만들고 본인 계정을 테스트 사용자로 추가한 뒤, **게시 상태를 "프로덕션"으로** 바꿉니다
   (테스트 상태면 토큰이 7일마다 만료됩니다).
3. 사용자 인증 정보 → OAuth 클라이언트 ID → **데스크톱 앱**을 만들어 클라이언트 ID/보안 비밀을 받습니다.
4. 사용자 인증 정보 → API 키를 만들고 Text-to-Speech API로 제한합니다.
5. 토큰 발급:
   ```bash
   export YT_CLIENT_ID=... YT_CLIENT_SECRET=...
   python3 youtube.py auth-url          # 출력된 주소를 열어 승인 → localhost 주소로 이동(페이지 오류는 정상)
   python3 youtube.py exchange "<주소창의 전체 URL>"
   ```
6. 환경 변수 `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`, `GOOGLE_TTS_API_KEY`를 클라우드 환경 설정에 저장합니다.

```bash
python3 youtube.py upload out/001_toto_rainbow_umbrella_ko.json --privacy private
```

심사(audit)를 받지 않은 API 프로젝트로 올린 영상은 유튜브가 **비공개로 고정**합니다.
YouTube Studio에서 확인한 뒤 직접 공개로 바꾸세요. 모든 영상은 "아동용(Made for Kids)"으로 올라갑니다.

## 동화 JSON 형식

```jsonc
{
  "id": "002_short_name",            // 파일 이름과 같게
  "seed": 2,                          // 배경음악 변주
  "title":   {"ko": "...", "en": "..."},
  "summary": {"ko": "...", "en": "..."},
  "moral":   {"ko": "...", "en": "..."},
  "tags":    {"ko": ["..."], "en": ["..."]},
  "thumbnail": {"scene": 3, "t": 3.0},  // 썸네일로 쓸 장면/시점(초)
  "scenes": [{
    "bg": "meadow | forest | riverside | snowfield",
    "sky": "day | cloudy | sunset | night", "sky_to": "(선택) 장면 중 하늘 전환",
    "weather": "none | rain | snow | sparkle", "weather_ramp": [시작, 끝],  // 0~1 진행도, 끝<시작이면 그침
    "rainbow": false,
    "zoom": [1.0, 1.05], "focus": [640, 420],
    "card": {"ko": "큰 제목 글자", "en": "..."}, "card_sub": {...}, "hide_subtitles": false,
    "min_duration": 3,
    "props": [{"type": "leaf|gift|puddle|apple|star|flower|house", "x": 800, "y": 600, "scale": 1, "z": "back|front"}],
    "actors": [{
      "char": "bunny | bear | squirrel | duck | fox | cat",
      "id": "(선택) 같은 동물이 둘일 때 구분용, lines의 who와 매칭",
      "x": 640 또는 [시작x, 끝x], "move": [0, 1], "y": 610, "scale": 1, "face": 1 또는 -1,
      "action": "idle | walk | hop | jump | shiver",
      "arms": "down | up | wave | hug | umbrella", "mood": "happy | sad | surprised",
      "umbrella": {"width": 260, "top": -280},   // 무지개 우산을 든 경우
      "palette": {"fur": "#hex", "belly": "#hex"}, "z": 0, "shadow": true, "appear": 0
    }],
    "lines": [{"who": "narrator 또는 actor id", "mood": "(선택)", "ko": "...", "en": "..."}]
  }]
}
```

화면 좌표는 1280×720 기준이고 땅은 y≈560~620입니다. 한 편에 장면 10~12개, 대사 30줄 안팎이면 약 3~4분입니다.

## 채널 운영 원칙

- 3~8세 눈높이: 짧은 문장, 쉬운 단어, 반복 구조, 무섭거나 폭력적인 내용 없음, 따뜻한 결말과 교훈 한 가지.
- 매번 새로운 이야기·주제·캐릭터 조합 (반복 대량생산 콘텐츠는 수익화가 제한됩니다).
- 올린 이야기는 `published.md`에 기록해 겹치지 않게 합니다.
