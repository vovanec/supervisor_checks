from setuptools import setup, find_packages


install_requires = ['supervisor>=4.0.0',
                    'psutil']


tests_require = install_requires + []


setup(
    name='supervisor_checks',
    packages=find_packages(),
    version='0.1.0',
    description='Framework to build health checks for Supervisor-based services.',
    author='Vovan Kuznetsov',
    author_email='vovanec@gmail.com',
    maintainer_email='vovanec@gmail.com',
    url='https://github.com/vovanec/supervisor_checks',
    download_url='https://github.com/vovanec/supervisor_checks/tarball/0.1.0',
    keywords=['supervisor', 'event', 'listener', 'eventlistener',
              'http', 'memory', 'xmlrpc', 'health', 'check', 'monitor'],
    license='MIT',
    classifiers=['License :: OSI Approved :: MIT License',
                 'Development Status :: 4 - Beta',
                 'Intended Audience :: Developers',
                 'Programming Language :: Python :: 3.4'],
    install_requires=install_requires,
    tests_require=tests_require,
    test_suite='nose.collector',
    extras_require={
        'test': tests_require,
    },
    entry_points={
        'console_scripts': [
            'supervisor_memory_check=supervisor_checks.bin.memory_check:main',
            'supervisor_http_check=supervisor_checks.bin.http_check:main',
            'supervisor_tcp_check=supervisor_checks.bin.tcp_check:main',
            'supervisor_complex_check=supervisor_checks.bin.complex_check:main']
    }
)
