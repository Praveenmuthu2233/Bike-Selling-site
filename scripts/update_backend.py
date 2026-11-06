import os
import sys

def update_app_py():
    app_path = os.path.join("my-node-app", "app.py")
    with open(app_path, "r", encoding="utf-8") as f:
        content = f.read()

    # In admin_sold_bike_detail_api, query bike_documents
    old_target = """                # 3. Query sale_documents
                try:
                    cursor.execute("SELECT id, bike_id, document_type, document_ref_masked, file_name, file_size, created_at FROM sale_documents WHERE bike_id = %s ORDER BY id DESC LIMIT 1", (bike_id,))
                    proof_doc = cursor.fetchone()
                except Exception:
                    pass"""

    new_replacement = """                # 3. Query sale_documents & ownership bike_documents
                try:
                    cursor.execute("SELECT id, bike_id, document_type, document_ref_masked, file_name, file_size, created_at FROM sale_documents WHERE bike_id = %s ORDER BY id DESC LIMIT 1", (bike_id,))
                    proof_doc = cursor.fetchone()
                except Exception:
                    pass

                bike_docs_list = []
                try:
                    cursor.execute("SELECT id, bike_id, user_id, doc_type, file_name, file_size, status, remarks, created_at FROM bike_documents WHERE bike_id = %s ORDER BY id DESC", (bike_id,))
                    b_docs = cursor.fetchall() or []
                    for doc in b_docs:
                        doc["created_at"] = str(doc.get("created_at") or "")
                        doc["download_url"] = f"/api/documents/{doc['id']}/download"
                        doc["view_url"] = f"/api/documents/{doc['id']}/view"
                        bike_docs_list.append(doc)
                except Exception:
                    bike_docs_list = []"""

    if old_target in content:
        content = content.replace(old_target, new_replacement, 1)
        print("Replaced sale_documents query with bike_documents query")
    else:
        print("sale_documents target not found in app.py")

    # In res_payload, include bike_documents
    old_payload = """        "proof_document": proof_info,
        "sale_info": sale_info,"""

    new_payload = """        "proof_document": proof_info,
        "bike_documents": bike_docs_list if 'bike_docs_list' in locals() else [],
        "sale_info": sale_info,"""

    if old_payload in content:
        content = content.replace(old_payload, new_payload, 1)
        print("Added bike_documents to res_payload")
    else:
        print("res_payload target not found in app.py")

    with open(app_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("app.py updated successfully")

if __name__ == "__main__":
    update_app_py()
