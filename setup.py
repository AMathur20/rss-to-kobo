from setuptools import setup, find_packages

setup(
    name="rss-to-kobo",
    version="2.0.0",
    packages=find_packages(where=".", include=['scripts*']),
    package_dir={"": "."},
    install_requires=[
        'dropbox>=11.36.0',
        'python-dotenv>=0.19.0',
        'cryptography>=36.0.0',
        'requests>=2.25.0',
    ],
    entry_points={
        'console_scripts': [
            'rss-auth=scripts.auth.cli:main',
        ],
    },
    python_requires='>=3.8',
)
