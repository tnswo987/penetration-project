// web/backend/src/routes/logs.js
const express = require("express");
const fs = require("fs").promises;
const path = require("path");

const router = express.Router();

const LOG_PATH = path.resolve(__dirname, "../../../..", "PYTHON", "log.txt");
console.log("[LOG_PATH]", LOG_PATH);

// 한 줄을 JSON 객체로 변환
function parseLogLine(line, index) {
  if (!line.trim()) return null;

  const parts = line.split(",");
  const [idRaw, time, level, device, ...msgParts] = parts;

  const id = idRaw && !Number.isNaN(Number(idRaw)) ? Number(idRaw) : index + 1;
  const message = (msgParts || []).join(",").trim();

  return {
    id,
    time: (time || "").trim(),
    level: (level || "").trim(),
    device: (device || "").trim(),
    message,
  };
}

// GET /api/logs  → log.txt 읽어서 JSON으로 반환
router.get("/", async (req, res) => {
  try {
    const raw = await fs.readFile(LOG_PATH, "utf8");
    console.log("[logs] raw content length:", raw.length);

    const lines = raw.split("\n");
    const logs = lines
      .map((line, idx) => parseLogLine(line, idx))
      .filter(Boolean);

    res.json(logs);
  } catch (err) {
    if (err.code === "ENOENT") {
      console.warn("[logs] log.txt not found:", LOG_PATH);
      return res.json([]); // 파일 없으면 빈 배열
    }
    console.error("[logs] read error:", err);
    res.status(500).json({ error: "Failed to read log file" });
  }
});

// DELETE /api/logs  → log.txt 내용 비우기
router.delete("/", async (req, res) => {
  try {
    await fs.writeFile(LOG_PATH, "", "utf8");
    console.log("[logs] log.txt cleared");
    res.json({ ok: true });
  } catch (err) {
    console.error("[logs] clear error:", err);
    res.status(500).json({ error: "Failed to clear log file" });
  }
});

module.exports = router;
