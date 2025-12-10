<template>
  <section>
    <div class="section-title-row">
      <div>
        <h2 class="section-title">TurtleBot</h2>
        <p class="section-caption">배터리 / 속도 / 미션 상태 요약</p>
      </div>
      <span class="badge badge-info">샘플 레이아웃</span>
    </div>

    <div class="tb-grid">
      <!-- Battery -->
      <div class="tb-card">
        <div class="tb-card-header">
          <span>Battery</span>
          <span class="text-muted">잔량 · 전압</span>
        </div>
        <ul class="metric-list">
          <li>
            <span>State of Charge</span>
            <span>78 %</span>
          </li>
          <li>
            <span>Voltage</span>
            <span>24.6 V</span>
          </li>
          <li>
            <span>Current</span>
            <span>1.8 A</span>
          </li>
        </ul>
      </div>

      <!-- Motion -->
      <div class="tb-card">
        <div class="tb-card-header">
          <span>Motion</span>
          <span class="text-muted">속도 · 방향</span>
        </div>
        <ul class="metric-list">
          <li>
            <span>Linear Velocity</span>
            <span>0.23 m/s</span>
          </li>
          <li>
            <span>Angular Velocity</span>
            <span>0.05 rad/s</span>
          </li>
          <li>
            <span>Status</span>
            <span>Cruising</span>
          </li>
        </ul>
      </div>

      <!-- Mission -->
      <div class="tb-card">
        <div class="tb-card-header">
          <span>Mission</span>
          <span class="text-muted">현재 목표</span>
        </div>
        <ul class="metric-list">
          <li>
            <span>Goal</span>
            <span>Docking Station</span>
          </li>
          <li>
            <span>Status</span>
            <span>In progress</span>
          </li>
          <li>
            <span>ETA</span>
            <span>00:01:32</span>
          </li>
        </ul>
      </div>
    </div>
  </section>
</template>

<script setup>
// 이 뷰는 지금은 정적 예시만 표시
</script>

<style scoped>
.tb-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

@media (max-width: 900px) {
  .tb-grid {
    grid-template-columns: repeat(1, minmax(0, 1fr));
  }
}

.tb-card {
  background: #ffffff;
  border-radius: 10px;
  border: 1px solid #e2e5ef;
  padding: 12px 12px 10px;
}

.tb-card-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
  font-size: 0.9rem;
  font-weight: 500;
}
</style>
