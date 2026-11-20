Feature: 워크플로 실행 조건
  정시 실행은 GitHub 예약(schedule)이 아니라 Home Assistant 가 repository_dispatch 로 호출한다.
  낮/밤은 호출 시각으로 정해진다.

  Scenario: 외부 호출 이벤트로 실행된다
    Given 워크플로 파일
    Then 외부 호출 이벤트는 "wallpaper-update" 하나다
    And 수동 실행도 가능하다

  Scenario: GitHub 예약 실행은 쓰지 않는다
    Given 워크플로 파일
    Then 예약 실행은 없다
    And 예약 실행을 살리기 위한 keepalive 작업도 없다

  Scenario: 낮/밤은 입력값이 없으면 호출 시각으로 정한다
    Given 워크플로 파일
    Then 생성 단계의 시간대 입력값은 "auto" 이다

  Scenario: 생성 단계는 배포된 latest.json 주소를 받아 직전 명승지를 읽는다
    Given 워크플로 파일
    Then 생성 단계의 LATEST_JSON_URL 은 이 저장소의 Pages 주소 latest.json 이다
