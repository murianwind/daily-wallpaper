Feature: 기상청 날씨 캘린더(weather.ics) 조회
  weather-calendar 가 만든 ics 의 오늘 시간별 예보에서 지금 시각의 날씨를 읽어 프롬프트에 쓸 상태로 바꾸고,
  읽지 못해도 이미지 생성을 막지 않는다.

  Scenario Outline: 기상청 날씨 표기를 상태로 분류한다
    When 날씨 표기 "<label>" 를 분류한다
    Then 분류 결과는 "<condition>" 이다

    Examples:
      | label    | condition     |
      | 맑음     | clear         |
      | 구름많음 | partly_cloudy |
      | 흐림     | overcast      |
      | 비       | rain          |
      | 소나기   | rain          |
      | 눈       | snow          |
      | 비/눈    | snow          |
      | 안개     | fog           |
      | 뇌우     | thunderstorm  |
      | 황사     | unknown       |

  Scenario Outline: 오늘 일정에서 지금 시각의 날씨를 읽는다
    Given 오늘(2026-11-23) 시간별 예보가 06시 흐림, 10시 비, 20시 흐림 이다
    When <hour>시에 날씨를 조회한다
    Then 조회한 날씨는 "<condition>" 이다

    Examples:
      | hour | condition |
      | 6    | overcast  |
      | 10   | rain      |
      | 15   | rain      |
      | 22   | overcast  |

  Scenario: 예보에 없는 시각이면 가장 가까운 시각의 값을 쓴다
    Given 오늘(2026-11-23) 시간별 예보가 06시 흐림, 10시 비, 20시 흐림 이다
    When 4시에 날씨를 조회한다
    Then 조회한 날씨는 "overcast" 이다

  Scenario: 긴 줄이 접힌 ics 도 읽는다
    Given 오늘(2026-11-23) 일정의 설명이 접힌 줄로 나뉘어 있다
    When 10시에 날씨를 조회한다
    Then 조회한 날씨는 "rain" 이다

  Scenario: 오늘 일정이 없으면 unknown 으로 처리한다
    Given ics 에 다른 날짜의 일정만 있다
    When 10시에 날씨를 조회한다
    Then 조회한 날씨는 "unknown" 이다

  Scenario: 연결 오류가 나면 unknown 으로 처리한다
    Given ics 요청이 연결 오류로 실패한다
    When 10시에 날씨를 조회한다
    Then 조회한 날씨는 "unknown" 이다

  Scenario: HTTP 오류 응답이면 unknown 으로 처리한다
    Given ics 가 HTTP 500 을 돌려준다
    When 10시에 날씨를 조회한다
    Then 조회한 날씨는 "unknown" 이다

  Scenario: 형식이 예상과 다르면 unknown 으로 처리한다
    Given ics 가 예상과 다른 내용을 돌려준다
    When 10시에 날씨를 조회한다
    Then 조회한 날씨는 "unknown" 이다

  Scenario: 설정된 주소에서 ics 를 받는다
    Given 오늘(2026-11-23) 시간별 예보가 06시 흐림, 10시 비, 20시 흐림 이다
    When 10시에 날씨를 조회한다
    Then 요청 주소는 설정의 weather.ics 주소이다
