// web/backend/src/index.js
const express = require("express");
const cors = require("cors");
const path = require("path");

const logsRouter = require("./routes/logs");

const app = express();
const PORT = 3000;

// CORS + JSON 파싱
app.use(cors());
app.use(express.json());

// 간단한 상태 확인용
app.get("/api/health", (req, res) => {
  res.json({ ok: true });
});

// /api/logs 라우터 연결
app.use("/api/logs", logsRouter);

const HOST = "0.0.0.0";

// 서버 시작
app.listen(PORT, HOST, () => {
  console.log(`Backend listening on http://${HOST}:${PORT}`);
});
