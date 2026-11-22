Feature: 달 모양 계산
  생성 시각으로 그날의 달 모양(8단계)을 구한다. 북반구에서 차오르는 달은 오른쪽이 밝다.
  기준 자료(2026-11, 세계시): 하현 11/1 20:28, 새달 11/9 07:02, 상현 11/17 11:48, 보름 11/24 14:53
  출처: https://www.moongiant.com/moonphases/november/2026/ , https://starwalk.space/en/news/full-moon-november-2022

  Scenario Outline: 실제 천문 자료의 날짜는 알려진 달 모양이 된다
    When 한국 시각 <day> 16시 10분 의 달 모양을 구한다
    Then 달 모양은 "<phase>" 이다

    Examples:
      | day        | phase           |
      | 2026-11-01 | last_quarter    |
      | 2026-11-09 | new             |
      | 2026-11-13 | waxing_crescent |
      | 2026-11-17 | first_quarter   |
      | 2026-11-20 | waxing_gibbous  |
      | 2026-11-24 | full            |
      | 2026-11-28 | waning_gibbous  |
      | 2026-12-05 | waning_crescent |

  Scenario: 같은 순간이면 시간대 표기가 달라도 같은 달 모양이다
    When 한국 시각 2026-11-24 16시 10분 과 같은 순간의 세계시로 달 모양을 구한다
    Then 두 달 모양은 같다

  Scenario: 시간대 정보가 없는 시각은 거부된다
    When 시간대 정보가 없는 시각의 달 모양을 구하려 한다
    Then 달 모양 입력 오류가 발생한다
