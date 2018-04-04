from setuptools import setup, find_packages

def readme():
    with open('README.md') as f:
        return f.read()

setup(
    name='wishful_module_spectral_scan_usrp',
    version='0.1.0',
    packages=find_packages(),
    url='http://www.wishful-project.eu/software',
    license='',
    author='',
    author_email='',
    description='WiSHFUL Module - Spectral Scan USRP ',
    long_description='Implementation of a wireless agent using the unified programming interfaces (UPIs) of the Wishful project.',
    keywords='wireless control',
    install_requires=[]
)
