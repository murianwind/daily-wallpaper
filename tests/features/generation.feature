Feature: 이미지 생성 요청 (Cloudflare Workers AI)
  무료 사용량을 아끼기 위해 재시도 횟수를 제한하고, 일시적인 오류만 재시도한다.

  Scenario: 성공하면 디코딩된 이미지 바이트를 돌려준다
    Given Cloudflare가 정상 응답한다
    When 프롬프트로 이미지를 생성한다
    Then 이미지 바이트를 받는다
    And 요청은 1번 보냈다
    And 요청 주소에 계정 ID와 모델이 들어 있다
    And 요청 폼에 prompt, width, height, seed 가 들어 있다
    And 인증 헤더에 토큰이 들어 있다

  Scenario: 서버 오류 뒤에 재시도해서 성공한다
    Given Cloudflare가 처음 2번은 HTTP 500 을 돌려주고 그다음에 성공한다
    When 프롬프트로 이미지를 생성한다
    Then 이미지 바이트를 받는다
    And 요청은 3번 보냈다
    And 재시도 사이에 2번 대기했다

  Scenario: 요청 한도 오류(429)도 재시도한다
    Given Cloudflare가 처음 1번은 HTTP 429 을 돌려주고 그다음에 성공한다
    When 프롬프트로 이미지를 생성한다
    Then 이미지 바이트를 받는다
    And 요청은 2번 보냈다

  Scenario: 네트워크 오류도 재시도한다
    Given Cloudflare 연결이 처음 1번은 끊기고 그다음에 성공한다
    When 프롬프트로 이미지를 생성한다
    Then 이미지 바이트를 받는다
    And 요청은 2번 보냈다

  Scenario: 최대 시도 횟수를 넘기면 실패한다
    Given Cloudflare가 항상 HTTP 500 을 돌려준다
    When 프롬프트로 이미지를 생성한다
    Then 생성 오류가 발생한다
    And 요청은 3번 보냈다

  Scenario: 인증 오류는 재시도하지 않는다
    Given Cloudflare가 항상 HTTP 401 을 돌려준다
    When 프롬프트로 이미지를 생성한다
    Then 생성 오류가 발생한다
    And 요청은 1번 보냈다
    And 재시도 사이에 0번 대기했다

  Scenario: 재시도할 때마다 seed 가 달라진다
    Given Cloudflare가 항상 HTTP 500 을 돌려준다
    When 프롬프트로 이미지를 생성한다
    Then 시도마다 seed 가 서로 다르고 첫 seed 는 100 이다

  Scenario: 응답에 이미지가 없으면 재시도 없이 실패한다
    Given Cloudflare가 200 이지만 이미지가 없는 응답을 준다
    When 프롬프트로 이미지를 생성한다
    Then 생성 오류가 발생한다
    And 요청은 1번 보냈다

  Scenario: 오류 메시지에 계정 ID와 토큰이 노출되지 않는다
    Given Cloudflare 연결 오류 메시지에 요청 주소와 토큰이 들어 있다
    When 프롬프트로 이미지를 생성한다
    Then 생성 오류가 발생한다
    And 오류 메시지에 계정 ID와 토큰이 없다
