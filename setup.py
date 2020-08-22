import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="atlas_horizon",
    version="0.0.1",
    author="Ihor Kyrylenko",
    author_email="igornergyone@gmail.com",
    description="A small program to work with .ATL files and making queries to HORIZON system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pypa/atlas",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)