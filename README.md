# colab_grading_client
colab notebook functions to invoke AI teaching and grading assistant

Get API tokens from testpypi.org and pypi.org
Store in ~/.pypirc

To (re) build the package:
rm -rf dist/
python -m build
twine upload --repository pypi dist/* 
