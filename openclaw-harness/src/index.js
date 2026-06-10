/**
 * OpenClaw gateway — forwards chat requests to MnemOS memory server.
 */

require("dotenv").config();
const express = require("express");
const cors = require("cors");
const axios = require("axios");

const PORT = process.env.PORT || 3000;
const MCP_SERVER_URL = process.env.MCP_SERVER_URL || "http://localhost:8000";

const app = express();
app.use(cors());
app.use(express.json());

app.get("/health", async (_req, res) => {
  try {
    const upstream = await axios.get(`${MCP_SERVER_URL}/health`, { timeout: 5000 });
    res.json({
      status: "ok",
      openclaw: true,
      mnemos: upstream.data,
    });
  } catch (error) {
    res.status(503).json({
      status: "degraded",
      openclaw: true,
      mnemos: "unreachable",
      error: error.message,
    });
  }
});

app.post("/chat", async (req, res) => {
  try {
    const { user_id, session_id, message } = req.body;
    const upstream = await axios.post(
      `${MCP_SERVER_URL}/chat`,
      { user_id, session_id, message },
      { timeout: 60000 }
    );
    res.json(upstream.data);
  } catch (error) {
    const status = error.response?.status || 502;
    res.status(status).json({
      error: "Failed to reach MnemOS memory server",
      detail: error.message,
    });
  }
});

app.use((err, _req, res, _next) => {
  res.status(500).json({ error: err.message });
});

app.listen(PORT, () => {
  console.log(`OpenClaw Harness running on port ${PORT}, routing to ${MCP_SERVER_URL}`);
});
