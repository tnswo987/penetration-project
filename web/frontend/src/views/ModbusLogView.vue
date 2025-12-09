<template>
  <section>
    <h2>Modbus Log Viewer</h2>
    <p class="desc">pymodbus로 쌓이는 로그를 여기서 확인할 예정이야. 지금은 백엔드 mock 데이터 연동 상태.</p>

    <button class="reload-btn" @click="fetchLogs">새로고침</button>

    <table v-if="logs.length" class="log-table">
      <thead>
        <tr>
          <th>ID</th>
          <th>시간</th>
          <th>레벨</th>
          <th>메시지</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="log in logs" :key="log.id">
          <td>{{ log.id }}</td>
          <td>{{ log.timestamp }}</td>
          <td>{{ log.level }}</td>
          <td>{{ log.message }}</td>
        </tr>
      </tbody>
    </table>

    <p v-else class="empty">표시할 로그가 없습니다.</p>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import api from '../services/api';

const logs = ref([]);

const fetchLogs = async () => {
  try {
    const res = await api.get('/api/logs');
    logs.value = res.data;
  } catch (err) {
    console.error('로그 불러오기 실패:', err);
  }
};

onMounted(() => {
  fetchLogs();
});
</script>

<style scoped>
h2 {
  margin: 0 0 0.5rem;
  font-size: 1.2rem;
}

.desc {
  margin-bottom: 1rem;
  font-size: 0.9rem;
  color: #666;
}

.reload-btn {
  margin-bottom: 0.75rem;
  padding: 0.3rem 0.9rem;
  border-radius: 4px;
  border: 1px solid #ccc;
  background: #fafafa;
  cursor: pointer;
}

.log-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.log-table th,
.log-table td {
  border: 1px solid #e0e0e0;
  padding: 0.4rem 0.6rem;
}

.log-table th {
  background: #fafafa;
  text-align: left;
}

.empty {
  margin-top: 1rem;
  color: #888;
}
</style>
