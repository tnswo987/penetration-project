const express = require("express");
const http = require("http");
const { Server } = require("socket.io");
const cors = require("cors");

const logsRouter = require("./routes/logs");

const app = express();
const server = http.createServer(app);
const io = new Server(server, {
  cors: {
    origin: "*", // 개발 단계라 일단 모두 허용
  },
});

app.use(cors());
app.use(express.json());

// health check
app.get("/health", (req, res) => {
  res.json({ status: "ok" });
});

// REST API
app.use("/api/logs", logsRouter);

// WebSocket 연결 로그 정도만
io.on("connection", (socket) => {
  console.log("client connected:", socket.id);
  socket.on("disconnect", () => {
    console.log("client disconnected:", socket.id);
  });
});

// 나중에 다른 모듈에서 쓰고 싶을 때를 대비해서
app.set("io", io);

const PORT = 3001;
server.listen(PORT, () => {
  console.log(`Backend server listening on port ${PORT}`);
});
