## Frontend (Vue.js)

    - Modbus Log 탭 ? pymodbus로 저장된 로그 리스트

    - Dobot Sensor 탭 ? 센서 값 그래프

    - TurtleBot Monitor 탭 ? 전류/전압/배터리 상태 실시간 관제

WebSocket(Socke.IO) + REST API로 Node.js와 통신

## Backend (Node.js / Express)

REST API

GET /api/logs : 저장된 Modbus 로그 조회

GET /api/dobot/history : Dobot 센서 과거 데이터

GET /api/turtlebot/history : 배터리/전류 과거 데이터

WebSocket (Socket.IO)

    - modbus_log 채널: 새 로그가 쌓일 때마다 push

    - dobot_sensor 채널: 주기적으로 센서값 push

    - turtlebot_status 채널: ROS 토픽 데이터 push
