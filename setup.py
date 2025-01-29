from setuptools import setup, find_packages

setup(
    name="code_assistant",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "transformers>=4.36.0",
        "torch>=2.1.0",
        "pathspec>=0.11.0",
        "sympy>=1.12",
    ],
    author="Bamba Ba",
    author_email="lebabamth@gmail.com",
    description="A Local AI-powered code assistant using DeepSeek",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    python_requires=">=3.8",
)
