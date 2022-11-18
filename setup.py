from setuptools import setup

setup(
    name='scan_cleaner',
    version='0.0.1',
    install_requires=[
        'opencv-contrib-python',
        'numpy',
        'img2pdf',
        'Pillow',
    ],
    entry_points={
        "console_scripts": [
            "scan_cleaner = main:cli",
        ],
    },
)
