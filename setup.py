from setuptools import setup, find_packages

setup(
    name="ai-voice-agent",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "pinecone-client",
        "python-jose",
        "passlib",
        "python-multipart",
        "pydantic",
    ],
)
