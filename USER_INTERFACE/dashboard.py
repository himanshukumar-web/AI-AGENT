"""
JARVIS AI — Lightweight Local Status Dashboard (Phase 4)
Zero-dependency HTTP server providing a real-time monitor for JARVIS subsystems.
Start with: python main.py --dashboard
"""

import http.server
import json
import socketserver
import threading
from typing import Any, Dict


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    """Serves the JARVIS status dashboard and API endpoints."""

    def do_GET(self):
        if self.path == "/api/status":
            self._send_json(self._get_status_data())
        elif self.path in ["/", "/index.html"]:
            self._send_html(self._render_dashboard_html())
        else:
            self.send_error(404, "Endpoint not found")

    def _get_status_data(self) -> Dict[str, Any]:
        """Collect real-time system metrics without exposing secrets."""
        try:
            from BRAIN.UTILS.diagnostics import doctor
            from BRAIN.CORE_AGENT.task_manager import task_manager
            from BRAIN.TOOLS.action_logger import action_logger
            from BRAIN.MEMORY.memory_manager import memory_manager

            diag = doctor.run_diagnostics()
            current_task = task_manager.get_current_task()
            recent_actions = action_logger.get_recent_actions(limit=5)
            facts_count = len(memory_manager.recall_facts())

            return {
                "diagnostics": diag,
                "current_task": current_task.to_dict() if current_task else None,
                "recent_actions": recent_actions,
                "memory_facts_count": facts_count,
            }
        except Exception as e:
            return {"error": str(e)}

    def _send_json(self, data: Dict[str, Any]):
        content = json.dumps(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _send_html(self, html_str: str):
        content = html_str.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _render_dashboard_html(self) -> str:
        return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>JARVIS AI — System Status Dashboard</title>
  <style>
    * { margin:0; padding:0; box-sizing:border-box; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
    body { background: #0b0f19; color: #e2e8f0; padding: 24px; }
    .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1e293b; padding-bottom: 16px; margin-bottom: 24px; }
    .title { font-size: 24px; font-weight: 700; color: #38bdf8; display: flex; align-items: center; gap: 8px; }
    .badge { background: #0284c7; color: white; padding: 4px 10px; border-radius: 9999px; font-size: 12px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-bottom: 24px; }
    .card { background: #131c2e; border: 1px solid #1e293b; border-radius: 12px; padding: 20px; }
    .card-title { font-size: 14px; text-transform: uppercase; color: #94a3b8; margin-bottom: 12px; letter-spacing: 0.05em; }
    .status-item { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #1e293b; font-size: 14px; }
    .status-ok { color: #4ade80; font-weight: 600; }
    .status-warn { color: #facc15; font-weight: 600; }
    .table-container { background: #131c2e; border: 1px solid #1e293b; border-radius: 12px; padding: 20px; margin-top: 16px; }
    table { width: 100%; border-collapse: collapse; font-size: 14px; }
    th { text-align: left; padding: 10px; color: #94a3b8; border-bottom: 1px solid #1e293b; }
    td { padding: 10px; border-bottom: 1px solid #0f172a; }
  </style>
</head>
<body>
  <div class="header">
    <div class="title">🤖 JARVIS AI — Live Agent Dashboard</div>
    <div class="badge">Phase 4 Active</div>
  </div>
  <div class="grid">
    <div class="card">
      <div class="card-title">Subsystem Health</div>
      <div id="diagnostics-list">Loading diagnostics...</div>
    </div>
    <div class="card">
      <div class="card-title">Active Task</div>
      <div id="active-task-info">Checking task manager...</div>
    </div>
  </div>
  <div class="table-container">
    <div class="card-title">Recent Tool Actions & Audits</div>
    <table>
      <thead>
        <tr><th>Timestamp</th><th>Tool</th><th>Duration (ms)</th><th>Status</th></tr>
      </thead>
      <tbody id="actions-table-body">
        <tr><td colspan="4">Loading actions...</td></tr>
      </tbody>
    </table>
  </div>
  <script>
    async function refreshStatus() {
      try {
        const res = await fetch('/api/status');
        const data = await res.json();
        const diagDiv = document.getElementById('diagnostics-list');
        if (data.diagnostics) {
          diagDiv.innerHTML = Object.entries(data.diagnostics).map(([k, v]) => `
            <div class="status-item">
              <span>${k.toUpperCase()}</span>
              <span class="${v.status === 'OK' ? 'status-ok' : 'status-warn'}">${v.status}</span>
            </div>
          `).join('');
        }
        const taskDiv = document.getElementById('active-task-info');
        if (data.current_task) {
          taskDiv.innerHTML = `<strong>${data.current_task.name}</strong><br>Step ${data.current_task.current_step}/${data.current_task.total_steps} (${data.current_task.progress_percent}%)`;
        } else {
          taskDiv.innerHTML = '<em>IDLE (No active tasks)</em>';
        }
        const tbody = document.getElementById('actions-table-body');
        if (data.recent_actions && data.recent_actions.length > 0) {
          tbody.innerHTML = data.recent_actions.map(a => `
            <tr>
              <td>${a.timestamp.substring(11, 19)}</td>
              <td>${a.tool_name}</td>
              <td>${a.duration_ms.toFixed(1)}</td>
              <td class="${a.success ? 'status-ok' : 'status-warn'}">${a.success ? 'SUCCESS' : 'FAILED'}</td>
            </tr>
          `).join('');
        }
      } catch (e) {
        console.error(e);
      }
    }
    refreshStatus();
    setInterval(refreshStatus, 3000);
  </script>
</body>
</html>"""


def start_dashboard_server(port: int = 7860, run_in_background: bool = True):
    """Launch the lightweight dashboard HTTP server."""
    handler = DashboardHandler
    server = socketserver.TCPServer(("127.0.0.1", port), handler)
    print(f"\n[DASHBOARD] JARVIS Live Dashboard active at: http://127.0.0.1:{port}/")
    if run_in_background:
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        return server
    else:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.server_close()
