"""LAB DASHBOARD — Lớp 3: app pywebview (dependency duy nhất).

`python -m research.governance.lab_app` mở cửa sổ app riêng (WebKit hệ
thống), nút "Làm mới" + auto-refresh 30 giây.
`python -m research.governance.lab_app --html` chỉ sinh
dashboard/index.html rồi thoát — KHÔNG cần pywebview (dùng được khi
không muốn dependency).

Dependency pin: pywebview==6.2.1 trong .venv của main checkout. Lớp 1+2
(dashboard_collect / dashboard_render) là thuần stdlib và chạy không
cần nó.
"""

from __future__ import annotations

import sys
import threading
from pathlib import Path

try:
    from dashboard_collect import collect_snapshot, write_outputs
except ImportError:  # chạy qua `python -m research.governance.lab_app`
    from .dashboard_collect import collect_snapshot, write_outputs

REFRESH_SECONDS = 30
WINDOW_TITLE = "Lab Dashboard — my-quantitative"
INJECT = """
<div style="position:fixed;right:18px;bottom:18px;z-index:99;display:flex;gap:8px;align-items:center">
<button onclick="window.pywebview && window.pywebview.api.refresh()"
 style="background:#4da3ff;color:#0f1216;border:0;border-radius:8px;
 padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer">Làm mới</button>
<span id="cd" style="color:#8b98a8;font-size:11px"></span>
</div>
<script>
try{var y=sessionStorage.getItem('lab_scroll');
if(y){document.addEventListener('DOMContentLoaded',function(){
window.scrollTo(0,parseInt(y))});}}catch(e){}
var t;window.addEventListener('scroll',function(){clearTimeout(t);
t=setTimeout(function(){try{sessionStorage.setItem('lab_scroll',
window.scrollY)}catch(e){}},150)});
setInterval(function(){
  var el=document.getElementById('cd');
  if(el){var s=Math.max(0,30-Math.floor((Date.now()%30000)/1000));
  el.textContent='tự refresh sau '+s+'s';}
},1000);
setInterval(function(){
  if(window.pywebview && window.pywebview.api){window.pywebview.api.refresh();}
},30000);
</script>
"""


def repo_root() -> Path:
    # worktree root = research/governance/../../
    return Path(__file__).resolve().parents[2]


def regenerate(render_only: bool = False) -> Path:
    """Sinh dashboard/index.html. Lần launch đầu (--html / mở window)
    cũng cập nhật plans/ACTIVE_CYCLES.json; các lần refresh 30s sau đó
    CHỈ render HTML để không ghi churn vào file đã commit."""
    root = repo_root()
    snap = collect_snapshot(root)
    write_outputs(snap, root / "dashboard", write_registry=not render_only)
    return root / "dashboard" / "index.html"


def render_for_window() -> Path:
    """Sinh HTML rồi chèn nút Làm mới + bộ đếm (chỉ trong app window;
    file dashboard/index.html thuần vẫn là output của lớp 2)."""
    path = regenerate(render_only=True)
    html = path.read_text(encoding="utf-8")
    if "pywebview.api" not in html:
        html = html.replace("</body>", INJECT + "\n</body>")
        path.write_text(html, encoding="utf-8")
    return path


def run_html_mode() -> int:
    path = regenerate()
    print(path)
    return 0


def run_window_mode() -> int:
    try:
        import webview  # pywebview==6.2.1
    except ImportError as exc:
        print(f"BLOCKED: pywebview chưa cài trong .venv ({exc}); "
              f"dùng `--html` hoặc pip install 'pywebview==6.2.1'",
              file=sys.stderr)
        return 3
    regenerate()  # launch: cập nhật cả plans/ACTIVE_CYCLES.json một lần
    path = render_for_window()  # các refresh sau chỉ render HTML

    class Api:
        @staticmethod
        def refresh():
            try:
                render_for_window()
            except Exception as exc:  # fail-closed: giữ nội dung cũ
                print(f"refresh lỗi: {exc}", file=sys.stderr)
            return True

    window = webview.create_window(WINDOW_TITLE, str(path), width=1280,
                                   height=860, min_size=(900, 600))

    def auto_refresh():
        import time
        while True:
            time.sleep(REFRESH_SECONDS)
            try:
                render_for_window()
                window.evaluate_js("location.reload()")
            except Exception as exc:
                print(f"auto-refresh lỗi: {exc}", file=sys.stderr)

    threading.Thread(target=auto_refresh, daemon=True).start()
    webview.start()
    return 0


def main(argv: list[str]) -> int:
    if "--html" in argv:
        return run_html_mode()
    return run_window_mode()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
