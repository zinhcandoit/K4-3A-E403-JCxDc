#!/usr/bin/env python3
"""
FalkorDB Knowledge Graph Visualizer for VLearn Track D3.
Vị trí: codebase/ui/visualize_graph.py
Tái hiện 100% giao diện & phong cách đồ thị mạng FalkorDB Browser / RedisInsight:
- Thanh điều hướng icon rail bên trái với logo FalkorDB
- Bảng 'Graph Info' (Nodes, Edges, Property Keys, Color Badges)
- Thanh Cypher query trên cùng kèm nút [RUN] và bộ lọc tìm kiếm
- Canvas đồ thị dạng chùm sao / tinh vân phát sáng (Star-cluster force simulation)
- Bảng Inspector chi tiết thuộc tính khi click vào từng node
- Thanh công cụ điều khiển vật lý, phóng to/thu nhỏ, fit màn hình
"""

import os
import sys
import json
import argparse
import webbrowser
from typing import Dict, Any

# Đảm bảo import được backend và db từ thư mục codebase
ui_dir = os.path.abspath(os.path.dirname(__file__))
codebase_dir = os.path.abspath(os.path.join(ui_dir, ".."))
if codebase_dir not in sys.path:
    sys.path.insert(0, codebase_dir)

from db.graph_service import GraphService


def generate_graph_html(graph_data: Dict[str, Any], height: str = "720px") -> str:
    """
    Tạo mã HTML/CSS/JS độc lập cho đồ thị mạng tương tác
    Mô phỏng 100% chuẩn giao diện FalkorDB Browser.
    """
    raw_nodes = graph_data.get("nodes", [])
    raw_edges = graph_data.get("edges", [])

    total_nodes = len(raw_nodes)
    total_edges = len(raw_edges)
    covered_nodes = sum(1 for node in raw_nodes if node.get("status") == "COVERED")
    uncovered_nodes = sum(1 for node in raw_nodes if node.get("status") == "UNCOVERED")

    # Statistics for 5 pedagogical node types
    concept_count = sum(1 for node in raw_nodes if node.get("node_type") == "Concept" or not node.get("node_type"))
    misconception_count = sum(1 for node in raw_nodes if node.get("node_type") == "Misconception")
    tradeoff_count = sum(1 for node in raw_nodes if node.get("node_type") == "Tradeoff")
    mechanism_count = sum(1 for node in raw_nodes if node.get("node_type") == "Mechanism")
    counter_example_count = sum(1 for node in raw_nodes if node.get("node_type") == "CounterExample")

    # Statistics for 8 relationship edge types
    prerequisite_count = sum(1 for edge in raw_edges if edge.get("type") == "PREREQUISITE_FOR")
    deep_dive_count = sum(1 for edge in raw_edges if edge.get("type") == "DEEP_DIVE_INTO")
    alternative_path_count = sum(1 for edge in raw_edges if edge.get("type") == "ALTERNATIVE_PATH")
    pitfall_count = sum(1 for edge in raw_edges if edge.get("type") in ["HAS_COMMON_PITFALL", "CONTRADICTS"])
    tradeoff_edge_count = sum(1 for edge in raw_edges if edge.get("type") == "HAS_TRADEOFF")
    mechanism_edge_count = sum(1 for edge in raw_edges if edge.get("type") == "DEPENDS_ON_MECHANISM")
    counter_example_edge_count = sum(1 for edge in raw_edges if edge.get("type") == "HAS_COUNTER_EXAMPLE")

    prop_keys = ["id", "name", "node_type", "status", "citation", "page", "category", "track", "core_truth", "probe_question"]

    nodes_json = json.dumps(raw_nodes, ensure_ascii=False)
    edges_json = json.dumps(raw_edges, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <title>Sơ Đồ Lộ Trình Kiến Thức — VLearn</title>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.9/standalone/umd/vis-network.min.js"></script>
  <style>
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }}
    body, html {{
      width: 100%;
      height: 100%;
      overflow: hidden;
      background-color: #0b0d13;
      color: #e2e8f0;
    }}

    /* Main FalkorDB Browser Shell */
    #falkordb-shell {{
      display: flex;
      width: 100%;
      height: {height};
      position: relative;
      background: #0b0d13;
    }}

    /* Left Icon Rail */
    .icon-rail {{
      width: 48px;
      height: 100%;
      background: #08090f;
      border-right: 1px solid #1a1d29;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 12px 0;
      z-index: 20;
      gap: 16px;
    }}
    .falkor-logo {{
      width: 32px;
      height: 32px;
      border-radius: 8px;
      background: linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      color: #ffffff;
      font-size: 17px;
      box-shadow: 0 0 12px rgba(236, 72, 153, 0.4);
      cursor: pointer;
    }}
    .rail-btn {{
      width: 34px;
      height: 34px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #94a3b8;
      cursor: pointer;
      transition: all 0.2s;
      font-size: 15px;
    }}
    .rail-btn:hover, .rail-btn.active {{
      background: #4f46e522;
      color: #818cf8;
      border: 1px solid #6366f144;
    }}

    /* Left Drawer: Graph Info */
    .graph-info-drawer {{
      width: 260px;
      height: 100%;
      background: #0f111a;
      border-right: 1px solid #1c2233;
      display: flex;
      flex-direction: column;
      padding: 14px 16px;
      z-index: 15;
      overflow-y: auto;
    }}
    .drawer-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 13.5px;
      font-weight: 700;
      color: #f1f5f9;
      margin-bottom: 14px;
      padding-bottom: 8px;
      border-bottom: 1px solid #1a2030;
    }}
    .section-title {{
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.6px;
      color: #64748b;
      margin: 12px 0 6px 0;
      display: flex;
      justify-content: space-between;
    }}
    .pill-list {{
      display: flex;
      flex-direction: column;
      gap: 6px;
      margin-bottom: 8px;
    }}
    .info-pill {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: #151926;
      border: 1px solid #20273c;
      border-radius: 6px;
      padding: 5px 10px;
      font-size: 11.5px;
      color: #cbd5e1;
      cursor: pointer;
      transition: all 0.15s;
    }}
    .info-pill:hover {{
      background: #1c2236;
      border-color: #38bdf8;
    }}
    .pill-left {{
      display: flex;
      align-items: center;
      gap: 7px;
    }}
    .pill-dot {{
      width: 8px;
      height: 8px;
      border-radius: 50%;
    }}
    .dot-cyan {{ background: #38bdf8; box-shadow: 0 0 6px #38bdf8; }}
    .dot-green {{ background: #10b981; box-shadow: 0 0 6px #10b981; }}
    .dot-orange {{ background: #f97316; box-shadow: 0 0 6px #f97316; }}
    .dot-purple {{ background: #a855f7; box-shadow: 0 0 6px #a855f7; }}
    .pill-count {{
      background: #232a3e;
      color: #94a3b8;
      border-radius: 10px;
      padding: 1px 7px;
      font-size: 10.5px;
      font-weight: 600;
    }}
    .prop-chip-cloud {{
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
      margin-top: 6px;
    }}
    .prop-chip {{
      background: #161b29;
      border: 1px solid #222a3d;
      color: #94a3b8;
      border-radius: 4px;
      padding: 2px 7px;
      font-size: 10.5px;
      font-family: "Fira Code", monospace;
    }}

    /* Main Viewport */
    .viewport {{
      flex: 1;
      height: 100%;
      position: relative;
      background: radial-gradient(circle at 60% 45%, #141828 0%, #0a0b12 85%);
      overflow: hidden;
    }}

    /* Top Cypher & Query Header */
    .cypher-topbar {{
      position: absolute;
      top: 10px;
      left: 14px;
      right: 14px;
      display: flex;
      gap: 10px;
      align-items: center;
      background: rgba(15, 18, 28, 0.9);
      backdrop-filter: blur(14px);
      border: 1px solid #252e44;
      border-radius: 8px;
      padding: 6px 12px;
      z-index: 10;
      box-shadow: 0 6px 20px rgba(0,0,0,0.5);
    }}
    .graph-selector {{
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 12.5px;
      font-weight: 600;
      color: #38bdf8;
      white-space: nowrap;
      padding-right: 10px;
      border-right: 1px solid #252e44;
    }}
    .cypher-code {{
      flex: 1;
      background: #090c15;
      border: 1px solid #1c2438;
      border-radius: 6px;
      color: #cbd5e1;
      font-family: "Fira Code", monospace;
      font-size: 12px;
      padding: 6px 10px;
      outline: none;
    }}
    .run-btn {{
      background: #4f46e5;
      color: #ffffff;
      border: none;
      border-radius: 6px;
      padding: 6px 16px;
      font-size: 12px;
      font-weight: 700;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 5px;
      transition: background 0.15s;
    }}
    .run-btn:hover {{
      background: #4338ca;
    }}
    .search-filter {{
      background: #090c15;
      border: 1px solid #1c2438;
      border-radius: 6px;
      color: #e2e8f0;
      font-size: 11.5px;
      padding: 5px 10px;
      width: 140px;
      outline: none;
    }}

    /* Graph Canvas */
    #graph-canvas {{
      width: 100%;
      height: 100%;
    }}

    /* Right Node Inspector Drawer (FalkorDB Property Panel) */
    .node-inspector {{
      position: absolute;
      top: 60px;
      right: 14px;
      width: 340px;
      max-height: calc(100% - 110px);
      overflow-y: auto;
      background: rgba(14, 18, 28, 0.95);
      backdrop-filter: blur(16px);
      border: 1px solid #28344e;
      border-radius: 10px;
      padding: 14px;
      z-index: 12;
      display: none;
      box-shadow: 0 10px 30px rgba(0,0,0,0.6);
      animation: slideIn 0.2s ease-out;
    }}
    .inspector-head {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 12px;
      padding-bottom: 8px;
      border-bottom: 1px solid #202b40;
    }}
    .inspector-title {{
      font-size: 13.5px;
      font-weight: 700;
      color: #f1f5f9;
    }}
    .close-btn {{
      background: none;
      border: none;
      color: #94a3b8;
      font-size: 16px;
      cursor: pointer;
    }}
    .prop-table {{
      width: 100%;
      font-size: 11.5px;
      border-collapse: collapse;
    }}
    .prop-table td {{
      padding: 6px 4px;
      vertical-align: top;
      border-bottom: 1px solid #1a2233;
    }}
    .prop-k {{
      color: #64748b;
      font-weight: 600;
      width: 32%;
      font-family: "Fira Code", monospace;
    }}
    .prop-v {{
      color: #cbd5e1;
      word-break: break-word;
    }}
    .prop-highlight {{
      background: #111a2e;
      border-left: 3px solid #38bdf8;
      padding: 8px;
      border-radius: 4px;
      margin-top: 10px;
      font-size: 11.5px;
      line-height: 1.45;
      color: #e2e8f0;
    }}

    /* Bottom Control Bar */
    .bottom-bar {{
      position: absolute;
      bottom: 12px;
      left: 14px;
      right: 14px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      pointer-events: none;
      z-index: 10;
    }}
    .status-caption {{
      background: rgba(14, 18, 28, 0.85);
      border: 1px solid #212a3e;
      border-radius: 6px;
      padding: 4px 10px;
      font-size: 11px;
      color: #f59e0b;
      display: flex;
      align-items: center;
      gap: 6px;
      pointer-events: auto;
    }}
    .floating-toolbar {{
      display: flex;
      gap: 6px;
      background: rgba(15, 19, 30, 0.92);
      backdrop-filter: blur(12px);
      border: 1px solid #263148;
      border-radius: 24px;
      padding: 4px 10px;
      pointer-events: auto;
      box-shadow: 0 4px 16px rgba(0,0,0,0.5);
    }}
    .t-btn {{
      background: #161c2c;
      border: 1px solid #252e44;
      color: #cbd5e1;
      width: 28px;
      height: 28px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 12px;
      cursor: pointer;
      transition: all 0.15s;
    }}
    .t-btn:hover {{
      background: #4f46e5;
      color: #ffffff;
      border-color: #4f46e5;
      transform: scale(1.08);
    }}

    @keyframes slideIn {{
      from {{ opacity: 0; transform: translateX(10px); }}
      to {{ opacity: 1; transform: translateX(0); }}
    }}
  </style>
</head>
<body>
  <div id="falkordb-shell">
    <!-- 1. Left Icon Rail -->
    <div class="icon-rail">
      <div class="falkor-logo" title="VLearn" style="background:#10a37f; color:#fff; font-weight:700;">V</div>
      <div class="rail-btn active" title="Sơ đồ tri thức">🗺️</div>
      <div class="rail-btn" title="Danh sách chủ đề">📚</div>
      <div class="rail-btn" title="Tổng kết buổi học">📋</div>
      <div class="rail-btn" title="Chế độ tối" style="margin-top:auto;">🌙</div>
    </div>

    <!-- 2. Left Drawer: Graph Info (Collapsible) -->
    <div class="graph-info-drawer">
      <div class="drawer-header">
        <span>Lộ Trình Học Tập</span>
        <span style="font-size:11px; color:#10b981; font-weight:600;">● Trực quan</span>
      </div>

      <div style="font-size:11px; color:#94a3b8; margin-bottom:12px;">
        Khóa học: <strong style="color:#f1f5f9;">Phát triển Sản phẩm AI</strong>
      </div>

      <!-- Nodes Breakdown -->
      <div class="section-title">
        <span>Thực thể Đồ thị ({total_nodes})</span>
      </div>
      <div class="pill-list">
        <div class="info-pill" onclick="filterByStatus('all')">
          <div class="pill-left">
            <span class="pill-dot dot-cyan"></span>
            <span>Khái niệm học tập</span>
          </div>
          <span class="pill-count">{concept_count}</span>
        </div>
        <div class="info-pill" onclick="filterByStatus('COVERED')">
          <div class="pill-left">
            <span class="pill-dot dot-green"></span>
            <span>🟢 Đã thông suốt</span>
          </div>
          <span class="pill-count">{covered_nodes}</span>
        </div>
        <div class="info-pill">
          <div class="pill-left">
            <span class="pill-dot" style="background:#f43f5e; box-shadow:0 0 6px #f43f5e;"></span>
            <span>⚠️ Bẫy ngộ nhận</span>
          </div>
          <span class="pill-count">{misconception_count}</span>
        </div>
        <div class="info-pill">
          <div class="pill-left">
            <span class="pill-dot dot-orange"></span>
            <span>⚖️ Đánh đổi kỹ thuật</span>
          </div>
          <span class="pill-count">{tradeoff_count}</span>
        </div>
        <div class="info-pill">
          <div class="pill-left">
            <span class="pill-dot dot-purple"></span>
            <span>⚙️ Cơ chế nhân quả</span>
          </div>
          <span class="pill-count">{mechanism_count}</span>
        </div>
        <div class="info-pill">
          <div class="pill-left">
            <span class="pill-dot" style="background:#06b6d4; box-shadow:0 0 6px #06b6d4;"></span>
            <span>💡 Phản ví dụ / Biên</span>
          </div>
          <span class="pill-count">{counter_example_count}</span>
        </div>
      </div>

      <!-- Relationships Breakdown -->
      <div class="section-title">
        <span>Liên kết Sư phạm ({total_edges})</span>
      </div>
      <div class="pill-list">
        <div class="info-pill">
          <div class="pill-left">
            <span class="pill-dot dot-green"></span>
            <span>Tiên quyết (PREREQ)</span>
          </div>
          <span class="pill-count">{prerequisite_count}</span>
        </div>
        <div class="info-pill">
          <div class="pill-left">
            <span class="pill-dot dot-purple"></span>
            <span>Đào sâu (DEEP_DIVE)</span>
          </div>
          <span class="pill-count">{deep_dive_count}</span>
        </div>
        <div class="info-pill">
          <div class="pill-left">
            <span class="pill-dot dot-cyan"></span>
            <span>Nhánh rẽ (ALT_PATH)</span>
          </div>
          <span class="pill-count">{alternative_path_count}</span>
        </div>
        <div class="info-pill">
          <div class="pill-left">
            <span class="pill-dot" style="background:#f43f5e;"></span>
            <span>Bẫy ngộ nhận (PITFALL)</span>
          </div>
          <span class="pill-count">{pitfall_count}</span>
        </div>
        <div class="info-pill">
          <div class="pill-left">
            <span class="pill-dot dot-orange"></span>
            <span>Đánh đổi (TRADEOFF)</span>
          </div>
          <span class="pill-count">{tradeoff_edge_count}</span>
        </div>
        <div class="info-pill">
          <div class="pill-left">
            <span class="pill-dot" style="background:#a855f7;"></span>
            <span>Cơ chế (MECHANISM)</span>
          </div>
          <span class="pill-count">{mechanism_edge_count}</span>
        </div>
        <div class="info-pill">
          <div class="pill-left">
            <span class="pill-dot" style="background:#06b6d4;"></span>
            <span>Phản ví dụ (COUNTER_EX)</span>
          </div>
          <span class="pill-count">{counter_example_edge_count}</span>
        </div>
      </div>

      <!-- Guide Legend -->
      <div class="section-title">
        <span>Hướng dẫn</span>
      </div>
      <div style="font-size:11px; color:#94a3b8; line-height:1.6; padding:4px 0;">
        • Nhấp vào từng nút để xem nội dung & câu hỏi vặn.<br/>
        • Kéo thả hoặc cuộn chuột để phóng to/thu nhỏ.<br/>
        • Màu xanh lá biểu thị kiến thức đã thông suốt.
      </div>
    </div>

    <!-- 3. Main Graph Viewport -->
    <div class="viewport">
      <!-- Top Navigation Bar -->
      <div class="cypher-topbar" style="display:flex; align-items:center; gap:10px;">
        <div class="graph-selector" style="font-weight:600; font-size:13px; color:#38bdf8;">
          <span>🗺️ Sơ đồ kiến thức</span>
        </div>
        <input type="text" class="search-filter" id="node-search" placeholder="🔍 Tìm kiếm chủ đề..." onkeyup="searchNode(this.value)" style="flex:1; max-width:360px;" />
        <button class="run-btn" onclick="fitView()" style="background:#10b981; border:none; padding:6px 14px; border-radius:6px; color:#fff; font-weight:600; cursor:pointer;">Căn chỉnh góc nhìn</button>
      </div>

      <!-- Interactive Canvas -->
      <div id="graph-canvas"></div>

      <!-- Node Properties Inspector Drawer -->
      <div class="node-inspector" id="node-inspector">
        <div class="inspector-head">
          <div>
            <span style="font-size:10px; font-weight:700; color:#10b981; text-transform:uppercase;" id="insp-tag">CHỦ ĐỀ KIẾN THỨC</span>
            <div class="inspector-title" id="insp-title">Chủ đề</div>
          </div>
          <button class="close-btn" onclick="closeInspector()">✕</button>
        </div>

        <div style="margin: 12px 0; padding: 8px 12px; background: #161a23; border-radius: 6px; font-size: 12px; display: flex; justify-content: space-between; align-items: center;">
          <span style="color:#94a3b8;">Trạng thái:</span>
          <span id="prop-status-badge" style="font-weight:600; color:#10b981;">Đang tải...</span>
        </div>

        <div class="prop-highlight" style="border-left-color:#10b981;">
          <div style="font-size:10.5px; font-weight:700; color:#10b981; margin-bottom:4px; text-transform:uppercase;">Kiến thức trọng tâm:</div>
          <div id="prop-truth" style="font-size:12.5px; line-height:1.5;">...</div>
        </div>

        <div class="prop-highlight" style="border-left-color:#f59e0b; margin-top:10px;">
          <div style="font-size:10.5px; font-weight:700; color:#f59e0b; margin-bottom:4px; text-transform:uppercase;">Câu hỏi gợi mở cùng Alex:</div>
          <div id="prop-q" style="color:#fef3c7; font-size:12.5px; line-height:1.5;">...</div>
        </div>
      </div>

      <!-- Bottom Status & Controls -->
      <div class="bottom-bar">
        <div class="status-caption">
          <span>ⓘ</span>
          <span>Lộ trình học tập trực quan — VLearn AI Platform</span>
        </div>

        <div class="floating-toolbar">
          <button class="t-btn" title="Fit to Screen" onclick="fitView()">🎯</button>
          <button class="t-btn" title="Zoom In" onclick="zoomIn()">➕</button>
          <button class="t-btn" title="Zoom Out" onclick="zoomOut()">➖</button>
          <button class="t-btn" title="Bật/Tắt mô phỏng vật lý" id="phys-btn" onclick="togglePhysics()">⏸️</button>
          <button class="t-btn" title="Reset Layout" onclick="resetLayout()">⚡</button>
        </div>
      </div>
    </div>
  </div>

  <script>
    const rawNodes = {nodes_json};
    const rawEdges = {edges_json};

    let physicsActive = true;

    // Chuẩn hóa dữ liệu mô phỏng phong cách FalkorDB Canvas
    const nodes = new vis.DataSet(rawNodes.map(n => {{
      const isCovered = n.status === "COVERED";
      const isSlide = String(n.id).startsWith("slide");

      // Bảng màu chuẩn FalkorDB: Hubs cyan/teal, Branches amber/orange, Pending purple
      let nodeColor = {{
        background: isCovered ? "#10b981" : (isSlide ? "#f97316" : "#38bdf8"),
        border: isCovered ? "#059669" : (isSlide ? "#ea580c" : "#0284c7"),
        highlight: {{
          background: "#ffffff",
          border: isCovered ? "#10b981" : "#38bdf8"
        }}
      }};

      let nodeSize = isCovered ? 26 : (isSlide ? 20 : 23);

      const nodeName = n.full_name || n.name || n.label || n.id || 'Node';
      const nodeLabel = n.label || ('P.' + (n.page || 1) + ' ' + nodeName.substring(0, 18));
      const nodeTitle = nodeName + ' (Trang ' + (n.page || 1) + ')';

      return {{
        id: n.id,
        label: nodeLabel,
        title: nodeTitle,
        value: nodeSize,
        color: nodeColor,
        shape: 'dot',
        font: {{
          color: '#f8fafc',
          size: 11.5,
          face: 'Inter, -apple-system, sans-serif',
          strokeWidth: 3,
          strokeColor: '#0b0d13'
        }},
        shadow: {{
          enabled: true,
          color: isCovered ? 'rgba(16, 185, 129, 0.45)' : 'rgba(56, 189, 248, 0.45)',
          size: 12,
          x: 0,
          y: 0
        }}
      }};
    }}));

    const edges = new vis.DataSet(rawEdges.map((e, idx) => {{
      const isAlt = e.type === "ALTERNATIVE_PATH" || e.type === "DEEP_DIVE_INTO";
      return {{
        id: 'e_' + idx,
        from: e.source || e.from,
        to: e.target || e.to,
        label: e.label || e.type,
        color: {{
          color: isAlt ? '#f9731699' : '#38bdf888',
          highlight: '#38bdf8'
        }},
        arrows: {{
          to: {{ enabled: true, scaleFactor: 0.7 }}
        }},
        font: {{
          color: '#94a3b8',
          size: 9.5,
          align: 'middle',
          background: '#0b0d13'
        }},
        smooth: {{
          type: 'curvedCW',
          roundness: 0.18
        }},
        width: isAlt ? 2 : 1.8
      }};
    }}));

    const container = document.getElementById('graph-canvas');
    const data = {{ nodes: nodes, edges: edges }};

    // Cấu hình Force-directed physics tương đương D3 Force của FalkorDB Canvas
    const options = {{
      nodes: {{
        scaling: {{ min: 18, max: 32 }}
      }},
      physics: {{
        enabled: true,
        solver: 'forceAtlas2Based',
        forceAtlas2Based: {{
          gravitationalConstant: -75,
          centralGravity: 0.008,
          springLength: 130,
          springConstant: 0.05,
          damping: 0.88,
          avoidOverlap: 0.75
        }},
        stabilization: {{
          iterations: 140,
          updateInterval: 25
        }}
      }},
      interaction: {{
        hover: true,
        hoverConnectedEdges: true,
        tooltipDelay: 100,
        zoomView: true,
        dragView: true,
        dragNodes: true
      }}
    }};

    const network = new vis.Network(container, data, options);

    // Xử lý sự kiện click node để mở Inspector Table
    network.on('click', function(params) {{
      if (params.nodes.length > 0) {{
        const nodeId = params.nodes[0];
        const n = rawNodes.find(item => item.id === nodeId);
        if (n) {{
          showInspector(n);
        }}
      }} else {{
        closeInspector();
      }}
    }});

    function showInspector(n) {{
      const panel = document.getElementById('node-inspector');
      document.getElementById('insp-title').textContent = n.full_name || n.label;
      
      let tagText = 'KHÁI NIỆM BÀI GIẢNG';
      let statusHtml = '<span style="color:#38bdf8; font-weight:700;">🔵 Chưa hoàn thành</span>';
      let truthText = n.core_truth || 'Đang cập nhật nội dung bài giảng...';
      let qText = n.child_question || n.learning_question || 'Bạn hãy cùng Alex thảo luận và làm rõ cơ chế nhé!';

      if (n.node_type === 'Misconception') {{
        tagText = '⚠️ BẪY NGỘ NHẬN';
        statusHtml = '<span style="color:#f43f5e; font-weight:700;">⚠️ Điểm mù nhận thức</span>';
        truthText = (n.pitfall_text || '') + (n.truth_hint ? (' | Bản chất chuẩn: ' + n.truth_hint) : '');
        qText = n.probe_question || 'Alex sẽ hỏi vặn để bạn tự thấy điểm mâu thuẫn!';
      }} else if (n.node_type === 'Tradeoff') {{
        tagText = '⚖️ ĐÁNH ĐỔI KỸ THUẬT';
        statusHtml = '<span style="color:#f59e0b; font-weight:700;">⚖️ Đánh đổi hệ thống</span>';
        truthText = (n.dimension_a && n.dimension_b) ? (n.dimension_a + ' VS ' + n.dimension_b) : 'Đánh đổi kỹ thuật';
        qText = n.probe_question || 'Alex sẽ hỏi vặn về cái giá phải trả của giải pháp!';
      }} else if (n.node_type === 'Mechanism') {{
        tagText = '⚙️ CƠ CHẾ NHÂN QUẢ';
        statusHtml = '<span style="color:#8b5cf6; font-weight:700;">⚙️ Chuỗi nhân quả cốt lõi</span>';
        truthText = n.causal_chain || '';
        qText = n.probe_question || 'Alex sẽ hỏi sâu vào chuỗi nguyên nhân - kết quả!';
      }} else if (n.node_type === 'CounterExample') {{
        tagText = '💡 PHẢN VÍ DỤ / TRƯỜNG HỢP BIÊN';
        statusHtml = '<span style="color:#06b6d4; font-weight:700;">💡 Tình huống thực tế</span>';
        truthText = n.scenario || '';
        qText = n.probe_question || 'Alex sẽ thách đố bằng ví dụ cụ thể!';
      }} else if (n.status === 'COVERED') {{
        statusHtml = '<span style="color:#10b981; font-weight:700;">🟢 Đã thông suốt</span>';
      }}

      document.getElementById('insp-tag').textContent = tagText;
      document.getElementById('prop-status-badge').innerHTML = statusHtml;
      document.getElementById('prop-truth').textContent = truthText;
      document.getElementById('prop-q').textContent = qText;

      panel.style.display = 'block';
    }}

    function closeInspector() {{
      document.getElementById('node-inspector').style.display = 'none';
    }}

    function fitView() {{
      network.fit({{ animation: {{ duration: 500, easingFunction: 'easeInOutQuad' }} }});
    }}

    function zoomIn() {{
      network.moveTo({{ scale: network.getScale() * 1.3, animation: {{ duration: 250 }} }});
    }}

    function zoomOut() {{
      network.moveTo({{ scale: network.getScale() * 0.75, animation: {{ duration: 250 }} }});
    }}

    function togglePhysics() {{
      physicsActive = !physicsActive;
      network.setOptions({{ physics: {{ enabled: physicsActive }} }});
      const btn = document.getElementById('phys-btn');
      btn.textContent = physicsActive ? '⏸️' : '▶️';
    }}

    function resetLayout() {{
      network.setOptions({{ physics: {{ enabled: true }} }});
      fitView();
    }}

    function searchNode(q) {{
      if (!q || !q.trim()) return;
      const term = q.toLowerCase().trim();
      const match = rawNodes.find(n => 
        (n.full_name && n.full_name.toLowerCase().includes(term)) ||
        (n.label && n.label.toLowerCase().includes(term))
      );
      if (match) {{
        network.focus(match.id, {{
          scale: 1.3,
          animation: {{ duration: 400, easingFunction: 'easeInOutQuad' }}
        }});
        showInspector(match);
      }}
    }}

    function filterByStatus(st) {{
      if (st === 'all') {{
        nodes.forEach(n => nodes.update({{ id: n.id, hidden: false }}));
      }} else {{
        rawNodes.forEach(n => {{
          nodes.update({{ id: n.id, hidden: (n.status !== st) }});
        }});
      }}
      fitView();
    }}

    function filterByTrack(trackPrefix) {{
      rawNodes.forEach(n => {{
        nodes.update({{ id: n.id, hidden: !String(n.track).includes(trackPrefix) }});
      }});
      fitView();
    }}
  </script>
</body>
</html>
"""
    return html


def main():
    parser = argparse.ArgumentParser(description="FalkorDB Knowledge Graph Visualizer")
    parser.add_argument("--open", action="store_true", help="Tự động mở đồ thị trên trình duyệt")
    default_html = os.path.join(ui_dir, "graph_visualizer.html")
    parser.add_argument("--output", type=str, default=default_html, help="Đường dẫn file HTML xuất ra")
    args = parser.parse_args()

    print("🔌 Đang kết nối tới FalkorDB để trích xuất cấu trúc đồ thị...")
    graph_service = GraphService()
    graph_data = graph_service.export_graph_for_ui()

    print(f"📊 Đã trích xuất: {len(graph_data.get('nodes', []))} Nodes và {len(graph_data.get('edges', []))} Edges.")

    html_content = generate_graph_html(graph_data, height="100vh")

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"✅ Đã tạo thành công file đồ thị tương tác tại: {args.output}")

    if args.open:
        print("🌐 Đang mở trên trình duyệt mặc định...")
        webbrowser.open(f"file://{args.output}")


if __name__ == "__main__":
    main()
