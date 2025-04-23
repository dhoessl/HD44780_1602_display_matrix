from setuptools import setup

setup(
    name='lcd_i2c_display_matrix',
    version='0.3.1-0',
    description='library to manage multiple 1602 LCD displays in a matrix',
    url='https://github.com/dhoessl/HD44780_1602_display_matrix',
    author="Dominic Hößl",
    author_email="dominichoessl@gmail.com",
    license="",
    packages=['lcd_i2c_display_matrix'],
    install_requires=['smbus', 'netifaces'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
    ]
)
