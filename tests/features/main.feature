Feature: 배경화면 생성 실행
  명승지 선택 → 날씨 → 프롬프트 → 생성 → 후처리 → 저장을 조립하고,
  실패하면 기존 이미지를 건드리지 않고 알린다.

  Scenario Outline: 시간대를 정한다
    When 요청 "<requested>" 와 한국 시각 <hour>시 <minute>분 으로 시간대를 정한다
    Then 정해진 시간대는 "<expected>" 이다

    Examples:
      | requested | hour | minute | expected |
      | auto      | 4    | 0      | day      |
      | auto      | 6    | 0      | day      |
      | auto      | 11   | 59     | day      |
      | auto      | 12   | 0      | night    |
      | auto      | 16   | 0      | night    |
      | auto      | 17   | 30     | night    |
      | night     | 6    | 0      | night    |
      | day       | 18   | 0      | day      |

  Scenario: 알 수 없는 시간대 요청은 설정 오류다
    When 요청 "dawn" 와 한국 시각 6시 0분 으로 시간대를 정하려 한다
    Then 설정 오류가 발생한다

  Scenario: 필수 환경변수가 없으면 설정 오류다
    When 환경변수 없이 설정을 불러오려 한다
    Then 설정 오류가 발생하고 메시지에 "CF_ACCOUNT_ID"와 "CF_API_TOKEN"이 들어 있다

  Scenario: 선택 환경변수의 기본값을 쓴다
    When 필수 환경변수만으로 설정을 불러온다
    Then 모델은 기본 모델이고 웹훅과 기록 주소는 없다

  Scenario: 빈 웹훅 값은 설정하지 않은 것으로 본다
    When 웹훅과 기록 주소 값이 빈 문자열인 환경변수로 설정을 불러온다
    Then 모델은 기본 모델이고 웹훅과 기록 주소는 없다

  Scenario: 환경변수로 모델과 웹훅을 지정할 수 있다
    When 모델과 웹훅과 기록 주소를 지정한 환경변수로 설정을 불러온다
    Then 설정에 지정한 모델과 웹훅과 기록 주소가 들어 있다

  Scenario: 성공하면 latest.jpg 와 latest.json 을 만든다
    Given 정상 설정과 정상 동작하는 생성기
    When day 시간대로 2026-11-19 에 실행한다
    Then 종료 코드는 0 이다
    And out 폴더에 1179x2556 크기의 latest.jpg 가 있다
    And latest.json 에 slot 이 "day" 이고 weather 가 "clear" 이고 season 이 "autumn" 이다
    And 알림은 가지 않았다

  Scenario: 프롬프트에 고른 명승지와 계절과 날씨가 반영된다
    Given 정상 설정과 정상 동작하는 생성기
    And 날씨가 "rain" 으로 조회된다
    When night 시간대로 2026-11-19 에 실행한다
    Then 생성기에 보낸 프롬프트에 고른 명승지 묘사가 들어 있다
    And 생성기에 보낸 프롬프트에 "rainy night" 가 들어 있다
    And 생성기에 보낸 프롬프트에 "autumn" 가 들어 있다

  Scenario: 설정된 모델과 생성 해상도로 생성기를 호출한다
    Given 정상 설정과 정상 동작하는 생성기
    When day 시간대로 2026-11-19 에 실행한다
    Then 생성기는 모델 "@cf/test/model" 과 1104x1600 크기로 호출되었다

  Scenario: 연달아 실행해도 이전 실행의 명승지는 다시 나오지 않는다
    Given 정상 설정과 정상 동작하는 생성기
    And 기록 주소가 설정되어 있고 배포된 기록을 따라간다
    When 낮과 밤을 번갈아 10번 연달아 실행한다
    Then 10번의 명승지가 모두 다르다

  Scenario: 배포된 기록에 있는 명승지는 피하고 기록을 갱신한다
    Given 정상 설정과 정상 동작하는 생성기
    And 기록 주소가 설정되어 있고 배포된 기록이 목록의 앞쪽 20곳이다
    When day 시간대로 2026-11-19 에 실행한다
    Then 고른 명승지는 배포된 기록에 없다
    And latest.json 의 기록은 고른 명승지가 맨 앞이고 이전 기록 19곳이 이어진다

  Scenario: 기록 주소가 없으면 기록을 읽지 않고 고른 명승지만 기록한다
    Given 정상 설정과 정상 동작하는 생성기
    When day 시간대로 2026-11-19 에 실행한다
    Then 기록은 읽지 않았다
    And latest.json 의 기록은 고른 명승지 하나뿐이다

  Scenario: 실행마다 다른 시드로 생성하고 시드를 기록한다
    Given 정상 설정과 정상 동작하는 생성기
    When day 시간대로 2026-11-19 에 2번 연달아 실행한다
    Then 두 번의 생성 시드가 서로 다르고 latest.json 에 마지막 시드가 기록된다

  Scenario: 밤에는 오늘의 달 모양과 위치가 프롬프트와 latest.json 에 같게 기록된다
    Given 정상 설정과 정상 동작하는 생성기
    When night 시간대로 2026-11-20 에 실행한다
    Then 생성기에 보낸 프롬프트에 "waxing gibbous" 가 들어 있다
    And latest.json 의 달 모양은 "waxing_gibbous" 이다
    And latest.json 의 해달 위치는 프롬프트에 쓴 쪽과 같다

  Scenario: 실행마다 달의 위치가 왼쪽과 오른쪽으로 무작위로 정해진다
    Given 정상 설정과 정상 동작하는 생성기
    When night 시간대로 2026-11-20 에 20번 연달아 실행한다
    Then 프롬프트에 해달 위치가 왼쪽인 경우와 오른쪽인 경우가 모두 나왔다

  Scenario: 낮에는 해도 달도 그리지 않도록 프롬프트를 보낸다
    Given 정상 설정과 정상 동작하는 생성기
    When day 시간대로 2026-11-20 에 실행한다
    Then 생성기에 보낸 프롬프트에 "no sun and no moon" 가 들어 있다

  Scenario: 생성이 실패하면 기존 이미지를 유지하고 알린 뒤 1 을 돌려준다
    Given 정상 설정과 항상 실패하는 생성기
    And 디스코드 웹훅이 설정되어 있다
    And 이전에 만든 latest.jpg 가 있다
    When day 시간대로 2026-11-19 에 실행한다
    Then 종료 코드는 1 이다
    And latest.jpg 는 이전 내용 그대로다
    And 디스코드 알림이 1번 갔고 메시지에 고른 명승지 이름이 들어 있다

  Scenario: 생성기가 이미지가 아닌 데이터를 주면 같은 방식으로 실패 처리한다
    Given 정상 설정과 이미지가 아닌 데이터를 주는 생성기
    And 디스코드 웹훅이 설정되어 있다
    When day 시간대로 2026-11-19 에 실행한다
    Then 종료 코드는 1 이다
    And out 폴더에 latest.jpg 가 없다
    And 디스코드 알림이 1번 갔고 메시지에 고른 명승지 이름이 들어 있다

  Scenario: 웹훅이 없어도 실패 처리는 정상적으로 끝난다
    Given 정상 설정과 항상 실패하는 생성기
    When day 시간대로 2026-11-19 에 실행한다
    Then 종료 코드는 1 이다

  Scenario: 명령줄 실행에서 설정이 빠지면 2 를 돌려준다
    When 환경변수 없이 명령줄로 실행한다
    Then 명령줄 종료 코드는 2 이다
