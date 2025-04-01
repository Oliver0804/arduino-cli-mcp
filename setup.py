from setuptools import setup, find_packages, Command
import os
import shutil

# 添加清理命令
class CleanCommand(Command):
    """自定義 clean 命令來刪除建置時產生的檔案"""
    user_options = []
    
    def initialize_options(self):
        pass
    
    def finalize_options(self):
        pass
    
    def run(self):
        """執行清理操作"""
        # 要清理的目錄
        dirs_to_clean = [
            'build',
            'dist',
            '*.egg-info',
            '**/__pycache__',
            '**/*.pyc',
            '**/*.pyo',
        ]
        
        for d in dirs_to_clean:
            # 使用 glob 模式來匹配目錄
            import glob
            for path in glob.glob(d, recursive=True):
                if os.path.isdir(path):
                    print(f"清理目錄: {path}")
                    shutil.rmtree(path, ignore_errors=True)
                elif os.path.isfile(path):
                    print(f"刪除檔案: {path}")
                    os.remove(path)

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="arduino-cli-mcp",
    version="0.1.4",
    author="Oliver",
    author_email="icetzsr@gmail.com",
    description="Arduino CLI MCP Server for GitHub Copilot integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/oliver0804/arduino-cli-mcp",
    packages=find_packages(include=["arduino_cli_mcp", "arduino_cli_mcp.*"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
    ],
    python_requires=">=3.11",
    install_requires=[
        "mcp",
        "pydantic"
    ],
    entry_points={
        "console_scripts": [
            "arduino-cli-mcp=arduino_cli_mcp.main:main",
        ],
    },
    include_package_data=True,
    # 添加自定義命令
    cmdclass={
        'clean': CleanCommand,
    }
)
