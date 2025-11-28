# 11-28 Debugging Test

# 공정 전체 Process
	1. Setup
	2. 공정 시작 버튼 (STM)
	3. RealSense로 물류 색상 탐지
	4. Dobot이 색상에 따라 물건 분류
	5. TurtleBot에 박스가 특정 개수 이상 적재되면 이동 시작

# 비상 상황 시 동작
- 컨베이어 벨트 멈춤
- STM 보드 LED 점멸
- Dobot 동작 정지
- Turtlebot 초기 위치로 복귀
