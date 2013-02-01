#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
	name = 'geventreactor',
	version = '0.1.0',
	description = 'Twisted reactor based on gevent',
	long_description = 'geventreactor is a gevent-powered Twisted reactor whose goal is to enable mixing of gevent- and Twisted-oriented code, allowing developers to benefit from the performance of libevent and greenlet while retaining access to the extensive functionality of Twisted.',
	license = 'MIT',
	author = 'Jiang Yio',
	author_email = 'inportb@gmail.com',
	url = 'http://github.com/jyio/geventreactor',
	packages = find_packages(),
	install_requires = ['gevent']
)
