import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="atlas_horizon",
    version="0.1",
    author="Ihor Kyrylenko",
    author_email="igornergyone@gmail.com",
    description="A small program to work with .ATL files and making queries to HORIZON system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pypa/atlas",
    packages=setuptools.find_packages(where='src'),
    package_dir={
            '': 'src',
        },
    # include_package_data=True,
    package_data={
             "": ["*.dat", "*.txt"],
        },
    scripts=["run_atlas.py"],
    py_modules=["MODULES/ATL",
                "MODULES/Functions",
                "MODULES/Observation"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "astropy>=4",
        "astroquery>=0.4",
        "pandas>=1.1",
        "tqdm>=4",
    ],
    python_requires='>=3.8',
)