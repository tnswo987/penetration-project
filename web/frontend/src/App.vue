<template>
  <div class="app">
    <header class="app-header">
      <h1>Penetration Project Dashboard</h1>
      <p class="subtitle">Modbus · Dobot · TurtleBot 관제</p>
    </header>

    <nav class="tab-nav">
      <RouterLink to="/logs" class="tab" active-class="active">Modbus Log</RouterLink>
      <RouterLink to="/dobot" class="tab" active-class="active">Dobot Sensor</RouterLink>
      <RouterLink to="/turtlebot" class="tab" active-class="active">TurtleBot Monitor</RouterLink>
    </nav>

    <main class="app-main">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
// script 따로 필요 없음
</script>

<style scoped>
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.app-header {
  padding: 1rem 2rem;
  border-bottom: 1px solid #e5e5e5;
}

.app-header h1 {
  margin: 0;
  font-size: 1.4rem;
  font-weight: 700;
}

.subtitle {
  margin: 0.2rem 0 0;
  font-size: 0.9rem;
  color: #666;
}

.tab-nav {
  display: flex;
  gap: 0.75rem;
  padding: 0.75rem 2rem;
  border-bottom: 1px solid #f0f0f0;
}

.tab {
  text-decoration: none;
  padding: 0.4rem 0.9rem;
  border-radius: 999px;
  border: 1px solid transparent;
  font-size: 0.9rem;
  color: #444;
}

.tab.active {
  border-color: #444;
  font-weight: 600;
}

.app-main {
  padding: 1rem 2rem 2rem;
  flex: 1;
}
</style>
