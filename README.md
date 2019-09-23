Home Assistant: DawonDNS Component 
=======================================

이 Component는 [Home Assistant][hass] 에서 DawonDNS WiFi 플러그를 제어합니다.

설치방법:

1. 이 repository의 모든 파일을 HA설치폴더 `~/.homeassistant` 혹은 `~/config` 폴더 내 `custom_components\dawon` 폴더 내부에 넣으세요.

       $ cd ~/.homeassistant
       $ mkdir custom_components
       $ cd custom_components
       $ git clone https://github.com/gugu927/dawon.git dawon

2. HA설치폴더 `~/.homeassistant` 혹은 `~/config` 폴더 내 switch.yaml 에 아래 내용을 추가합니다.

  platform: dawon
  user_id: '다원DNS 계정 ID'
  user_account: '다원DNS 계정 google 혹은 kakako'
  scan_interval : 60
  device_list:
    'DAWONDNS-B530_W-xxxxxxxxxxxx'
    'DAWONDNS-B530_W-yyyyyyyyyyy'

Credits
-------

This is by [GuGU927][andy]. The license is [MIT][].

For Korean user, visit [HomeAssistant Naver Cafe][cafe]

[cafe]: https://cafe.naver.com/koreassistant
[mit]: https://opensource.org/licenses/MIT
[andy]: https://github.com/gugu927/dawon
[hass]: https://home-assistant.io
