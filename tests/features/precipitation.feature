Feature: 비와 눈 그리기
  비나 눈이 오는 날에는 후처리에서 빗줄기나 눈송이를 화면 전체에 옅게 얹어 내리는 하늘로 보이게 한다.

  Scenario Outline: 날씨에 따라 그릴 강수 종류를 정한다
    When 날씨 "<condition>" 의 강수를 정한다
    Then 강수 종류는 "<kind>" 이다

    Examples:
      | condition     | kind |
      | rain          | rain |
      | thunderstorm  | rain |
      | snow          | snow |
      | clear         | 없음 |
      | partly_cloudy | 없음 |
      | overcast      | 없음 |
      | fog           | 없음 |
      | unknown       | 없음 |

  Scenario Outline: 빗줄기와 눈송이는 화면 위 중간 아래에 고르게 퍼진다
    Given 어두운 단색 캔버스
    When <kind> 를 그린다
    Then 위쪽과 가운데와 아래쪽 모두에 밝은 점이 있다
    And 밝은 점의 비율은 화면의 일부분에 그친다
    And 평균 밝기는 조금만 올라간다

    Examples:
      | kind |
      | rain |
      | snow |

  Scenario: 빗줄기는 위아래로 긴 선이다
    Given 어두운 단색 캔버스
    When rain 를 그린다
    Then 밝은 점들은 가로보다 세로로 길게 이어진다

  Scenario: 같은 시드로 그리면 같은 결과가 나온다
    Given 어두운 단색 캔버스
    When 시드 1 로 rain 을 두 번 그린다
    Then 두 결과는 같다

  Scenario: 시드가 다르면 다른 결과가 나온다
    Given 어두운 단색 캔버스
    When 시드 1 과 시드 2 로 rain 을 그린다
    Then 두 결과는 다르다

  Scenario: 알 수 없는 강수 종류는 거부한다
    Given 어두운 단색 캔버스
    When hail 를 그리려 한다
    Then 알 수 없는 강수 종류 오류가 발생한다
