Feature: 서울 날씨 조회 (Open-Meteo)
  날씨 코드를 프롬프트에 쓸 상태로 분류하고, 조회가 실패해도 이미지 생성을 막지 않는다.

  Scenario Outline: WMO 날씨 코드를 상태로 분류한다
    When 날씨 코드 <code> 를 분류한다
    Then 분류 결과는 "<condition>" 이다

    Examples:
      | code | condition     |
      | 0    | clear         |
      | 1    | partly_cloudy |
      | 2    | partly_cloudy |
      | 3    | overcast      |
      | 45   | fog           |
      | 48   | fog           |
      | 53   | rain          |
      | 65   | rain          |
      | 81   | rain          |
      | 73   | snow          |
      | 86   | snow          |
      | 95   | thunderstorm  |
      | 99   | thunderstorm  |
      | 123  | unknown       |

  Scenario: 날씨 코드가 없으면 unknown 으로 분류한다
    When 날씨 코드가 없는 상태를 분류한다
    Then 분류 결과는 "unknown" 이다

  Scenario: Open-Meteo 응답에서 날씨를 읽는다
    Given Open-Meteo가 날씨 코드 61 을 돌려준다
    When 서울 날씨를 조회한다
    Then 조회한 날씨는 "rain" 이다
    And 요청에 서울 좌표와 Asia/Seoul 시간대와 weather_code 항목이 들어 있다

  Scenario: 연결 오류가 나면 unknown 으로 처리한다
    Given Open-Meteo 요청이 연결 오류로 실패한다
    When 서울 날씨를 조회한다
    Then 조회한 날씨는 "unknown" 이다

  Scenario: HTTP 오류 응답이면 unknown 으로 처리한다
    Given Open-Meteo가 HTTP 500 을 돌려준다
    When 서울 날씨를 조회한다
    Then 조회한 날씨는 "unknown" 이다

  Scenario: 응답 형식이 예상과 다르면 unknown 으로 처리한다
    Given Open-Meteo가 예상과 다른 JSON 을 돌려준다
    When 서울 날씨를 조회한다
    Then 조회한 날씨는 "unknown" 이다
