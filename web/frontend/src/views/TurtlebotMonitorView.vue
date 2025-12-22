<template>
  <section>
    <div class="section-title-row">
      <div>
        <h2 class="section-title">TurtleBot</h2>
        <span class="text-muted">{{ nowText }}</span>
      </div>

      <span class="badge" :class="rosConnected ? 'badge-info' : 'badge-warn'">
        {{ rosConnected ? "LIVE" : "OFFLINE" }}
      </span>
    </div>

    <div class="tb-layout">
      <!-- LEFT -->
      <div class="tb-left">
        <div class="tb-cards">
          <!-- Battery -->
          <div class="content-card tb-card">
            <div class="tb-card-header">
              <span>Robot State</span>
            </div>

            <div class="bar-row">
              <div class="bar-label">
                <span>State of Charge</span>
                <span class="text-muted">{{ socText + '%'}}</span>
              </div>
              <div class="bar-track">
                <div class="bar-fill" :style="{ width: minBar(socPct) - Number(100 -socText) + '%' }"></div>
              </div>
            </div>

            <div class="bar-row">
              <div class="bar-label">
                <span>Voltage</span>
                <span class="text-muted">{{ battery.voltage.toFixed(1) }} V</span>
              </div>
              <div class="bar-track">
                <div class="bar-fill" :style="{ width: minBar(voltPct) + '%' }"></div>
              </div>
            </div>

            <div class="bar-row">
              <div class="bar-label">
                <span>Distance of Obstacles</span>
                <span class="text-muted">{{ obstacle.dist.toFixed(1) }}</span>
              </div>
            </div>
          </div>

          <!-- Motion -->
          <div class="content-card tb-card">
            <div class="tb-card-header">
              <span>Motion</span>
            </div>

            <div class="bar-row">
              <div class="bar-label">
                <span>Linear Velocity</span>
                <span class="text-muted">{{ motion.lin.toFixed(2) }} m/s</span>
              </div>
              <div class="bar-track">
                <div class="bar-fill" :style="{ width: minBar(linPct) + '%' }"></div>
              </div>
            </div>

            <div class="bar-row">
              <div class="bar-label">
                <span>Angular Velocity</span>
                <span class="text-muted">{{ motion.ang.toFixed(2) }} rad/s</span>
              </div>
              <div class="bar-track">
                <div class="bar-fill" :style="{ width: minBar(angPct) + '%' }"></div>
              </div>
            </div>

            <div class="bar-row">
              <div class="bar-label">
                <span>Status</span>
                <span class="text-muted">{{ motion.status }}</span>
              </div>
            </div>
          </div>

          <!-- Navigation -->
          <div class="content-card tb-card">
            <div class="tb-card-header">
              <span>Navigation</span>
            </div>

            <div class="bar-row">
              <div class="bar-label">
                <span>Mission</span>
                <span class="text-muted">{{ nav.missionState }}</span>
              </div>
            </div>

            <div class="bar-row">
              <div class="bar-label">
                <span>Emergency</span>
                <span :class="nav.emergency ? 'emergency_on' : 'text-muted'">{{ nav.emergency ? "On" : "Off" }}</span>
              </div>
            </div>

            <div class="bar-row">
              <div class="bar-label">
                <span>Work wait</span>
                <span class="text-muted">{{ nav.waitRemaining }} s</span>
              </div>
              <div class="bar-track">
                <div class="bar-fill" :style="{ width: waitPct + '%' }"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- RIGHT -->
      <div class="tb-right">
        <div class="content-card tb-map-card">
          <div class="tb-card-header">
            <span>Map</span>
            <span class="text-muted">현재 위치</span>
          </div>

          <div class="map-stage">
            <img class="map-img" :src="mapUrl" alt="slam map" ref="imgRef" @load="onMapLoaded" />
            <canvas class="map-overlay" ref="canvasRef"></canvas>
          </div>

          <div class="tb-map-footer text-muted">
            pose(world): x={{ poseWorld.x.toFixed(2) }}, y={{ poseWorld.y.toFixed(2) }}, yaw={{ poseWorld.yaw.toFixed(2) }}
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, reactive, ref } from "vue";
import * as ROSLIB from "roslib";
import YAML from "js-yaml";

/* ===============================
 * Utils
 * =============================== */
const clamp01 = (v) => Math.min(1, Math.max(0, v));
const toPct = (v01) => Math.round(clamp01(v01) * 100);

// 0%일 때도 최소 4%는 보이게
function minBar(pct, min = 4) {
  if (!rosConnected.value) return min;
  return pct === 0 ? min : pct;
}

/* ===============================
 * Config
 * =============================== */
const mapUrl = "/public/maps/final.png";
const MAP_YAML_URL = "/public/maps/final.yaml";
const ROSBRIDGE_URL = "ws://192.168.110.108:9090";
const UNLOADING_SECONDS = 10;

/* ===============================
 * Time
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
 * State
 * =============================== */
const rosConnected = ref(false);

const battery = reactive({ soc: 0, voltage: 0});
const motion = reactive({ lin: 0, ang: 0, status: "Offline" });
const poseWorld = reactive({ x: 0, y: 0, yaw: 0 });

const nav = reactive({
  missionState: "초기 위치에서 대기",
  emergency: false,
  waitRemaining: 10,
});

// Battery normalization
const VOLT_MIN = 0.0;
const VOLT_MAX = 30.0;
const CURR_MAX_ABS = 5.0;
const LIN_MAX = 0.35;
const ANG_MAX = 1.8;

const obstacle = reactive({ dist: 0 });

const socText = computed(() =>
  battery.soc < 0 ? "N/A" : `${(battery.soc).toFixed(0)}`
);

const socPct = computed(() => (battery.soc < 0 ? 0 : toPct(battery.soc)));

const voltPct = computed(() => {
  const v = (battery.voltage - VOLT_MIN) / (VOLT_MAX - VOLT_MIN);
  return toPct(v);
});

const linPct = computed(() => toPct(Math.abs(motion.lin) / LIN_MAX));
const angPct = computed(() => toPct(Math.abs(motion.ang) / ANG_MAX));

const waitPct = computed(() => {
  // 10초에서 0초로 내려갈 때 progress가 차오르게 (0% -> 100%)
  const done01 = (UNLOADING_SECONDS - nav.waitRemaining) / UNLOADING_SECONDS;
  return toPct(done01);
});

/* ===============================
 * Map Meta (YAML)
 * =============================== */
const mapMeta = reactive({
  resolution: 0.05,
  originX: 0,
  originY: 0,
  imgW: 0,
  imgH: 0,
  scaleX: 1,
  scaleY: 1,
  ready: false,
});

async function loadMapYaml() {
  const res = await fetch(MAP_YAML_URL);
  const y = YAML.load(await res.text());
  mapMeta.resolution = y.resolution;
  mapMeta.originX = y.origin[0];
  mapMeta.originY = y.origin[1];
  mapMeta.ready = true;
}

/* ===============================
 * Canvas / Overlay
 * =============================== */
const imgRef = ref(null);
const canvasRef = ref(null);

// 로봇 이미지
const robotImg = new Image();
let robotImgReady = false;
robotImg.onload = () => (robotImgReady = true);

function worldToCanvas(x, y) {
  if (!mapMeta.ready) return { px: 0, py: 0 };

  const u = (x - mapMeta.originX) / mapMeta.resolution;
  const v = (y - mapMeta.originY) / mapMeta.resolution;

  return {
    px: u * mapMeta.scaleX,
    py: (mapMeta.imgH - v) * mapMeta.scaleY,
  };
}

async function onMapLoaded() {
  const img = imgRef.value;
  const canvas = canvasRef.value;
  if (!img || !canvas) return;

  const rect = img.getBoundingClientRect();
  canvas.width = rect.width;
  canvas.height = rect.height;

  mapMeta.imgW = img.naturalWidth;
  mapMeta.imgH = img.naturalHeight;
  mapMeta.scaleX = canvas.width / mapMeta.imgW;
  mapMeta.scaleY = canvas.height / mapMeta.imgH;

  if (!mapMeta.ready) await loadMapYaml();
  drawOverlay();
}

function drawRobot(ctx, x, y, yaw) {
  if (!robotImgReady) return;

  const size = 32;
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(yaw);
  ctx.drawImage(robotImg, -size, -size, size * 2, size * 2);
  ctx.restore();
}

function drawOverlay() {
  const canvas = canvasRef.value;
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const { px, py } = worldToCanvas(poseWorld.x, poseWorld.y);
  drawRobot(ctx, px, py, poseWorld.yaw);

  // 점 표시(옵션)
  ctx.beginPath();
  ctx.arc(px, py, 7, 0, Math.PI * 2);
  ctx.fillStyle = "rgba(237,28,36,0.8)";
  ctx.fill();
}

function handleResize() {
  onMapLoaded();
}

/* ===============================
 * ROS (rosbridge)
 * =============================== */
let ros;
let batteryTopic, odomTopic, amclTopic, scanTopic;
let missionTopic, emergencyTopic, waitTopic;

function quatToYaw(q) {
  return Math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z));
}

// ===== Motion smoothing params =====
const LIN_DEADBAND = 0.0;   // m/s, 이 이하로는 0으로 고정
const ANG_DEADBAND = 0.05;   // rad/s, 이 이하로는 0으로 고정

const LIN_MAX_JUMP = 0.25;   // 1프레임에 이 이상 튀면 이상치로 보고 무시 (옵션)
const ANG_MAX_JUMP = 2.5;

const EMA_ALPHA = 0.35;      // 0~1 (작을수록 더 부드러움)

// helpers
const safeNum = (v) => (typeof v === "number" && Number.isFinite(v) ? v : null);

function deadband(v, eps) {
  return Math.abs(v) < eps ? 0 : v;
}

function ema(prev, next, alpha) {
  return prev + alpha * (next - prev);
}

function clampJump(prev, next, maxJump) {
  // 너무 큰 순간 튐은 무시하고 이전값 유지
  return Math.abs(next - prev) > maxJump ? prev : next;
}


function computeStatus(l, a) {
  if (Math.abs(l) < 0.0001 && Math.abs(a) < 0.0001) return "Stopped";
  else return "Cruising";
}

function connectRos() {
  ros = new ROSLIB.Ros({ url: ROSBRIDGE_URL });

  ros.on("connection", () => {
    console.log("ROS CONNECTED");
    rosConnected.value = true;
    motion.status = "Connected";

    // Battery (실기에서 publish 되면 값 들어옴)
    batteryTopic = new ROSLIB.Topic({
      ros,
      name: "/battery_state",
      messageType: "sensor_msgs/msg/BatteryState",
    });
    batteryTopic.subscribe((m) => {
      battery.soc = (m.percentage ?? -1);
      battery.voltage = m.voltage ?? 0;
    });

    scanTopic = new ROSLIB.Topic({
      ros,
      name: "/scan",
      messageType: "sensor_msgs/msg/LaserScan",
    });

    scanTopic.subscribe((m) => {
      const rmin = m.range_min ?? 0.12;
      const rmax = m.range_max ?? 3.5;

      let minDist = Infinity;
      for (const r of m.ranges) {
        if (!Number.isFinite(r)) continue;
        if (r <= 0) continue;
        if (r < rmin || r > rmax) continue;
        if (r < minDist) minDist = r;
      }

      if (Number.isFinite(minDist)) {
        obstacle.dist = minDist;
      }
    });


    // Odom
    odomTopic = new ROSLIB.Topic({
      ros,
      name: "/odom",
      messageType: "nav_msgs/Odometry",
    });
    const safeNum = (v) => (typeof v === "number" && Number.isFinite(v) ? v : null);

    odomTopic.subscribe((m) => {
      let lin = safeNum(m?.twist?.twist?.linear?.x);
      let ang = safeNum(m?.twist?.twist?.angular?.z);

      // 값이 없으면 업데이트 스킵 (이전값 유지)
      if (lin === null && ang === null) return;

      // 없으면 0으로 만들지 말고 "이전값"을 기반으로 처리
      if (lin === null) lin = motion.lin;
      if (ang === null) ang = motion.ang;

      // 1) 데드존: 0 근처 흔들림 제거
      lin = deadband(lin, LIN_DEADBAND);
      ang = deadband(ang, ANG_DEADBAND);

      // 2) 순간 점프 방지(옵션이지만 실기에서 효과 큼)
      lin = clampJump(motion.lin, lin, LIN_MAX_JUMP);
      ang = clampJump(motion.ang, ang, ANG_MAX_JUMP);

      // 3) EMA로 부드럽게
      motion.lin = ema(motion.lin, lin, EMA_ALPHA);
      motion.ang = ema(motion.ang, ang, EMA_ALPHA);

      // status도 "필터된 값" 기준으로
      motion.status = computeStatus(motion.lin, motion.ang);
    });


    // AMCL
    amclTopic = new ROSLIB.Topic({
      ros,
      name: "/amcl_pose",
      messageType: "geometry_msgs/PoseWithCovarianceStamped",
    });
    amclTopic.subscribe((m) => {
      poseWorld.x = m.pose.pose.position.x ?? 0;
      poseWorld.y = m.pose.pose.position.y ?? 0;
      poseWorld.yaw = quatToYaw(m.pose.pose.orientation);
      drawOverlay();
    });

    // ===== UI Topics from your NAV node =====
    missionTopic = new ROSLIB.Topic({
      ros,
      name: "/ui/mission_state",
      messageType: "std_msgs/msg/String",
    });
    missionTopic.subscribe((m) => {
      nav.missionState = m.data ?? "초기 위치에서 대기";
    });

    emergencyTopic = new ROSLIB.Topic({
      ros,
      name: "/ui/emergency",
      messageType: "std_msgs/msg/Bool",
    });
    emergencyTopic.subscribe((m) => {
      nav.emergency = !!m.data;
    });

    waitTopic = new ROSLIB.Topic({
      ros,
      name: "/ui/wait_remaining",
      messageType: "std_msgs/msg/Int32",
    });
    waitTopic.subscribe((m) => {
      const v = Number(m.data);
      nav.waitRemaining = Number.isFinite(v) ? v : 0;
    });
  });

  ros.on("error", (e) => {
    console.error("ROS ERROR", e);
    rosConnected.value = false;
    motion.status = "Offline";
  });

  ros.on("close", () => {
    console.warn("ROS CLOSED");
    rosConnected.value = false;
    motion.status = "Offline";
  });
}

function disconnectRos() {
  batteryTopic?.unsubscribe();
  odomTopic?.unsubscribe();
  amclTopic?.unsubscribe();
  scanTopic?.unsubscribe();

  missionTopic?.unsubscribe();
  emergencyTopic?.unsubscribe();
  waitTopic?.unsubscribe();

  ros?.close();
}

/* ===============================
 * Lifecycle
 * =============================== */
onMounted(() => {
  updateNow();
  timerId = setInterval(updateNow, 1000);
  connectRos();
  window.addEventListener("resize", handleResize);
});

onBeforeUnmount(() => {
  clearInterval(timerId);
  disconnectRos();
  window.removeEventListener("resize", handleResize);
});
</script>

<style scoped>
.tb-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  align-items: start;
}

@media (max-width: 1100px) {
  .tb-layout {
    grid-template-columns: 1fr;
  }
}

.tb-cards {
  margin-top: 15px;
  display: grid;
  gap: 12px;
}

.tb-card {
  padding: 12px 14px 14px;
}

.tb-card-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
  font-size: 0.9rem;
  font-weight: 500;
}

.tb-map-card {
  margin-top: 15px;
  padding: 12px 14px 14px;
}

.map-stage {
  position: relative;
  width: 100%;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid #eef1f7;
  background: #fff;
}

.map-img {
  width: 100%;
  height: auto;
  display: block;
}

.map-overlay {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.tb-map-footer {
  margin-top: 8px;
  font-size: 0.82rem;
}
</style>
