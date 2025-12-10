<template>
  <div class="app-shell">
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-inner">
        <div class="sidebar-logo">
          <span>Automated Process</span>
          <div class="sidebar-logo-sub">Live Dashboard</div>
        </div>

        <div class="sidebar-divider"></div>

        <nav class="sidebar-nav">
          <RouterLink to="/logs" class="sidebar-zone zone-logs" active-class="active">
            <div class="sidebar-label">Modbus Log</div>
          </RouterLink>

          <div class="sidebar-divider"></div>

          <RouterLink to="/dobot" class="sidebar-zone zone-dobot" active-class="active">
            <div class="sidebar-label">Dobot</div>
          </RouterLink>

          <div class="sidebar-divider"></div>

          <RouterLink to="/turtlebot" class="sidebar-zone zone-turtle" active-class="active">
            <div class="sidebar-label">TurtleBot</div>
          </RouterLink>
        </nav>
      </div>
    </aside>

    <!-- Main -->
    <main class="main-area">
      <header class="topbar">
        <div>
          <div class="topbar-title">Realtime Monitor</div>
        </div>
        <div class="topbar-right">
          Copyright 2025. Kwon, Ryu All rights reserved.
        </div>
      </header>

      <div class="main-content">
        <div class="content-card">
          <RouterView />
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
// 라우터만 사용하므로 별도 로직 없음
</script>
