import setuptools

setuptools.setup(
    name="pickora",
    version="1.0.0",
    author="splitline",
    author_email="tbsthitw@gmail.com",
    description="A toy compiler that can convert Python scripts into pickle bytecode.",
    long_description=open("README.md", "r").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/splitline/Pickora",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',

    entry_points={
        "console_scripts": [
            "pickora = pickora:main",
        ],
    },
)

