from pathlib import Path

from setuptools import setup, find_packages

# Read the contents of README file
source_root = Path(".")
with (source_root / "README.md").open(encoding="utf-8") as f:
    long_description = f.read()

version = "2.5.0"

with (source_root / "src" / "pandas_profiling" / "version.py").open(
    "w", encoding="utf-8"
) as f:
    f.writelines(
        [
            '"""This file is auto-generated by setup.py, please do not alter."""\n',
            '__version__ = "{}"\n'.format(version),
            "",
        ]
    )

setup(
    name="pandas-profiling",
    version=version,
    author="Simon Brugman",
    author_email="pandasprofiling@gmail.com",
    packages=find_packages("src"),
    package_dir={"": "src"},
    url="https://github.com/pandas-profiling/pandas-profiling",
    license="MIT",
    description="Generate profile report for pandas DataFrame",
    install_requires=[
        "numpy>=1.16.0",
        "scipy>=1.4.1",
        "pandas==0.25.3",
        "matplotlib>=3.0.3",  # 3.1.2 for Python > 3.5
        "confuse==1.0.0",
        "jinja2==2.11.1",
        "visions==0.2.2",
        # Related to HTML report
        "htmlmin==0.1.12",
        # Could be optional
        "missingno==0.4.2",
        "phik==0.9.9",
        "astropy>=3.2.3",  # 4.0 for Python > 3.5
        "tangled-up-in-unicode==0.0.3",
        "tqdm==4.43.0",
        "kaggle==1.5.6",
        "ipywidgets==7.5.1",
        "requests==2.23.0",
    ],
    extras_require={
        "notebook": ["jupyter-client==5.3.4", "jupyter-core==4.6.2"],
        "app": ["pyqt5==5.14.1"],
    },
    include_package_data=True,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Environment :: Console",
        "Operating System :: OS Independent",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Healthcare Industry",
        "Topic :: Scientific/Engineering",
        "Framework :: IPython",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    keywords="pandas data-science data-analysis python jupyter ipython",
    long_description=long_description,
    long_description_content_type="text/markdown",
    entry_points={
        "console_scripts": [
            "pandas_profiling = pandas_profiling.controller.console:main"
        ]
    },
    options={"bdist_wheel": {"universal": True}},
)
