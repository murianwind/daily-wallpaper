# daily-wallpaper

하루 두 번(낮/밤), 정선풍 진경산수화 스타일의 명승지 풍경을 AI로 생성해 GitHub Pages에 올리고,
아이폰 단축어가 그 이미지를 받아 잠금화면과 홈 화면 배경으로 바꿉니다.
이미지는 아이폰에 저장되지 않고 매번 내려받아 바로 적용됩니다.

```
GitHub Actions (Home Assistant 호출: 04:10 / 16:10 KST)
  명승지 선택 → 서울 날씨(Open-Meteo) → 프롬프트 조립
  → Cloudflare Workers AI 로 생성 (실패 시 최대 3회) → 1179x2556 JPEG → GitHub Pages(latest.jpg)
아이폰 단축어 자동화 (07:00 / 18:00) → latest.jpg 다운로드 → 배경화면 설정
```

- 화면은 항상 **회색조 수묵화**입니다(프롬프트에서 흑백 수묵을 요구하고, 후처리에서 한 번 더 회색조로 변환). 한지 테두리는 프롬프트로 막고, 그래도 생기는 가장자리는 사방 7%를 잘라 제거합니다(`EDGE_TRIM_RATIO`). **낮**: 밝고 옅은 먹색. **밤**: 짙은 먹빛, 달빛. 서울의 현재 날씨(맑음·흐림·안개·비·눈·뇌우)와 계절이 프롬프트에 반영됩니다.
- **명승지**: 아래 목록 중 실행할 때마다 무작위로 고릅니다(자동·수동 모두). 직전 실행들이 쓴 명승지 최근 20곳(목록의 절반)은 피하므로, 낮/밤이나 수동 재실행에서도 겹치지 않습니다. 기록은 배포된 `latest.json` 의 `recent_spot_ids` 에 담겨 다음 실행이 읽어 갑니다(저장소 커밋 없음). 기록을 읽지 못하면 그 회차만 완전 무작위입니다. 생성 시드도 실행마다 무작위이고 `latest.json` 의 `seed` 에 남습니다.
- 날씨 조회가 실패해도 날씨 없이 생성합니다. 생성이 끝내 실패하면 이전 이미지를 그대로 두고, 디스코드 웹훅이 있으면 알립니다.

## 처음 설정

1. **저장소**: 이 폴더를 공개(public) GitHub 저장소로 올립니다.
2. **Cloudflare**: 무료 계정(카드 불필요)을 만들고 *계정 ID*와, Workers AI 권한이 있는 *API 토큰*을 발급합니다.
3. **GitHub Secrets** (Settings → Secrets and variables → Actions)
   - `CF_ACCOUNT_ID`, `CF_API_TOKEN` (필수)
   - `DISCORD_WEBHOOK_URL` (선택, 최종 실패 알림)
   - Variables 에 `WALLPAPER_MODEL` (선택, 기본값 `@cf/black-forest-labs/flux-2-klein-4b`)
4. **Pages**: Settings → Pages → Source 를 *GitHub Actions* 로 지정합니다.
5. **첫 실행**: Actions 탭 → wallpaper → *Run workflow* (slot: day). 성공하면
   `https://<사용자명>.github.io/<저장소명>/latest.jpg` 에서 이미지를 볼 수 있습니다.

> 첫 실행에서 꼭 확인할 것: (a) 이미지가 정상으로 받아지는지, (b) Cloudflare 대시보드의 Workers AI 사용량에서
> 한 장당 소모량이 무료 한도(하루 10,000 neurons) 대비 얼마인지. 응답 형식과 소모량은 공식 문서의 일부만
> 확인된 상태라 이 단계가 실측입니다. 한도는 매일 UTC 00:00(한국 09:00)에 초기화됩니다.

## 아이폰 단축어

1. 단축어 앱 → 새 단축어 → 이름 `AI 배경화면`
2. 액션을 순서대로 추가
   1. **현재 날짜** → **날짜 형식 지정** (사용자 지정: `yyyyMMddHHmm`)
   2. **텍스트**: `https://<사용자명>.github.io/<저장소명>/latest.jpg?t=` 뒤에 위 형식 지정 결과를 붙입니다. (`?t=` 는 캐시 방지용)
   3. **URL 콘텐츠 가져오기** (Get Contents of URL), 입력은 위 텍스트
   4. **배경화면 설정** (Set Wallpaper): 입력은 가져온 콘텐츠, 대상은 *잠금 화면과 홈 화면*,
      *미리 보기 보기*(Show Preview)와 *피사체 기준으로 자르기*(Crop to Subject)는 끕니다.
3. 자동화 탭 → 개인용 자동화 → *시간* → 매일 07:00 → 단축어 실행 → `AI 배경화면` → **즉시 실행** 으로 설정
4. 같은 방식으로 매일 18:00 자동화를 하나 더 만듭니다.

먼저 단축어를 수동으로 한 번 실행해 두 화면에 모두 적용되는지 확인하세요.

## 운영 메모

- 공개 저장소의 Actions 로그는 누구나 볼 수 있습니다. 코드는 URL·토큰·계정 ID를 로그에 남기지 않도록 작성되어 있습니다.
- 정시 실행은 GitHub `schedule` 이 아니라 **Home Assistant 가 `repository_dispatch` 로 호출**합니다.
  GitHub `schedule` 은 이 계정에서 3~7시간씩 늦어지는 것이 관찰되어 쓰지 않습니다(그래서 60일 비활동 자동
  중지 문제도 없습니다). 호출은 04:10(낮 그림), 16:10(밤 그림)이고 단축어는 05:00, 17:00 에 받아갑니다.
- 낮/밤은 호출 시각(한국 12시 이전이면 낮)으로 정해집니다. 수동 실행은 Actions 탭의 *Run workflow* 를 쓰세요.
- 호출이 빠지면(Home Assistant 가 꺼져 있었던 경우 등) 그 회차의 이미지는 갱신되지 않고 이전 이미지가 유지됩니다.

### Home Assistant 호출 설정

`configuration.yaml` 의 `rest_command` (토큰은 weather-calendar 용을 쓰려면 이 저장소 접근 권한이 필요합니다):

```yaml
rest_command:
  trigger_wallpaper_update:
    url: "https://api.github.com/repos/murianwind/daily-wallpaper/dispatches"
    method: POST
    headers:
      Authorization: !secret github_weather_token
      Accept: "application/vnd.github.v3+json"
    payload: '{"event_type": "wallpaper-update"}'
    content_type: "application/json"
```

자동화에는 `time` 트리거(`04:10:00`, `16:10:00`)와 `rest_command.trigger_wallpaper_update` 동작을 추가합니다.

## 바꾸는 방법

| 바꾸고 싶은 것 | 위치 |
|---|---|
| 명승지 추가/삭제/묘사 수정 | `data/spots.json` (`id`는 중복 불가, `visual`은 영어 시각 묘사). 최근 기록 반영 길이는 곳 수의 절반이라 자동으로 맞춰집니다 |
| 화풍, 계절·날씨·시간대 문구 | `src/wallpaper/prompt_builder.py` |
| 날씨 기준 지점(서울), 해상도, 모델, 재시도 횟수 | `src/wallpaper/config.py` |
| 생성 시각 | Home Assistant 자동화의 `time` 트리거 (워크플로에는 시각이 없음) |

FLUX 계열 모델은 "박연폭포" 같은 이름을 정확히 모를 수 있어서, 이름 대신 `visual` 의 영어 묘사로 장면을 그립니다.
결과는 실제 지형의 재현이 아니라 그 분위기의 산수화입니다. 묘사가 마음에 들지 않으면 `spots.json` 의 `visual` 만 고치면 됩니다.

## 개발

```
pip install -r requirements-dev.txt
python -m pytest          # BDD 시나리오 (tests/features/*.feature)
ruff check . && ruff format --check .
vulture src               # 데드코드 점검
```

모듈은 각각 한 가지 책임만 가집니다: `spot_selector`(선택) · `weather`(날씨) · `prompt_builder`(프롬프트) ·
`cf_client`(생성·재시도) · `image_post`(후처리) · `notifier`(알림) · `main`(조립).

## 출처 표기

- 날씨 데이터: [Open-Meteo.com](https://open-meteo.com/) (CC BY 4.0). 키 없이 쓰는 무료 API이고 비영리 개인 용도에 해당합니다.
- 이미지 생성: Cloudflare Workers AI, FLUX.2 [klein] (Black Forest Labs). 모델 약관은 Cloudflare 모델 페이지를 확인하세요.

## 명승지 목록

총 40곳 (낮/밤 하루 2곳씩 → 20일 주기)

| 명승지 | 지역 |
|---|---|
| 박연폭포 | 개성 |
| 총석정 | 통천 |
| 해금강 | 고성 |
| 만폭동 | 내금강 |
| 비로봉 | 금강산 |
| 삼부연 | 철원 |
| 구룡연 | 외금강 |
| 명경대 | 내금강 |
| 삼일포 | 고성 |
| 장안사 | 내금강 |
| 정양사 | 내금강 |
| 단발령 | 금강산 |
| 옥류동 | 외금강 |
| 만물상 | 외금강 |
| 상팔담 | 외금강 |
| 십이폭포 | 외금강 |
| 보덕암 | 내금강 |
| 시중대 | 통천 |
| 문암 | 고성 |
| 청간정 | 고성 |
| 낙산사 | 양양 |
| 경포대 | 강릉 |
| 죽서루 | 삼척 |
| 망양정 | 울진 |
| 월송정 | 울진 |
| 도담삼봉 | 단양 |
| 옥순봉 | 단양 |
| 구담봉 | 단양 |
| 사인암 | 단양 |
| 삼용추 | 포항 내연산 |
| 압구정 | 서울 한강변 |
| 인왕산 | 서울 |
| 북한산 | 서울 |
| 비선대 | 설악산 |
| 울산바위 | 설악산 |
| 마이산 | 진안 |
| 부용대 | 안동 |
| 월출산 | 영암 |
| 정방폭포 | 제주 |
| 성산일출봉 | 제주 |
