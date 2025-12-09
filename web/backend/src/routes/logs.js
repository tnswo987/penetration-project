const express = require("express");
const router = express.Router();

// GET /api/logs
router.get("/", async (req, res) => {
  // TODO: 나중에 pymodbus 로그 파일/DB와 연동
  const mockLogs = [
    {
      id: 1,
      timestamp: "2025-12-09 22:00:00",
      level: "INFO",
      message: "Modbus connected",
    },
    {
      id: 2,
      timestamp: "2025-12-09 22:01:10",
      level: "WARN",
      message: "Voltage threshold exceeded",
    },
  ];
  res.json(mockLogs);
});

module.exports = router;
