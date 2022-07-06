#!/bin/bash
pipenv run pytest -o log_cli=true  -x --pdb -s --pdbcls=IPython.terminal.debugger:TerminalPdb --junit-xml=xunit_results.xml $1