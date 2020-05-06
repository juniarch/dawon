Home Assistant: DawonDNS Component (v.0.0.3)
=======================================

이 Component는 [Home Assistant][hass] 에서 DawonDNS WiFi 플러그를 제어합니다.

설치방법:

1. 이 repository의 모든 파일을 HA설치폴더 `~/.homeassistant` 혹은 `~/config` 폴더 내 `custom_components\dawon` 폴더 내부에 넣으세요.

       $ cd ~/.homeassistant
       $ mkdir custom_components
       $ cd custom_components
       $ git clone https://github.com/gugu927/dawon.git dawon

2. HA설치폴더 `~/.homeassistant` 혹은 `~/config` 폴더 내 `switch.yaml` 에 아래 내용을 추가합니다.

       - platform: dawon
         user_id: '다원DNS 계정 ID'
         user_account: 'google, kakako 또는 naver 등'
         scan_interval : 60
         device_list:
           - 'DAWONDNS-B530_W-xxxxxxxxxxxx'
           - 'DAWONDNS-B530_W-yyyyyyyyyyy'

패치노트:

       0.0.1:
       - 다원DNS B530_W Component
       0.0.2:
       - 전력량 상태값 소수점 2자리 까지 표기되도록 수정
       - 누적사용량 표시단위 수정(W -> kWh)
       - 스위치 기본아이콘 설정(mdi:power-socket-eu)
       - 스위치 off 시 현재 전력량 0.00으로 즉시 변경
       - 센서류 entity_id 수정
       0.0.3:
       - header관련 오류 수정


Credits
-------

This is by [GuGU927][andy]. The license is [MIT][].

For Korean user, visit [HomeAssistant Naver Cafe][cafe]

[cafe]: https://cafe.naver.com/koreassistant
[mit]: https://opensource.org/licenses/MIT
[andy]: https://github.com/gugu927/dawon
[hass]: https://home-assistant.io
