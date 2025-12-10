<template>
  <section>
    <div class="section-title-row">
      <div>
        <h2 class="section-title">Dobot</h2>
        <p class="section-caption">팔 상태 / 부하 / 비상 여부</p>
      </div>
      <span class="badge badge-info">샘플 레이아웃</span>
    </div>

    <div class="db-grid">
      <!-- Arm Status -->
      <div class="db-card">
        <div class="db-card-header">
          <span>Arm Status</span>
          <span class="badge badge-info">READY</span>
        </div>
        <ul class="metric-list">
          <li>
            <span>Joint Temperature</span>
            <span>42.3 °C</span>
          </li>
          <li>
            <span>Load</span>
            <span>37 %</span>
          </li>
          <li>
            <span>Cycle Count</span>
            <span>1250 cycles</span>
          </li>
          <li>
            <span>Emergency Stop</span>
            <span class="badge badge-danger">Normal</span>
          </li>
        </ul>
      </div>

      <!-- Sensor Trend placeholder -->
      <div class="db-card">
        <div class="db-card-header">
          <span>Sensor Trend</span>
          <span class="text-muted">추후 그래프 영역</span>
        </div>
        <div class="db-placeholder">
          토크 / 온도 등을<br />
          Line Chart로 표현할 수 있는<br />
          영역입니다.
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
// Dobot도 지금은 정적 예시만
</script>

<style scoped>
.db-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr);
  gap: 12px;
}

@media (max-width: 900px) {
  .db-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}

.db-card {
  background: #ffffff;
  border-radius: 10px;
  border: 1px solid #e2e5ef;
  padding: 12px 12px 10px;
}

.db-card-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
  font-size: 0.9rem;
  font-weight: 500;
}

.db-placeholder {
  margin-top: 8px;
  padding: 16px 10px;
  border-radius: 8px;
  border: 1px dashed #d4d9e6;
  font-size: 0.82rem;
  text-align: center;
  color: var(--text-muted);
}
</style>
