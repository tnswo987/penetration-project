# Critical Thing

### 작업자 공간 ----/---- 로봇 작업 공간 분리

- Backend

  index.js 수정

  ```js
  const HOST = "0.0.0.0";
  app.listen(PORT, HOST, () => {
    console.log(`Backend listening on http://${HOST}:${PORT}`);
  });
  ```

  - Windows 포트 허용 check

- Frontend

  web/frontend/src/services/api.js 수정

  ```js
  import axios from "axios";
  const api = axios.create({
    baseURL: "http://0.0.0.0:3000/api",
  });
  ```

## Frontend (Vue.js)

- Modbus Log 탭 -> pymodbus로 저장된 로그 리스트

- Dobot Sensor 탭 -> 센서 값 그래프

- TurtleBot Monitor 탭 -> 전류/전압/배터리 상태 실시간 관제

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

---

## 1. Modbus Log 탭

```

Log_id - Timestamp - Level - Device - Message

ex)

1,2025-12-10 23:55:01,INFO,Modbus,Client connected to Modbus server
2,2025-12-10 23:55:03,INFO,Modbus,Read holding registers success
3,2025-12-10 23:55:06,WARN,Dobot,Joint angle approaching limit
4,2025-12-10 23:55:08,INFO,Dobot,Pick operation started
5,2025-12-10 23:55:10,INFO,Dobot,Pick operation completed successfully
6,2025-12-10 23:55:13,INFO,TurtleBot,Navigation goal received
7,2025-12-10 23:55:15,WARN,TurtleBot,Obstacle detected too close
8,2025-12-10 23:55:18,INFO,TurtleBot,Obstacle avoided successfully
9,2025-12-10 23:55:21,ERROR,TurtleBot,Battery voltage dropped below threshold
10,2025-12-10 23:55:25,INFO,System,Emergency state released by operator

```

---

---

| Log_id | Timestamp           | Level | Device    | Message                                 |
| ------ | ------------------- | ----- | --------- | --------------------------------------- |
| 1      | 2025-12-10 23:55:01 | INFO  | Modbus    | Client connected to Modbus server       |
| 2      | 2025-12-10 23:55:03 | INFO  | Modbus    | Read holding registers success          |
| 3      | 2025-12-10 23:55:06 | WARN  | Dobot     | Joint angle approaching limit           |
| 4      | 2025-12-10 23:55:08 | INFO  | Dobot     | Pick operation started                  |
| 5      | 2025-12-10 23:55:10 | INFO  | Dobot     | Pick operation completed successfully   |
| 6      | 2025-12-10 23:55:13 | INFO  | TurtleBot | Navigation goal received                |
| 7      | 2025-12-10 23:55:15 | WARN  | TurtleBot | Obstacle detected too close             |
| 8      | 2025-12-10 23:55:18 | INFO  | TurtleBot | Obstacle avoided successfully           |
| 9      | 2025-12-10 23:55:21 | ERROR | TurtleBot | Battery voltage dropped below threshold |
| 10     | 2025-12-10 23:55:25 | INFO  | System    | Emergency state released by operator    |

---

### Level 분류 기준

---

| level | 의미                                |
| ----- | ----------------------------------- |
| INFO  | 정상 동작                           |
| WARN  | 주의 필요 (곧 문제 가능성)          |
| ERROR | 즉시 조치 필요                      |
| FATAL | 시스템 중단 수준 (나중에 추가 가능) |

```

```

```

```
