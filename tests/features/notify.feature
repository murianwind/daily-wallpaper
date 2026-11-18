Feature: 실패 알림 (디스코드 웹훅)
  알림은 부가 기능이므로 설정이 없거나 전송이 실패해도 본래 작업의 실패 처리를 방해하지 않는다.

  Scenario: 웹훅이 설정되어 있으면 메시지를 보낸다
    Given 정상 동작하는 웹훅
    When 웹훅 주소 "https://discord.test/hook" 로 "생성 실패" 메시지를 보낸다
    Then 알림 결과는 성공이다
    And 웹훅으로 "생성 실패" 내용이 1번 전송되었다

  Scenario: 웹훅이 설정되어 있지 않으면 보내지 않는다
    Given 정상 동작하는 웹훅
    When 웹훅 주소 없이 "생성 실패" 메시지를 보낸다
    Then 알림 결과는 실패이다
    And 전송은 한 번도 일어나지 않았다

  Scenario: 전송에 실패해도 예외 없이 실패로 알린다
    Given 연결이 끊기는 웹훅
    When 웹훅 주소 "https://discord.test/hook" 로 "생성 실패" 메시지를 보낸다
    Then 알림 결과는 실패이다

  Scenario: HTTP 오류 응답도 실패로 알린다
    Given HTTP 400 을 돌려주는 웹훅
    When 웹훅 주소 "https://discord.test/hook" 로 "생성 실패" 메시지를 보낸다
    Then 알림 결과는 실패이다

  Scenario: 디스코드 글자 수 제한을 넘는 메시지는 잘라서 보낸다
    Given 정상 동작하는 웹훅
    When 웹훅 주소 "https://discord.test/hook" 로 5000자짜리 메시지를 보낸다
    Then 전송된 내용은 2000자를 넘지 않는다
