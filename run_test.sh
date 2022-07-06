#!/bin/bash
pipenv run pytest -o --bugzilla  --jira -x --pdb -s --skip-deprecated-api-test --pdbcls=IPython.terminal.debugger:TerminalPdb --junit-xml=~/xunit_results.xml --cluster-sanity-skip-check $1