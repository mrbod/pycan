from setuptools import setup

name = 'pycan'
version = '1.0.0'

setup(name=name,
        version=version,
        description='CAN tool',
        author='Per Forser',
        packages=['pycan'],
        entry_points={
            'console_scripts': [
                'pycan=pycan.main:main',
                'biscan_conv=pycan.biscan_conv:main',
                'kvaserlog=pycan.kvaserlog:main'
                ],
            }
        )

