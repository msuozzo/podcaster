all: test

.PHONY: test coverage clean
test:
	python test.py

coverage:
	coverage run test.py
	coverage report -m `find podcaster -type f -name '*.py' -not -name '__init__.py' -not -name 'vlc.py'`
	coverage html

clean:
	find . -name '*~' -o -name '*.pyc' | xargs rm -f
