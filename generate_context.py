import os

# --- 設定：你想要打包哪些檔案？ ---
# 1. 要讀取的副檔名
TARGET_EXTENSIONS = {".py", ".toml", ".txt", ".md", ".json"}
# 2. 要忽略的資料夾 (避免讀到虛擬環境或 git)
IGNORE_DIRS = {"venv", ".git", "__pycache__", ".streamlit", "assets"}
# (注意：.streamlit 裡面通常有 secrets，如果不想讓 API Key 曝光，這裡設為忽略，或者手動遮蔽)


def generate_project_context():
    output = []

    # --- 第一部分：生成專案結構樹 ---
    output.append("# 📂 Project Structure")
    output.append("```text")
    for root, dirs, files in os.walk("."):
        # 過濾忽略的資料夾
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        level = root.replace(".", "").count(os.sep)
        indent = " " * 4 * (level)
        output.append(f"{indent}{os.path.basename(root)}/")
        subindent = " " * 4 * (level + 1)
        for f in files:
            output.append(f"{subindent}{f}")
    output.append("```\n")

    # --- 第二部分：讀取檔案內容 ---
    output.append("# 📜 File Contents")

    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for file in files:
            ext = os.path.splitext(file)[1]
            if ext in TARGET_EXTENSIONS:
                file_path = os.path.join(root, file)

                # 特別排除這個生成腳本本身
                if "generate_context.py" in file_path:
                    continue

                output.append(f"\n### File: {file_path}")
                output.append("```python" if ext == ".py" else "```text")

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        output.append(content)
                except Exception as e:
                    output.append(f"# Error reading file: {e}")

                output.append("```")

    # --- 輸出結果 ---
    final_text = "\n".join(output)

    # 寫入一個 txt 檔，方便你打開複製
    with open("project_context.txt", "w", encoding="utf-8") as f:
        f.write(final_text)

    print("✅ 打包完成！請打開 'project_context.txt'，全選複製並貼給 AI。")


if __name__ == "__main__":
    generate_project_context()
