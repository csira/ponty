from setuptools import find_packages, setup


if __name__ == "__main__":
    setup(
        packages=find_packages(),
        package_data={"ponty": ["py.typed"]},
        name="ponty",
        version="0.3.4",
        license="BSD",
        url="https://github.com/csira/ponty",
        description="Minimal async web framework, built on aiohttp.",
        install_requires=[
            "aiohttp>=3.7.3",
            "jsonschema==3.2.0",
            "typing-extensions>=4.2.0",
        ],
        python_requires=">=3.8",
        classifiers=[
            "Development Status :: 4 - Beta",
            "Environment :: Web Environment",
            "Framework :: AsyncIO",
            "Framework :: aiohttp",
            "Intended Audience :: Developers",
            "License :: Freely Distributable",
            "License :: OSI Approved :: BSD License",
            "Operating System :: OS Independent",
            "Programming Language :: Python",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "Topic :: Internet :: WWW/HTTP",
            "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
            "Topic :: Software Development :: Libraries :: Python Modules",
            "Typing :: Typed",
        ]
    )
