Feature: 워크플로 예약 실행
  생성은 한국 시각 새벽 4시(낮 그림)와 오후 4시(밤 그림)에 돌고, 낮/밤은 실행 시각으로 정해진다.

  Scenario: 예약 실행은 한국 시간 기준으로 하루 두 번이다
    Given 워크플로 파일
    Then 예약 실행은 2건이다
    And 모든 예약 실행의 시간대는 "Asia/Seoul" 이다
    And 예약 실행 시각은 "0 4 * * *" 와 "0 16 * * *" 이다

  Scenario: 낮/밤은 크론 식이 아니라 실행 시각으로 정한다
    Given 워크플로 파일
    Then 예약 실행의 시간대 입력값은 "auto" 이다

  Scenario: 생성 단계는 배포된 latest.json 주소를 받아 직전 명승지를 읽는다
    Given 워크플로 파일
    Then 생성 단계의 LATEST_JSON_URL 은 이 저장소의 Pages 주소 latest.json 이다
