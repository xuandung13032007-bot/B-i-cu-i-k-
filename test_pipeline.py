import os
import json
from agent_engine import AgentEngine

def run_test():
    print("=== BẮT ĐẦU KIỂM TRA QUY TRÌNH AI AGENT ===")
    engine = AgentEngine()

    # Bối cảnh doanh nghiệp
    context = {
        "company_name": "Công ty Cổ phần Thời Trang & Đồ Gia Dụng Á Châu",
        "industry": "Bán lẻ đa kênh (E-commerce & Offline)",
        "business_goal": "Tối ưu hóa doanh số và nhận diện nhóm hàng chủ lực",
        "key_questions": "Sản phẩm nào đem lại 80% lợi nhuận? Kênh bán hàng nào đang dẫn đầu?"
    }

    sample_path = os.path.join("sample_data", "doanh_thu_ban_le_sample.csv")
    with open(sample_path, "rb") as f:
        file_bytes = f.read()

    # 1. Validation
    print("\n[Node 1 & 2] Kiểm tra đúng (Validation):")
    val_res = engine.validate_and_load_input(file_bytes=file_bytes, filename="sample.csv")
    print("-> Kết quả:", val_res["valid"], "| Số dòng gốc:", val_res["summary"]["total_rows"])
    assert val_res["valid"] is True

    # 2. Cleaning
    print("\n[Node 3] Data Cleaning:")
    clean_res = engine.clean_data()
    print("-> Kết quả:", clean_res["success"])
    print("-> Dòng trùng đã xóa:", clean_res["report"]["duplicates_removed"])
    print("-> Missing values đã lấp:", clean_res["report"]["missing_values_handled"])
    assert clean_res["success"] is True

    # 3. Quality Check
    print("\n[Node 4] Quality Check:")
    audit_res = engine.check_data_quality()
    print("-> Đạt chuẩn:", audit_res["passed"], "| Điểm chất lượng:", audit_res["audit"]["score"])
    assert audit_res["passed"] is True

    # 4. Process (Theo bối cảnh)
    print("\n[Node 5] Process (Phân tích theo bối cảnh doanh nghiệp):")
    proc_res = engine.process_business_data(context)
    kpis = proc_res["analysis"]["kpis"]
    print("-> Doanh thu tổng:", f"{kpis['total_revenue']:,.0f} VNĐ")
    print("-> Biên lợi nhuận:", f"{kpis['profit_margin']}%")
    print("-> Top Pareto:", proc_res["analysis"]["pareto"][0]["name"])
    assert proc_res["success"] is True

    # 5. Verify
    print("\n[Node 6] Verify (Kiểm định số liệu):")
    ver_res = engine.verify_analysis()
    print("-> Kết quả kiểm định:", ver_res["verified"], "| Độ tin cậy:", ver_res["verification"]["confidence_score"], "%")
    assert ver_res["verified"] is True

    # 6. Feedback simulation
    print("\n[Node 6b] Feedback loop (Thử nghiệm phản hồi người dùng):")
    fb_res = engine.process_business_data(context, user_feedback="Đào sâu phân tích nhóm Điện tử và kênh Shopee")
    print("-> Đã nhận diện feedback:", fb_res["analysis"]["feedback_adjustment"])

    # 7. Export Dashboard HTML
    print("\n[Node 7] Xuất file báo cáo & Dashboard HTML:")
    os.makedirs("reports", exist_ok=True)
    exp_res = engine.export_html_dashboard(output_dir="reports")
    print("-> File Dashboard:", exp_res["dashboard_filename"])
    print("-> File CSV sạch:", exp_res["cleaned_csv_filename"])
    assert os.path.exists(exp_res["dashboard_path"])
    assert os.path.exists(exp_res["cleaned_csv_path"])

    print("\n=== TẤT CẢ CÁC BƯỚC ĐÃ VƯỢT QUA XUẤT SẮC 100%! ===")

if __name__ == "__main__":
    run_test()
