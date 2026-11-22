Feature: 프롬프트 조립
  정선풍 진경산수화라는 고정 스타일 위에 명승지, 계절, 날씨, 시간대를 얹는다.

  Scenario Outline: 날짜로 계절을 정한다
    When 날짜 <date> 의 계절을 구한다
    Then 계절은 "<season>" 이다

    Examples:
      | date       | season |
      | 2026-03-01 | spring |
      | 2026-05-31 | spring |
      | 2026-06-01 | summer |
      | 2026-08-31 | summer |
      | 2026-09-01 | autumn |
      | 2026-11-30 | autumn |
      | 2026-12-01 | winter |
      | 2027-02-28 | winter |

  Scenario: 고정 화풍 문구가 항상 들어간다
    Given 박연폭포 명승지
    When day 시간대, autumn 계절, clear 날씨, left 쪽으로 프롬프트를 만든다
    Then 프롬프트에 "jingyeong sansuhwa" 가 들어 있다
    And 프롬프트에 "Jeong Seon" 가 들어 있다
    And 프롬프트에 "no text" 가 들어 있다

  Scenario: 흑백 수묵을 요구한다
    Given 박연폭포 명승지
    When day 시간대, autumn 계절, clear 날씨, left 쪽으로 프롬프트를 만든다
    Then 프롬프트에 "monochrome" 가 들어 있다
    And 프롬프트에 "no color" 가 들어 있다

  Scenario: 그림이 화면 가장자리까지 꽉 차도록 요구한다
    Given 박연폭포 명승지
    When day 시간대, autumn 계절, clear 날씨, left 쪽으로 프롬프트를 만든다
    Then 프롬프트에 "edge to edge" 가 들어 있다
    And 프롬프트에 "no paper margin" 가 들어 있다

  Scenario: 멀리서 내려다본 원경 조망도 구도를 요구한다
    Given 박연폭포 명승지
    When day 시간대, autumn 계절, clear 날씨, left 쪽으로 프롬프트를 만든다
    Then 프롬프트에 "distant panoramic view" 가 들어 있다
    And 프롬프트에 "seen from far away" 가 들어 있다

  Scenario: 하늘 윗부분은 비워 두도록 요구한다
    Given 박연폭포 명승지
    When day 시간대, autumn 계절, clear 날씨, left 쪽으로 프롬프트를 만든다
    Then 프롬프트에 "empty sky" 가 들어 있다
    And 프롬프트에 "upper third" 가 들어 있지 않다

  Scenario Outline: 해와 달은 고른 쪽에 작게 두고 가운데는 피한다
    Given 박연폭포 명승지
    When night 시간대, autumn 계절, clear 날씨, <side> 쪽으로 프롬프트를 만든다
    Then 프롬프트에 "<present>" 가 들어 있다
    And 프롬프트에 "<absent>" 가 들어 있지 않다
    And 프롬프트에 "never at the center" 가 들어 있다

    Examples:
      | side  | present                      | absent                       |
      | left  | in the left part of the sky  | in the right part of the sky |
      | right | in the right part of the sky | in the left part of the sky  |

  Scenario: 알 수 없는 해달 위치는 거부된다
    Given 박연폭포 명승지
    When day 시간대, autumn 계절, clear 날씨, center 쪽으로 프롬프트를 만들려 한다
    Then 프롬프트 입력 오류가 발생한다

  Scenario: 명승지 묘사가 들어간다
    Given 박연폭포 명승지
    When day 시간대, autumn 계절, clear 날씨, left 쪽으로 프롬프트를 만든다
    Then 프롬프트에 "waterfall plunging" 가 들어 있다

  Scenario: 낮 프롬프트는 어두운 먹색 톤을 요구한다
    Given 박연폭포 명승지
    When day 시간대, autumn 계절, clear 날씨, left 쪽으로 프롬프트를 만든다
    Then 프롬프트에 "dark charcoal" 가 들어 있다
    And 프롬프트에 "deep black ink" 가 들어 있지 않다
    And 프롬프트에 "bright" 가 들어 있지 않다

  Scenario: 밤 프롬프트는 더 어두운 톤을 요구한다
    Given 박연폭포 명승지
    When night 시간대, autumn 계절, clear 날씨, left 쪽으로 프롬프트를 만든다
    Then 프롬프트에 "deep black ink" 가 들어 있다
    And 프롬프트에 "daytime" 가 들어 있지 않다

  Scenario: 모든 시간대에서 전체적으로 어두운 톤을 요구한다
    Given 박연폭포 명승지
    When day 시간대, autumn 계절, clear 날씨, left 쪽으로 프롬프트를 만든다
    Then 프롬프트에 "overall dark low-key" 가 들어 있다

  Scenario: 낮 프롬프트에는 해도 달도 그리지 않는다
    Given 박연폭포 명승지
    When day 시간대, autumn 계절, clear 날씨, left 쪽으로 프롬프트를 만든다
    Then 프롬프트에 "no sun and no moon" 가 들어 있다
    And 프롬프트에 "part of the sky" 가 들어 있지 않다

  Scenario Outline: 밤 프롬프트에는 오늘의 달 모양이 들어간다
    Given 박연폭포 명승지
    When night 시간대, autumn 계절, clear 날씨, right 쪽, <phase> 달로 프롬프트를 만든다
    Then 프롬프트에 "<text>" 가 들어 있다

    Examples:
      | phase           | text                                   |
      | waxing_crescent | waxing crescent, lit on its right edge |
      | first_quarter   | half moon, the right half lit          |
      | waxing_gibbous  | waxing gibbous                         |
      | full            | full round moon                        |
      | waning_gibbous  | waning gibbous                         |
      | last_quarter    | half moon, the left half lit           |
      | waning_crescent | waning crescent, lit on its left edge  |

  Scenario: 그믐달 밤에는 달을 그리지 않는다
    Given 박연폭포 명승지
    When night 시간대, autumn 계절, clear 날씨, right 쪽, new 달로 프롬프트를 만든다
    Then 프롬프트에 "no moon is drawn" 가 들어 있다
    And 프롬프트에 "part of the sky" 가 들어 있지 않다

  Scenario: 구름이나 비가 달을 가리면 달을 그리지 않는다
    Given 박연폭포 명승지
    When night 시간대, autumn 계절, rain 날씨, left 쪽으로 프롬프트를 만든다
    Then 프롬프트에 "if clouds or rain hide it, draw no moon" 가 들어 있다

  Scenario: 알 수 없는 달 모양은 거부된다
    Given 박연폭포 명승지
    When night 시간대, autumn 계절, clear 날씨, left 쪽, half 달로 프롬프트를 만들려 한다
    Then 프롬프트 입력 오류가 발생한다

  Scenario: 계절이 프롬프트에 반영된다
    Given 박연폭포 명승지
    When day 시간대, winter 계절, clear 날씨, left 쪽으로 프롬프트를 만든다
    Then 프롬프트에 "snow dusting the rocks" 가 들어 있다

  Scenario: 비 오는 낮의 날씨가 반영된다
    Given 박연폭포 명승지
    When day 시간대, summer 계절, rain 날씨, left 쪽으로 프롬프트를 만든다
    Then 프롬프트에 "falling rain" 가 들어 있다

  Scenario: 비 오는 밤에는 달이 가려진다
    Given 박연폭포 명승지
    When night 시간대, summer 계절, rain 날씨, left 쪽으로 프롬프트를 만든다
    Then 프롬프트에 "moon hidden" 가 들어 있다

  Scenario: 모든 날씨 상태와 시간대와 계절 조합에 문구가 준비되어 있다
    Given 박연폭포 명승지
    Then 모든 조합으로 프롬프트를 만들 수 있다

  Scenario: 어떤 조합도 프롬프트 길이 제한을 넘지 않는다
    Given 실제 명승지 데이터 파일
    Then 모든 명승지와 조합의 프롬프트가 2000자 이하이다

  Scenario: 어떤 조합에도 색 이름이 들어가지 않는다
    Given 실제 명승지 데이터 파일
    Then 모든 명승지와 조합의 프롬프트에 색 이름이 없다

  Scenario: 알 수 없는 시간대는 거부된다
    Given 박연폭포 명승지
    When dawn 시간대, autumn 계절, clear 날씨, left 쪽으로 프롬프트를 만들려 한다
    Then 프롬프트 입력 오류가 발생한다

  Scenario: 알 수 없는 날씨 상태는 거부된다
    Given 박연폭포 명승지
    When day 시간대, autumn 계절, hail 날씨, left 쪽으로 프롬프트를 만들려 한다
    Then 프롬프트 입력 오류가 발생한다
