<template>
  <section>
    <div class="section-title-row">
      <div>
        <h2 class="section-title">Modbus Log</h2>
         <p class="section-caption">
          Update Cycle (2sec)
        </p>
      </div>

      <!-- 로그 삭제 버튼 -->
      <button
        class="badge badge-danger badge-clickable"
        type="button"
        @click="clearLogs"
        :disabled="deleting"
      >
        {{ deleting ? '삭제 중...' : '로그 삭제' }}
      </button>
    </div>

    <table class="table" v-if="logs.length">
      <thead>
        <tr>
          <th>#</th>
          <th>Timestamp</th>
          <th>Level</th>
          <th>Device</th>
          <th>Message</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="log in logs" :key="log.id">
          <td>{{ log.id }}</td>
          <td>{{ log.time }}</td>
          <td>
            <span
              class="badge"
              :class="{
                'badge-info': log.level === 'INFO',
                'badge-warn': log.level === 'WARN',
                'badge-danger': log.level === 'ERROR'
              }"
            >
              {{ log.level }}
            </span>
          </td>
          <td>{{ log.device }}</td>
          <td>{{ log.message }}</td>
        </tr>
      </tbody>
    </table>

    <p v-else class="text-muted">
      표시할 로그가 없습니다.
    </p>
  </section>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import api from '../services/api';

const logs = ref([]);
const deleting = ref(false);
const pollingId = ref(null);

// 로그 가져오기
const fetchLogs = async () => {
  try {
    const res = await api.get('/logs');
    logs.value = res.data;
  } catch (err) {
    console.error('로그 불러오기 실패:', err);
    alert('로그를 불러오는 중 오류가 발생했습니다.');
  }
};

// 로그 삭제
const clearLogs = async () => {
  if (!confirm('정말 모든 로그를 삭제하시겠습니까?')) return;

  deleting.value = true;
  try {
    await api.delete('/logs');
    logs.value = [];
  } catch (err) {
    console.error('로그 삭제 실패:', err);
    alert('로그 삭제 중 오류가 발생했습니다.');
  } finally {
    deleting.value = false;
  }
};

onMounted(() => {
  fetchLogs();
  pollingId.value = setInterval(fetchLogs, 2000);
});

onUnmounted(() => {
  if (pollingId.value) {
    clearInterval(pollingId.value);
  }
});

</script>

<style scoped>
.badge-clickable {
  cursor: pointer;
  user-select: none;
}
.badge-clickable:disabled {
  opacity: 0.6;
  cursor: default;
}
</style>
