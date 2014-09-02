from setuptools import setup

name = 'pycan'
version = '1.0.0'

setup(name=name,
        version=version,
        description='CAN tool',
        author='Per Forser',
        packages=['pycan',
                'pycan.canchannel',
                'pycan.canmsg',
                'pycan.kvaser',
                'pycan.kvaserlog'
                ],
        entry_points={
            'console_scripts': [
                'pycan=pycan.main:main',
                'kvaserlog=pycan.kvaserlog.kvaserlog:main'
                ],
            }
        )

