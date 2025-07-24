from setuptools import setup, find_packages

setup(
    name='red_line_sms',
    version='0.0.1',
    description='Red Line SMS App',
    author='Kelvin Njenga',
    author_email='njengasheba@gmail.com',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        'frappe',
        'africastalking'
    ]
)
