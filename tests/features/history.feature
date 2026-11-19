Feature: 명승지 사용 기록
  직전 실행들이 쓴 명승지 id 는 배포된 latest.json 에서 읽는다.
  읽지 못하면 기록 없이 진행해서 이미지 생성을 막지 않는다.

  Scenario: 배포된 latest.json 에서 최근 명승지 목록을 읽는다
    Given 배포된 latest.json 의 최근 명승지가 "a, b, c" 이다
    When 최근 명승지 기록을 읽는다
    Then 읽은 기록은 "a, b, c" 이다
    And 요청은 설정한 주소로 갔고 캐시를 피하는 값이 붙어 있다

  Scenario: 연결 오류가 나면 빈 기록으로 처리한다
    Given 기록 주소 요청이 연결 오류로 실패한다
    When 최근 명승지 기록을 읽는다
    Then 읽은 기록은 비어 있다

  Scenario: 아직 배포 전이라 404 이면 빈 기록으로 처리한다
    Given 기록 주소가 HTTP 404 를 돌려준다
    When 최근 명승지 기록을 읽는다
    Then 읽은 기록은 비어 있다

  Scenario: JSON 이 아닌 응답이면 빈 기록으로 처리한다
    Given 기록 주소가 JSON 이 아닌 응답을 돌려준다
    When 최근 명승지 기록을 읽는다
    Then 읽은 기록은 비어 있다

  Scenario: 기록 항목이 없는 예전 형식이면 빈 기록으로 처리한다
    Given 기록 항목이 없는 예전 형식의 latest.json 이 배포되어 있다
    When 최근 명승지 기록을 읽는다
    Then 읽은 기록은 비어 있다

  Scenario: 기록 항목이 문자열 목록이 아니면 빈 기록으로 처리한다
    Given 기록 항목이 숫자 목록인 latest.json 이 배포되어 있다
    When 최근 명승지 기록을 읽는다
    Then 읽은 기록은 비어 있다

  Scenario: 새 명승지를 맨 앞에 넣고 한도까지만 남긴다
    When 기록 "a, b, c" 에 "d" 를 한도 3 으로 더한다
    Then 새 기록은 "d, a, b" 이다

  Scenario: 이미 있는 명승지는 중복 없이 맨 앞으로 옮긴다
    When 기록 "a, b, c" 에 "b" 를 한도 3 으로 더한다
    Then 새 기록은 "b, a, c" 이다
