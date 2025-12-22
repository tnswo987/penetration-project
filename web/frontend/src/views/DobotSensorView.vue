<template>
  <section>
    <div class="section-title-row">
      <div>
        <h2 class="section-title">Dobot</h2>
        <span class="text-muted">{{ nowText }}</span>
      </div>

      <div class="right-badges">
        <span class="badge" :class="connected ? 'badge-info' : 'badge-danger'">
          {{ connected ? "WS CONNECTED" : "WS DISCONNECTED" }}
        </span>
      </div>
    </div>

    <div class="db-grid">
      <!-- LEFT: 숫자 + AI 결과 -->
      <div class="db-card">
        <div class="db-card-header">
          <span>MPU Gyro Value</span>
          <span class="text-muted">seq: {{ seq }}</span>
        </div>

        <ul class="metric-list">
          <li>
            <span>ax</span>
            <span>{{ fmt(mpu.ax) }}</span>
          </li>
          <li>
            <span>ay</span>
            <span>{{ fmt(mpu.ay) }}</span>
          </li>
          <li>
            <span>az</span>
            <span>{{ fmt(mpu.az) }}</span>
          </li>
          <li>
            <span>gx</span>
            <span>{{ fmt(mpu.gx) }}</span>
          </li>
          <li>
            <span>gy</span>
            <span>{{ fmt(mpu.gy) }}</span>
          </li>
          <li>
            <span>gz</span>
            <span>{{ fmt(mpu.gz) }}</span>
          </li>
        </ul>

        <div class="ai-box">
          <div class="ai-border"></div>
          <div class="ai-header">
            <span>AI Inference</span>
            <span class="text-muted">{{ lastRxText }}</span>
          </div>

          <!-- 상태 표시 -->
          <div v-if="aiStatus !== null"
              class="ai-status"
              :class="aiStatus ? 'ok' : 'err'">
            {{ aiStatus ? "Normal" : "Error" }}
          </div>

          <div v-else class="ai-empty">
            추론 결과 대기중
          </div>

          <div v-if="lastError" class="ai-error">
            {{ lastError }}
          </div>
        </div>
      </div>

      <!-- RIGHT: Line Chart -->
      <div class="db-card">
        <div class="db-card-header">
          <span>Gyro Value Graph (ax~gz)</span>
          <span class="text-muted">최근 {{ windowSec }}초</span>
        </div>
        <div class="chart-wrap">
          <canvas ref="chartEl"></canvas>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount } from "vue";
import Chart from "chart.js/auto";

/* ===============================
 * 1) 시간 표시
 * =============================== */
const nowText = ref("");
let timerId = 0;

function pad2(n) {
  return String(n).padStart(2, "0");
}
function updateNow() {
  const d = new Date();
  nowText.value =
    `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())} ` +
    `${pad2(d.getHours())}:${pad2(d.getMinutes())}:${pad2(d.getSeconds())}`;
}

/* ===============================
 * 2) WebSocket 상태/데이터
 * =============================== */
const connected = ref(false);
const lastError = ref(null);
const seq = ref(0);
// true=정상, false=Error, null=대기
const aiStatus = ref(null);
// 마지막으로 WebSocket 메시지를 받은 시각
const lastRxTs = ref(0);
// 사람이 읽기 쉬운 형태의 마지막 수신 시각
const lastRxText = ref("");

const mpu = reactive({
  ax: null, ay: null, az: null,
  gx: null, gy: null, gz: null,
});

const aiText = ref("");

let ws = null;
let retryTimer = 0;

function connectWS() {
  ws = new WebSocket("ws://127.0.0.1:3001");

  ws.onopen = () => {
    connected.value = true;
    lastError.value = null;
  };

  ws.onmessage = (ev) => {
    let msg;
    try {
      msg = JSON.parse(ev.data);
    } catch {
      return;
    }

    // server에서 payload 형식: {type:"tick", seq, connected, mpu, ai}
    if (msg.type === "tick" || msg.type === "snapshot") {
      connected.value = !!msg.connected;
      seq.value = msg.seq ?? seq.value;

      const src = msg.mpu ?? {};
      // 숫자 갱신 (없으면 null 유지)
      mpu.ax = numOrNull(src.AcX);
      mpu.ay = numOrNull(src.AcY);
      mpu.az = numOrNull(src.AcZ);
      mpu.gx = numOrNull(src.GyX);
      mpu.gy = numOrNull(src.GyY);
      mpu.gz = numOrNull(src.GyZ);

      // AI 결과
      if (msg.ai !== undefined && msg.ai !== null) {
        const s = String(msg.ai).toLowerCase();

        if (s === "normal") {
          aiStatus.value = true;
        } else {
          aiStatus.value = false;
        }
      }

      // 마지막 수신 시각
      lastRxTs.value = Date.now();
      lastRxText.value = new Date(lastRxTs.value).toLocaleTimeString();

      // 차트 업데이트
      pushChartPoint({
        ax: mpu.ax, ay: mpu.ay, az: mpu.az,
        gx: mpu.gx, gy: mpu.gy, gz: mpu.gz,
      });
    }
  };

  ws.onclose = () => {
    connected.value = false;
    scheduleReconnect();
  };

  ws.onerror = () => {
    connected.value = false;
    lastError.value = "WebSocket error";
    try { ws.close(); } catch {}
  };
}

function scheduleReconnect() {
  if (retryTimer) return;
  retryTimer = window.setTimeout(() => {
    retryTimer = 0;
    connectWS();
  }, 1000);
}

function numOrNull(v) {
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

function fmt(v) {
  if (v === null || v === undefined) return "-";
  // 소수 4자리 정도 표시
  return Number(v).toFixed(4);
}

/* ===============================
 * 3) Chart.js
 * =============================== */
const chartEl = ref(null);
let chart = null;

const sendHz = 20;
// 최근 10초만 보여주기
const windowSec = 10;
const maxPoints = sendHz * windowSec;

function initChart() {
  const ctx = chartEl.value?.getContext("2d");
  if (!ctx) return;

  chart = new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        { label: "ax", data: [], tension: 0.2, pointRadius: 0 },
        { label: "ay", data: [], tension: 0.2, pointRadius: 0 },
        { label: "az", data: [], tension: 0.2, pointRadius: 0 },
        { label: "gx", data: [], tension: 0.2, pointRadius: 0 },
        { label: "gy", data: [], tension: 0.2, pointRadius: 0 },
        { label: "gz", data: [], tension: 0.2, pointRadius: 0 },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      plugins: {
        legend: { display: true },
      },
      scales: {
        x: { display: true, ticks: { maxTicksLimit: 6 } },
        y: { display: true },
      },
    },
  });
}

function pushChartPoint(v) {
  if (!chart) return;

  const t = new Date().toLocaleTimeString();

  chart.data.labels.push(t);
  chart.data.datasets[0].data.push(v.ax);
  chart.data.datasets[1].data.push(v.ay);
  chart.data.datasets[2].data.push(v.az);
  chart.data.datasets[3].data.push(v.gx);
  chart.data.datasets[4].data.push(v.gy);
  chart.data.datasets[5].data.push(v.gz);

  // 버퍼 초과하면 앞에서 제거
  if (chart.data.labels.length > maxPoints) {
    chart.data.labels.shift();
    for (const ds of chart.data.datasets) ds.data.shift();
  }

  chart.update("none");
}

/* ===============================
 * 4) lifecycle
 * =============================== */
onMounted(() => {
  updateNow();
  timerId = setInterval(updateNow, 1000);

  initChart();
  connectWS();

  // WS 수신이 끊겼는지 감지(옵션)
  const watchdog = setInterval(() => {
    if (!lastRxTs.value) return;
    const gap = Date.now() - lastRxTs.value;
    // 2초 이상 안 오면 끊김으로 표시
    if (gap > 2000) connected.value = false;
  }, 500);

  // cleanup
  onBeforeUnmount(() => clearInterval(watchdog));
});

onBeforeUnmount(() => {
  clearInterval(timerId);
  if (retryTimer) clearTimeout(retryTimer);
  try { ws?.close(); } catch {}
  try { chart?.destroy(); } catch {}
});
</script>

<style scoped>
.db-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.4fr);
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
  margin-bottom: 8px;
  font-size: 0.9rem;
  font-weight: 600;
}

.right-badges {
  display: flex;
  gap: 8px;
  align-items: center;
}

.metric-list {
  list-style: none;
  padding: 0;
  margin: 0;
  border-top: 1px solid #eef1f7;
}

.metric-list li {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #eef1f7;
  font-size: 0.9rem;
}

.ai-box {
  margin-top: 12px;
  padding-top: 10px;
}
.ai-border {
  padding-top: 15px;
  border-top: 1px dashed #d4d9e6;
}
.ai-header {
  display: flex;
  justify-content: space-between;
  font-weight: 600;
  font-size: 0.9rem;
  margin-bottom: 8px;
}

.ai-empty {
  padding: 10px;
  border: 1px dashed #d4d9e6;
  border-radius: 8px;
  color: var(--text-muted);
  font-size: 0.85rem;
}

.ai-error {
  margin-top: 8px;
  color: #b42318;
  font-size: 0.85rem;
}

.chart-wrap {
  height: 450px;
  width: 100%;
}
.ai-status {
  margin: 40px 0 6px;
  padding: 35px 12px;
  border-radius: 12px;
  text-align: center;
  font-size: 2.2rem;
  font-weight: 900;
  letter-spacing: 1px;
}
.ai-status.ok {
  color: #067647;
  background: #ecfdf3;
  border: 4px solid #34d399;
}
.ai-status.err {
  color: #b42318;
  background: #fef3f2;
  border: 4px solid #f87171;
}
</style>
