from setuptools import setup, find_packages

setup(
    name="mpp-examen",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.109.0",
        "uvicorn==0.27.0",
        "websockets==12.0",
        "pydantic==2.5.3",
        "typing-extensions==4.9.0",
        "python-multipart==0.0.6",
        "h11==0.14.0",
        "click==8.1.7",
        "starlette==0.36.3",
        "anyio==4.2.0",
    ],
    python_requires=">=3.9",
) 