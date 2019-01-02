from setuptools import setup


setup(
    name='wework',
    version='0.0.1',
    keywords=('work wechat sdk', ),
    description='dead simple work wechat sdk',
    author='Quseit',
    author_email='river@quseit.com',
    packages=['wework'],
    include_package_data=True,
    license='Apache License',
    install_requires=('requests', ),
)