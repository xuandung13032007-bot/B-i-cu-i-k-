import os
import sys
import re
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from agent_engine import AgentEngine
from gemini_service import GeminiService

PORT = 8080
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
SAMPLE_DIR = os.path.join(BASE_DIR, "sample_data")
os.makedirs(REPORTS_DIR, exist_ok=True)

# Khởi tạo engine toàn cục
engine = AgentEngine()

class AgentHttpHandler(BaseHTTPRequestHandler):

    def _set_headers(self, status=200, content_type='application/json'):
        self.send_response(status)
        self.send_header('Content-Type', f'{content_type}; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, x-goog-api-key')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def _parse_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        content_type = self.headers.get('Content-Type', '')
        body = self.rfile.read(content_length)
        
        form_data = {}
        files = {}

        if "multipart/form-data" in content_type:
            boundary_match = re.search(r'boundary=([^\s;]+)', content_type)
            if boundary_match:
                boundary = boundary_match.group(1).encode('utf-8')
                parts = body.split(b'--' + boundary)
                for part in parts:
                    if not part or part == b'--\r\n' or part == b'--' or part == b'\r\n':
                        continue
                    if b'\r\n\r\n' in part:
                        header_raw, content = part.split(b'\r\n\r\n', 1)
                        if content.endswith(b'\r\n'):
                            content = content[:-2]
                        header_str = header_raw.decode('utf-8', errors='replace')
                        name_match = re.search(r'name="([^"]+)"', header_str)
                        fname_match = re.search(r'filename="([^"]+)"', header_str)
                        if name_match:
                            key = name_match.group(1)
                            if fname_match:
                                files[key] = {
                                    'filename': fname_match.group(1),
                                    'bytes': content
                                }
                            else:
                                form_data[key] = content.decode('utf-8', errors='replace')
        elif "application/json" in content_type or body.strip().startswith(b'{'):
            try:
                form_data = json.loads(body.decode('utf-8', errors='replace'))
            except Exception:
                pass
        else:
            try:
                parsed_params = urllib.parse.parse_qs(body.decode('utf-8', errors='replace'))
                for k, v in parsed_params.items():
                    form_data[k] = v[0] if len(v) == 1 else v
            except Exception:
                pass

        return form_data, files

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/config":
            self._set_headers(200)
            is_cfg = engine.gemini.is_configured()
            key = engine.gemini.api_key
            masked = (key[:8] + "..." + key[-4:]) if len(key) > 12 else ""
            resp = {
                "configured": is_cfg,
                "masked_key": masked,
                "raw_key": key if is_cfg else "",
                "model": engine.gemini.model
            }
            self.wfile.write(json.dumps(resp, ensure_ascii=False).encode('utf-8'))
            return

        if path == "/api/sample/preview":
            sample_file = os.path.join(SAMPLE_DIR, "doanh_thu_ban_le_sample.csv")
            if os.path.exists(sample_file):
                import pandas as pd
                df = pd.read_csv(sample_file)
                resp = {
                    "success": True,
                    "filename": "doanh_thu_ban_le_sample.csv",
                    "total_rows": int(len(df)),
                    "total_cols": int(len(df.columns)),
                    "columns": list(df.columns),
                    "preview": df.head(8).fillna("").to_dict(orient="records"),
                    "context": {
                        "company_name": "Công ty Cổ phần Bán Lẻ & Thời Trang Tân Tiến",
                        "industry": "Bán lẻ đa kênh (Omnichannel: Cửa hàng offline, Shopee, Tiktok Shop, Website)",
                        "business_goal": "Tìm hiểu nguyên nhân biến động doanh số, xác định nhóm sản phẩm sinh lời cao nhất và tối ưu chi phí phân phối.",
                        "key_questions": "Top 20% danh mục nào đem lại 80% lợi nhuận? Kênh bán hàng nào đang có tỷ lệ chuyển đổi và doanh số tốt nhất?"
                    }
                }
            else:
                resp = {"success": False, "error": "Sample file not found"}
            self._set_headers(200)
            self.wfile.write(json.dumps(resp, ensure_ascii=False).encode('utf-8'))
            return

        if path == "/" or path == "/index.html":
            html_file = os.path.join(BASE_DIR, "templates", "index.html")
            if os.path.exists(html_file):
                self._set_headers(200, "text/html")
                with open(html_file, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self._set_headers(404, "text/plain")
                self.wfile.write(b"Index template not found.")
            return

        if path.startswith("/reports/"):
            filename = os.path.basename(path)
            file_path = os.path.join(REPORTS_DIR, filename)
            if os.path.exists(file_path):
                if filename.endswith(".html"):
                    c_type = "text/html"
                elif filename.endswith(".md"):
                    c_type = "text/markdown"
                else:
                    c_type = "text/csv"
                self._set_headers(200, c_type)
                with open(file_path, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self._set_headers(404, "text/plain")
                self.wfile.write(b"Report not found.")
            return

        if path.startswith("/sample_data/"):
            filename = os.path.basename(path)
            file_path = os.path.join(SAMPLE_DIR, filename)
            if os.path.exists(file_path):
                c_type = "text/csv" if filename.endswith(".csv") else "text/plain"
                self._set_headers(200, c_type)
                with open(file_path, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self._set_headers(404, "text/plain")
                self.wfile.write(b"Sample file not found.")
            return

        self._set_headers(404, "text/plain")
        self.wfile.write(b"404 Not Found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        form_data, files = self._parse_body()

        # ==============================================================
        # STEP RESET (Đưa về trạng thái ban đầu)
        # ==============================================================
        if path == "/api/step/reset" or path == "/api/reset" or path == "/api/reset_dwh":
            global engine
            gemini_key = engine.gemini.api_key
            gemini_model = engine.gemini.model
            engine = AgentEngine(gemini_api_key=gemini_key, gemini_model=gemini_model)
            self._set_headers(200)
            self.wfile.write(json.dumps({"success": True, "message": "Đã thiết lập lại hệ thống."}).encode('utf-8'))
            return

        # ==============================================================
        # TEST GEMINI API CONNECTION
        # ==============================================================
        if path == "/api/gemini/test":
            api_key = form_data.get("api_key", "")
            model = form_data.get("model", "gemini-2.5-flash")
            temp_gemini = GeminiService(api_key=api_key, model=model)
            res = temp_gemini.test_connection()
            self._set_headers(200)
            self.wfile.write(json.dumps(res, ensure_ascii=False).encode('utf-8'))
            return

        # ==============================================================
        # ROUTE: AI COPILOT CHAT ASSISTANT
        # ==============================================================
        if path == "/api/chat/assistant":
            message = form_data.get("message", "").strip()
            history = form_data.get("history", [])
            current_step = int(form_data.get("current_step", 1))

            frontend_ctx = form_data.get("context", {})
            if isinstance(frontend_ctx, str):
                try:
                    frontend_ctx = json.loads(frontend_ctx)
                except Exception:
                    frontend_ctx = {}
            elif not isinstance(frontend_ctx, dict):
                frontend_ctx = {}

            state_ctx = engine.state.get("business_context", {}) or {}
            context = {
                "company_name": frontend_ctx.get("company_name") or state_ctx.get("company_name") or "Công ty Cổ phần Bán Lẻ & Thời Trang Tân Tiến",
                "industry": frontend_ctx.get("industry") or state_ctx.get("industry") or "Bán lẻ đa kênh (Omnichannel)",
                "business_goal": frontend_ctx.get("business_goal") or state_ctx.get("business_goal") or "Tìm hiểu nguyên nhân biến động doanh số, xác định nhóm sản phẩm sinh lời cao nhất và tối ưu chi phí phân phối.",
                "key_questions": frontend_ctx.get("key_questions") or state_ctx.get("key_questions") or "Top 20% danh mục nào đem lại 80% lợi nhuận? Kênh bán hàng nào đang có tỷ lệ chuyển đổi và doanh số tốt nhất?"
            }

            analysis_data = engine.state.get("analysis_results", {})
            if not analysis_data:
                try:
                    if engine.state.get("cleaned_data") is None:
                        if engine.state.get("raw_data") is None:
                            sample_file = os.path.join(SAMPLE_DIR, "doanh_thu_ban_le_sample.csv")
                            if os.path.exists(sample_file):
                                with open(sample_file, "rb") as sf:
                                    engine.validate_and_load_input(file_bytes=sf.read(), filename="doanh_thu_ban_le_sample.csv")
                        if engine.state.get("raw_data") is not None:
                            engine.clean_data()
                            engine.check_data_quality()
                    if engine.state.get("cleaned_data") is not None:
                        proc_res = engine.process_business_data(context)
                        analysis_data = proc_res.get("analysis", {})
                except Exception:
                    analysis_data = {}

            cleaning_report = engine.state.get("cleaning_report", {})
            quality_audit = engine.state.get("quality_audit", {})

            reply_res = engine.gemini.chat_assistant(
                user_message=message,
                history=history,
                current_step=current_step,
                context=context,
                analysis_data=analysis_data,
                cleaning_report=cleaning_report,
                quality_audit=quality_audit
            )

            self._set_headers(200)
            self.wfile.write(json.dumps(reply_res, ensure_ascii=False).encode('utf-8'))
            return

        # ==============================================================
        # BƯỚC 1: XEM TRƯỚC DỮ LIỆU NGAY TẠI BƯỚC 1 (STEP 1 LIVE PREVIEW)
        # ==============================================================
        if path == "/api/step/preview":
            input_type = form_data.get("input_type", "upload")
            use_sample = form_data.get("use_sample", "false") == "true" or input_type == "sample"
            gsheet_url = form_data.get("gsheet_url", "").strip()
            file_bytes = None
            filename = None

            if use_sample:
                sample_file = os.path.join(SAMPLE_DIR, "doanh_thu_ban_le_sample.csv")
                if os.path.exists(sample_file):
                    with open(sample_file, "rb") as sf:
                        file_bytes = sf.read()
                    filename = "doanh_thu_ban_le_sample.csv"
            elif "file" in files:
                file_bytes = files["file"]["bytes"]
                filename = files["file"]["filename"]

            val_res = engine.validate_and_load_input(file_bytes=file_bytes, filename=filename, gsheet_url=gsheet_url)
            self._set_headers(200)
            if not val_res["valid"]:
                resp = {"success": False, "error": val_res.get("error"), "solution": val_res.get("solution")}
            else:
                resp = {
                    "success": True,
                    "filename": filename or "Google Sheet",
                    "total_rows": val_res["summary"]["total_rows"],
                    "total_cols": val_res["summary"]["total_cols"],
                    "columns": val_res["summary"]["columns"],
                    "preview": val_res["summary"]["preview"]
                }
            self.wfile.write(json.dumps(resp, ensure_ascii=False).encode('utf-8'))
            return

        # ==============================================================
        # BƯỚC 1 -> BƯỚC 2: VALIDATE INPUT (Kiểm tra nguồn dữ liệu)
        # ==============================================================
        if path == "/api/step/validate":
            gemini_key = form_data.get("gemini_api_key", "").strip()
            gemini_model = form_data.get("gemini_model", "gemini-2.5-flash").strip()
            if gemini_key:
                engine.set_gemini_config(api_key=gemini_key, model=gemini_model)

            context_raw = form_data.get("context", "{}")
            try:
                context = json.loads(context_raw) if isinstance(context_raw, str) else context_raw
            except Exception:
                context = {}
            engine.state["business_context"] = context

            input_type = form_data.get("input_type", "upload")
            use_sample = form_data.get("use_sample", "false") == "true" or form_data.get("sample", False)
            gsheet_url = form_data.get("gsheet_url", "") or form_data.get("file_url", "")

            file_bytes = None
            filename = None

            if use_sample or input_type == "sample":
                sample_file = os.path.join(SAMPLE_DIR, "doanh_thu_ban_le_sample.csv")
                if os.path.exists(sample_file):
                    with open(sample_file, "rb") as sf:
                        file_bytes = sf.read()
                    filename = "doanh_thu_ban_le_sample.csv"
                if not context.get("company_name"):
                    context["company_name"] = "Công ty Cổ phần Bán Lẻ & Thời Trang Tân Tiến"
                if not context.get("industry"):
                    context["industry"] = "Bán lẻ đa kênh (Omnichannel: Cửa hàng offline, Shopee, Tiktok Shop, Website)"
                if not context.get("business_goal"):
                    context["business_goal"] = "Tìm hiểu nguyên nhân biến động doanh số, xác định nhóm sản phẩm sinh lời cao nhất và tối ưu chi phí phân phối."
                if not context.get("key_questions"):
                    context["key_questions"] = "Top 20% danh mục nào đem lại 80% lợi nhuận? Kênh bán hàng nào đang có tỷ lệ chuyển đổi và doanh số tốt nhất?"
                engine.state["business_context"] = context
            elif "file" in files:
                file_bytes = files["file"]["bytes"]
                filename = files["file"]["filename"]
            elif gsheet_url:
                pass
            else:
                self._set_headers(200)
                resp = {
                    "success": False,
                    "step": "validate",
                    "error_title": "Chưa Cung Cấp Dữ Liệu",
                    "error": "Bạn chưa tải lên file Excel/CSV hoặc chưa nhập link Google Sheet.",
                    "solution": "Vui lòng tải file của bạn lên, dán link Google Sheet, hoặc chọn tab 'Dữ Liệu Mẫu' nếu muốn thử nghiệm."
                }
                self.wfile.write(json.dumps(resp, ensure_ascii=False).encode('utf-8'))
                return

            val_res = engine.validate_and_load_input(file_bytes=file_bytes, filename=filename, gsheet_url=gsheet_url)
            self._set_headers(200)
            if not val_res["valid"]:
                resp = {
                    "success": False,
                    "step": "validate",
                    "error_title": "Lỗi Kiểm Tra Nguồn Dữ Liệu Đầu Vào",
                    "error": val_res.get("error"),
                    "solution": val_res.get("solution")
                }
            else:
                resp = {
                    "success": True,
                    "step": "validate",
                    "filename": filename or "Google Sheet Data",
                    "summary": val_res["summary"]
                }
            self.wfile.write(json.dumps(resp, ensure_ascii=False).encode('utf-8'))
            return

        # ==============================================================
        # BƯỚC 2 -> BƯỚC 3: CLEANING & QUALITY CHECK (Làm sạch & Kiểm định)
        # ==============================================================
        if path == "/api/step/clean":
            clean_res = engine.clean_data()
            if not clean_res["success"]:
                self._set_headers(200)
                self.wfile.write(json.dumps({
                    "success": False,
                    "step": "cleaning",
                    "error_title": "Lỗi Quá Trình Làm Sạch Dữ Liệu",
                    "error": clean_res.get("error")
                }, ensure_ascii=False).encode('utf-8'))
                return

            audit_res = engine.check_data_quality()
            self._set_headers(200)
            if not audit_res["passed"]:
                resp = {
                    "success": False,
                    "step": "quality",
                    "error_title": "Dữ Liệu Không Đạt Tiêu Chuẩn Phân Tích",
                    "error": audit_res.get("error"),
                    "solution": audit_res.get("solution")
                }
            else:
                resp = {
                    "success": True,
                    "step": "clean",
                    "cleaning_report": clean_res["report"],
                    "quality_audit": audit_res["audit"]
                }
            self.wfile.write(json.dumps(resp, ensure_ascii=False).encode('utf-8'))
            return

        # ==============================================================
        # BƯỚC 3 -> BƯỚC 4: PROCESS & VERIFY (Phân tích theo bối cảnh với Gemini)
        # ==============================================================
        if path == "/api/step/process":
            # Có thể cập nhật lại bối cảnh nếu người dùng chỉnh sửa
            context_raw = form_data.get("context", "")
            if context_raw:
                try:
                    context = json.loads(context_raw) if isinstance(context_raw, str) else context_raw
                    engine.state["business_context"] = context
                except Exception:
                    pass
            else:
                context = engine.state.get("business_context", {})

            gemini_key = form_data.get("gemini_api_key", "").strip()
            gemini_model = form_data.get("gemini_model", "").strip()
            if gemini_key:
                engine.set_gemini_config(api_key=gemini_key, model=gemini_model)

            proc_res = engine.process_business_data(context)
            ver_res = engine.verify_analysis()

            self._set_headers(200)
            resp = {
                "success": True,
                "step": "process",
                "ai_source": engine.state["ai_source"],
                "analysis": proc_res["analysis"],
                "verification": ver_res["verification"]
            }
            self.wfile.write(json.dumps(resp, ensure_ascii=False).encode('utf-8'))
            return

        # ==============================================================
        # BƯỚC 4 FEEDBACK: NGƯỜI DÙNG PHẢN HỒI ĐIỀU CHỈNH
        # ==============================================================
        if path == "/api/step/feedback" or path == "/api/pipeline/feedback" or path == "/api/feedback":
            user_feedback = form_data.get("feedback", "") or form_data.get("message", "")
            ctx = engine.state.get("business_context", {})
            proc_res = engine.process_business_data(ctx, user_feedback=user_feedback)
            ver_res = engine.verify_analysis()

            self._set_headers(200)
            resp = {
                "success": True,
                "step": "feedback_updated",
                "ai_source": engine.state["ai_source"],
                "analysis": proc_res["analysis"],
                "verification": ver_res["verification"]
            }
            self.wfile.write(json.dumps(resp, ensure_ascii=False).encode('utf-8'))
            return

        # ==============================================================
        # BƯỚC 4 -> BƯỚC 5: EXPORT DASHBOARD HTML
        # ==============================================================
        if path == "/api/step/export" or path == "/api/pipeline/export" or path == "/api/export":
            export_res = engine.export_html_dashboard(output_dir=REPORTS_DIR)
            self._set_headers(200)
            self.wfile.write(json.dumps(export_res, ensure_ascii=False).encode('utf-8'))
            return

        # ==============================================================
        # BACKWARDS COMPATIBILITY: /api/pipeline/run & /api/analyze
        # ==============================================================
        if path == "/api/pipeline/run" or path == "/api/analyze":
            gemini_key = form_data.get("gemini_api_key", "").strip()
            gemini_model = form_data.get("gemini_model", "gemini-2.5-flash").strip()
            if gemini_key:
                engine.set_gemini_config(api_key=gemini_key, model=gemini_model)

            context_raw = form_data.get("context", "{}")
            try:
                context = json.loads(context_raw) if isinstance(context_raw, str) else context_raw
            except Exception:
                context = {}

            input_type = form_data.get("input_type", "upload")
            use_sample = form_data.get("use_sample", "false") == "true" or form_data.get("sample", False)
            gsheet_url = form_data.get("gsheet_url", "") or form_data.get("file_url", "")

            file_bytes = None
            filename = None

            if use_sample or input_type == "sample":
                sample_file = os.path.join(SAMPLE_DIR, "doanh_thu_ban_le_sample.csv")
                if os.path.exists(sample_file):
                    with open(sample_file, "rb") as sf:
                        file_bytes = sf.read()
                    filename = "doanh_thu_ban_le_sample.csv"
                if not context.get("company_name"):
                    context["company_name"] = "Công ty Cổ phần Bán Lẻ & Thời Trang Tân Tiến"
                if not context.get("industry"):
                    context["industry"] = "Bán lẻ đa kênh (Omnichannel: Cửa hàng offline, Shopee, Tiktok Shop, Website)"
                if not context.get("business_goal"):
                    context["business_goal"] = "Tìm hiểu nguyên nhân biến động doanh số, xác định nhóm sản phẩm sinh lời cao nhất và tối ưu chi phí phân phối."
                if not context.get("key_questions"):
                    context["key_questions"] = "Top 20% danh mục nào đem lại 80% lợi nhuận? Kênh bán hàng nào đang có tỷ lệ chuyển đổi và doanh số tốt nhất?"
                engine.state["business_context"] = context
            elif "file" in files:
                file_bytes = files["file"]["bytes"]
                filename = files["file"]["filename"]
            elif gsheet_url:
                pass
            else:
                self._set_headers(200)
                resp = {
                    "success": False,
                    "step": "validate",
                    "error_title": "Chưa Cung Cấp Dữ Liệu",
                    "error": "Bạn chưa tải lên file Excel/CSV hoặc chưa nhập link Google Sheet.",
                    "solution": "Vui lòng tải file của bạn lên, dán link Google Sheet, hoặc chọn tab 'Dữ Liệu Mẫu' nếu muốn thử nghiệm."
                }
                self.wfile.write(json.dumps(resp, ensure_ascii=False).encode('utf-8'))
                return

            val_res = engine.validate_and_load_input(file_bytes=file_bytes, filename=filename, gsheet_url=gsheet_url)
            if not val_res["valid"]:
                self._set_headers(200)
                resp = {
                    "success": False,
                    "step": "validate",
                    "error_title": "Lỗi Kiểm Tra Nguồn Dữ Liệu Đầu Vào",
                    "error": val_res.get("error"),
                    "solution": val_res.get("solution")
                }
                self.wfile.write(json.dumps(resp, ensure_ascii=False).encode('utf-8'))
                return

            clean_res = engine.clean_data()
            if not clean_res["success"]:
                self._set_headers(200)
                resp = {
                    "success": False,
                    "step": "cleaning",
                    "error_title": "Lỗi Trong Quá Trình Làm Sạch Dữ Liệu",
                    "error": clean_res.get("error")
                }
                self.wfile.write(json.dumps(resp, ensure_ascii=False).encode('utf-8'))
                return

            audit_res = engine.check_data_quality()
            if not audit_res["passed"]:
                self._set_headers(200)
                resp = {
                    "success": False,
                    "step": "quality",
                    "error_title": "Dữ Liệu Không Đạt Tiêu Chuẩn Phân Tích",
                    "error": audit_res.get("error"),
                    "solution": audit_res.get("solution")
                }
                self.wfile.write(json.dumps(resp, ensure_ascii=False).encode('utf-8'))
                return

            proc_res = engine.process_business_data(context)
            ver_res = engine.verify_analysis()

            self._set_headers(200)
            resp = {
                "success": True,
                "step": "review",
                "ai_source": engine.state["ai_source"],
                "summary": val_res["summary"],
                "cleaning_report": clean_res["report"],
                "quality_audit": audit_res["audit"],
                "analysis": proc_res["analysis"],
                "verification": ver_res["verification"]
            }
            self.wfile.write(json.dumps(resp, ensure_ascii=False).encode('utf-8'))
            return

        self._set_headers(404)
        self.wfile.write(b"API endpoint not found")

def run_server():
    server_address = ('0.0.0.0', PORT)
    httpd = HTTPServer(server_address, AgentHttpHandler)
    print("=" * 65)
    print(f"[*] AI Data Analyst Agent + Gemini API Server dang hoat dong!")
    print(f"[*] Mo trinh duyet va truy cap: http://localhost:{PORT}")
    print(f"[*] Gemini Models: gemini-2.5-flash | gemini-1.5-flash | gemini-1.5-pro")
    print(f"[*] Bam Ctrl + C de dung he thong.")
    print("=" * 65)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Dang tat server...")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
