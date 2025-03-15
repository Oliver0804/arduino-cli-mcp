from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="arduino-cli-mcp",
    version="0.1.0",
    author="Oliver",
    author_email="your.email@example.com",
    description="Arduino CLI MCP Server for GitHub Copilot integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/arduino-cli-mcp",
    packages=find_packages(include=["arduino_cli_mcp", "arduino_cli_mcp.*"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
    ],
    python_requires=">=3.7",
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
)
