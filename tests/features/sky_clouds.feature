Feature: 하늘 구름 무늬
  위쪽 빈 하늘은 그림을 베끼지 않고 새로 그리되, 날씨에 맞춰 구름 무늬를 넣어 단색으로 뭉개지지 않게 한다.

  Scenario Outline: 날씨에 따라 구름의 짙기를 정한다
    When 날씨 "<condition>" 의 구름을 정한다
    Then 구름의 세기는 <strength> 이다

    Examples:
      | condition     | strength |
      | clear         | 0.25     |
      | partly_cloudy | 0.6      |
      | fog           | 0.4      |
      | overcast      | 1.0      |
      | rain          | 1.0      |
      | thunderstorm  | 1.0      |
      | snow          | 1.0      |
      | unknown       | 0.4      |

  Scenario: 구름이 없으면 빈 영역의 각 줄은 가로로 고르다
    Given 밝은 회색 단색 1104x1600 PNG 이미지
    When 구름 없이 변환한다
    Then 빈 영역의 가로 밝기 변화는 거의 없다

  Scenario: 구름을 넣으면 빈 영역에 밝고 어두운 무늬가 생긴다
    Given 밝은 회색 단색 1104x1600 PNG 이미지
    When 세기 1.0 구름으로 변환한다
    Then 빈 영역의 가로 밝기 변화는 뚜렷하다

  Scenario: 약한 구름은 강한 구름보다 무늬가 약하다
    Given 밝은 회색 단색 1104x1600 PNG 이미지
    When 세기 0.25 구름과 세기 1.0 구름으로 각각 변환한다
    Then 약한 구름의 가로 밝기 변화가 더 작다

  Scenario: 구름이 있어도 빈 영역과 그림의 경계는 끊기지 않는다
    Given 밝은 회색 단색 1104x1600 PNG 이미지
    When 세기 1.0 구름으로 변환한다
    Then 경계 위아래 밝기는 거의 같다

  Scenario: 같은 시드는 같은 구름을 그린다
    Given 밝은 회색 단색 1104x1600 PNG 이미지
    When 시드 3 구름을 두 번 변환한다
    Then 두 결과는 같다

  Scenario: 시드가 다르면 구름도 다르다
    Given 밝은 회색 단색 1104x1600 PNG 이미지
    When 시드 3 구름과 시드 4 구름으로 각각 변환한다
    Then 두 결과는 다르다

  Scenario: 구름이 있어도 하늘은 맨 위로 갈수록 어두워진다
    Given 밝은 회색 단색 1104x1600 PNG 이미지
    When 세기 1.0 구름으로 변환한다
    Then 맨 위쪽 줄의 평균 밝기는 경계 근처 줄의 평균 밝기보다 어둡다
