Feature: 배경화면 이미지 후처리
  생성된 이미지를 아이폰 15 Pro 화면 크기(1179x2556)의 JPEG 로 맞춘다.

  Scenario: 생성 크기의 이미지를 화면 크기 JPEG 로 바꾼다
    Given 880x1920 PNG 이미지
    When 1179x2556 크기로 변환한다
    Then 결과는 1179x2556 JPEG 이다

  Scenario: 가로로 긴 이미지는 가운데 부분을 남기고 자른다
    Given 가로 3등분(빨강, 초록, 파랑)된 1200x400 PNG 이미지
    When 1179x2556 크기로 변환한다
    Then 결과는 1179x2556 JPEG 이다
    And 결과의 가운데 픽셀은 초록색 계열이다

  Scenario: 투명 배경 PNG 도 JPEG 로 바뀐다
    Given 투명 배경 RGBA PNG 이미지
    When 1179x2556 크기로 변환한다
    Then 결과는 1179x2556 JPEG 이다

  Scenario: 이미지가 아닌 데이터는 거부된다
    Given 이미지가 아닌 바이트
    When 1179x2556 크기로 변환한다
    Then 이미지 처리 오류가 발생한다
