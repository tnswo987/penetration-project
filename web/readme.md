# Web 실행 방법

```
1. git pull
2. vue official download
3. backend
  Node Version이 맞지 않으면
   - nvm 설치 (이미 있으면 스킵)
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
    source ~/.bashrc
   - Node 18 설치 & 사용
    nvm install 18
    nvm use 18
    nvm alias default 18
   - node_modules 깨끗이 재설치
    cd ~/pjt/penetration-project/web/backend
    rm -rf node_modules package-lock.json
    npm install
    npm start
4. frontend
  Node Version이 맞지 않으면
   - nvm 설치 (이미 있으면 스킵)
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
    source ~/.bashrc
   - Node 20.19.0 설치 & 사용
    nvm install 20.19.0
    nvm use 20.19.0
    node -v
   - node_modules 깨끗이 재설치
    cd ~/pjt/penetration-project/web/frontend
    rm -rf node_modules package-lock.json
    npm install
    npm run dev -- --host
5. websocket
  pip install websocket-server

```

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

---

## 2. TurtleBot 탭

### Critical

- Node.js에서 ROS2 Humble Topic 받기 !!

- Windows는 그냥 웹서버/WS만 하고, ROS 값은 rosbridge로 받기

  ```
  sudo apt install ros-humble-rosbridge-server
  ros2 launch rosbridge_server rosbridge_websocket_launch.xml
  ```

  ```
  // frontend install
  npm i js-yaml
  npm i roslib
  ```

1.  우측 Map + 로봇 위치/이동에 필요한 ROS Topic

    - /amcl_pose 또는

    - /tf (map → base_link)

2.  좌측 TurtleBot 상태 정보

    - /battery_state (sensor_msgs/BatteryState)

      percentage → State of Charge

      voltage → Voltage

      current → Current

    - /odom (nav_msgs/Odometry)

      twist.twist.linear.x → Linear Velocity

      twist.twist.angular.z → Angular Velocity

      Status (Cruising / Stopped 등)

      ```
         if |linear| < 0.01 && |angular| < 0.01 → "Stopped"
         else if |angular| > 0.2 → "Turning"
         else → "Cruising"
      ```

    - /joint_states (sensor_msgs/JointState)

      name[]

      velocity[] → Left / Right vel

      effort[] → Torque / Effort

- Turtlebot 탭 진입 → backend가 ROS 토픽 구독 시작 → 프론트에 push

- Turtlebot 탭 이탈 → backend가 구독 중단 → 리소스/트래픽 절약

---

## 3. Dobot Sensor 탭

### 구조

(ESP32+MPU6050 → Modbus 서버 PC → Node 백엔드 → Vue 대시보드)

```
npm i chart.js
```