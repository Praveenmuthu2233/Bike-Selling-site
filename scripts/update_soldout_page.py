import os

def update_sold_out_page():
    fpath = os.path.join("my-node-app", "templates", "SoldOutPage.html")
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update soldLimit from 8 to 6
    content = content.replace("const soldLimit = 8;", "const soldLimit = 6;")

    # 2. Update card link to /sold-bike-details.html?id=${bike.id}
    old_link = """<a href="/enquiry-bike-details.html?id=${bike.id}" class="btn btn-sm btn-outline">Details</a>"""
    new_link = """<a href="/sold-bike-details.html?id=${bike.id}" class="btn btn-sm btn-primary" style="display:inline-flex; align-items:center; gap:6px; font-weight:700;"><i class="fas fa-eye"></i> View Details</a>"""
    if old_link in content:
        content = content.replace(old_link, new_link)
        print("Updated details button to point to /sold-bike-details.html")
    else:
        print("Old link target not found, searching with regex or variations")
        # In case whitespace differs
        import re
        content = re.sub(
            r'<a\s+href=["\']/enquiry-bike-details\.html\?id=\$\{bike\.id\}["\'][^>]*>Details</a>',
            new_link,
            content
        )

    # 3. Enhance light theme styling on grid if needed
    old_header = """<main class="main-content" style="padding: 4.5rem 0 6rem;">"""
    new_header = """<main class="main-content" style="padding: 3.5rem 0 5rem; background-color: #F8FAFC;">"""
    if old_header in content:
        content = content.replace(old_header, new_header)

    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    print("SoldOutPage.html updated successfully")

if __name__ == "__main__":
    update_sold_out_page()
