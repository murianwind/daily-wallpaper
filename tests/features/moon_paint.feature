Feature: 달 그리기
  모델에 맡기지 않고 계산된 달 모양(8단계)을 후처리에서 직접 그린다.
  북반구 기준으로 차오르는 달은 오른쪽이, 기우는 달은 왼쪽이 밝다. 달은 가운데를 피해 한쪽에 둔다.

  Scenario Outline: 달은 고른 쪽 자리에 밝은 원으로 그려지고 가운데는 비어 있다
    Given 어두운 단색 캔버스
    When <side> 쪽에 full 달을 그린다
    Then 달 중심 픽셀은 밝다
    And 화면 가운데 같은 높이의 픽셀은 어둡다
    And 반대쪽 같은 높이의 픽셀은 어둡다

    Examples:
      | side  |
      | left  |
      | right |

  Scenario Outline: 달 모양에 따라 밝은 부분이 달라진다
    Given 어두운 단색 캔버스
    When right 쪽에 <phase> 달을 그린다
    Then 달 중심에서 오른쪽으로 <right> 반지름 지점은 <right_state>
    And 달 중심에서 왼쪽으로 <left> 반지름 지점은 <left_state>

    Examples:
      | phase           | right | right_state | left | left_state |
      | waxing_crescent | 0.85  | 밝다        | 0.2  | 어둡다     |
      | first_quarter   | 0.5   | 밝다        | 0.5  | 어둡다     |
      | waxing_gibbous  | 0.6   | 밝다        | 0.9  | 어둡다     |
      | waxing_gibbous  | 0.0   | 밝다        | 0.4  | 밝다       |
      | full            | 0.8   | 밝다        | 0.8  | 밝다       |
      | waning_gibbous  | 0.9   | 어둡다      | 0.6  | 밝다       |
      | last_quarter    | 0.5   | 어둡다      | 0.5  | 밝다       |
      | waning_crescent | 0.2   | 어둡다      | 0.85 | 밝다       |

  Scenario: 그믐에는 아무것도 그리지 않는다
    Given 어두운 단색 캔버스
    When right 쪽에 new 달을 그린다
    Then 캔버스는 바뀌지 않았다

  Scenario: 알 수 없는 달 모양은 거부된다
    Given 어두운 단색 캔버스
    When right 쪽에 half 달을 그리려 한다
    Then 달 입력 오류가 발생한다

  Scenario: 알 수 없는 위치는 거부된다
    Given 어두운 단색 캔버스
    When center 쪽에 full 달을 그리려 한다
    Then 달 입력 오류가 발생한다

  Scenario: 달은 화면 위쪽 38% 지점보다 위에 놓인다
    Given 어두운 단색 캔버스
    When right 쪽에 full 달을 그린다
    Then 달 중심은 화면 높이의 38% 보다 위에 있다

