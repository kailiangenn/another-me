from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="another-me",
    version="0.1.0",
    author="AME Team",
    author_email="shangkl@enn.cn",
    description="AME (Another Me Engine) - AI Digital Avatar Engine",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kailiangenn/another-me",
    project_urls={
        "Bug Tracker": "https://github.com/kailiangenn/another-me/issues",
        "Source Code": "https://github.com/kailiangenn/another-me",
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    package_dir={"": "ame"},
    packages=find_packages(where="ame"),
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov",
            "black",
            "flake8",
        ],
        "graph": [
            "falkordb",
            "redis",
        ]
    },
    entry_points={
        "console_scripts": [
        ],
    },
)