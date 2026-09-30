from setuptools import setup
from Cython.Build import cythonize

# python.exe setup.py build_ext --inplace
# cython: boundscheck=False, wraparound=False, nonecheck=False

setup(name="thermal_transfer",
      ext_modules=cythonize("thermal_transform.pyx", annotate=True))
