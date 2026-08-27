# build.py
import os
import zipfile

# 输出的文件名
OUTPUT_NAME = "AICard.ankiaddon"

# 输出文件夹
OUTPUT_DIR = "bin"

# 需要忽略的文件/文件夹
IGNORE_PATTERNS = {
    "__pycache__",
    ".git",
    ".vscode",
    ".DS_Store",
    "build.py",
    "docs",
    "bin",
    "README.md",   
    ".gitignore",   
    OUTPUT_NAME
}

def make_ankiaddon():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 输出到 bin 文件夹
    bin_dir = os.path.join(current_dir, OUTPUT_DIR)
    os.makedirs(bin_dir, exist_ok=True)
    output_path = os.path.join(bin_dir, OUTPUT_NAME)
    
    # 如果已存在先删除
    if os.path.exists(output_path):
        os.remove(output_path)

    print(f"正在打包插件到: {OUTPUT_NAME} ...")
    
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(current_dir):
            # 过滤不需要的目录
            dirs[:] = [d for d in dirs if d not in IGNORE_PATTERNS]
            
            for file in files:
                if file in IGNORE_PATTERNS or file.endswith(".pyc") or file.endswith(".ankiaddon"):
                    continue
                
                full_path = os.path.join(root, file)
                # 计算相对路径，确保在压缩包内部是平铺/相对的
                rel_path = os.path.relpath(full_path, current_dir)
                zip_file.write(full_path, rel_path)
                print(f"  + 添加: {rel_path}")

    print(f"\n🎉 打包完成！生成文件: {output_path}")

if __name__ == "__main__":
    make_ankiaddon()