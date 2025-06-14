from setuptools import setup, find_packages

setup(
    name="mpp-examen",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.95.2",
        "uvicorn==0.21.1",
        "websockets==11.0.3",
        "pydantic==1.10.7",
        "typing-extensions==4.5.0",
        "python-multipart==0.0.6",
        "h11==0.14.0",
        "click==8.1.7",
        "starlette==0.27.0",
        "anyio==3.6.2",
        "gunicorn==20.1.0",
    ],
    python_requires=">=3.9",
) 