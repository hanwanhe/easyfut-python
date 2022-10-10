import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="easyfut",
    version="1.0.0",
    author="hanwanhe",
    author_email="hanwanhe@foxmail.com",
    description="Easy http api for futures",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hanwanhe/easyfut-python",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6.4',
    install_requires=["tornado", "tqsdk"],
    entry_points={
        'console_scripts': [
            'easyfut = easyfut.main:run'
        ]
    },
    include_package_data=True
)