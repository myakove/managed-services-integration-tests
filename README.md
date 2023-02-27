# managed-services-integration-tests

This repository contains tests.

The infra for the tests can be found in https://github.com/RedHatQE/openshift-python-wrapper and https://github.com/RedHatQE/openshift-python-utilities
flake8 plugins defined in .flake8 can be found in https://github.com/RedHatQE/flake8-plugins

## Setup VirtualEnv
Use [poetry](https://python-poetry.org/docs/) to manage virtualenv.
```bash
pip install poetry
```
After installation, run:
```bash
poetry install
```
To get current env info
```bash
poetry env info
```
To get poetry virtualenv names
```bash
poetry env list
```
To remove current env
```bash
poetry env remove <env name>
```

To update one package
```bash
poetry update openshift-python-wrapper --no-cache
```

# Getting started

## Prepare a cluster

This project runs tests against an OCP cluster running on OSD / ROSA.
Export the cluster's kubeconfig file as KUBECONFIG
```bash
ocm get clusters -p search="name like '"<cluster name>"%'" | jq -r  '.items | .[] | .id' | xargs -I {} ocm get /api/clusters_mgmt/v1/clusters/{}/credentials | jq -r .kubeconfig > ~/kubeconfig ; export KUBECONFIG=~/kubeconfig
```

### Logging
Log file 'pytest-tests.log' is generated with the full pytest output in the tests root directory.
For each test failure cluster logs are collected and stored under 'tests-collected-info'.

To see verbose logging of a test run, add the following parameter:

```bash
make tests PYTEST_ARGS="-o log_cli=true"
```
To enable data-collector pass data-collector.yaml
YAML format:
```yaml
    data_collector_base_directory: "<base directory for data collection>"
    collect_data_function: "<import path for data collection method>"

```
YAML Example:
```yaml
    data_collector_base_directory: "tests-collected-info"
    collect_data_function: "ocp_wrapper_data_collector.data_collector.collect_data"
    collect_pod_logs: true
```
```bash
poetry run pytest .... --data-collector=data-collector.yaml

Logs will be available under tests-collected-info/ folder.

#### Cluster upgrade tests

To run the cluster upgrade test, you will need to provide the cluster name and the OCP target version.

Example:
poetry run pytest -m upgrade --ocp-target-version 4.10.35 --cluster-name <cluster name> --data-collector=<path to data collector yaml>

If running against a production cluster, add:
--tc=api_server:production

### Setting log level in command line

In order to run a test with a log level that is different from the default,
use the --log-cli-level command line switch.
The full list of possible log level strings can be found here:
https://docs.python.org/3/library/logging.html#logging-levels

When the switch is not used, we set the default level to INFO.

Example:
```bash
--log-cli-level=DEBUG
````

### Building and pushing tests container image

Container can be generated and pushed using make targets.

```
make -f Makefile
```

## How-to verify your patch

### Check the code
We use checks tools that are defined in .pre-commit-config.yaml file
To install pre-commit:
```bash
pip install pre-commit --user
pre-commit install
pre-commit install --hook-type commit-msg
```
pre-commit will try to fix the error.
If some error where fixed git add & git commit is needed again.
commit-msg use gitlint (https://jorisroovers.com/gitlint/)

To check for PEP 8 issues locally run:
```bash
tox
```

### Run functional tests via Jenkins job
`TODO`

##### Known Issues
pycurl may fail with error:
ImportError: pycurl: libcurl link-time ssl backend (nss) is different from compile-time ssl backend (none/other)

To fix it:
```bash
export PYCURL_SSL_LIBRARY=nss # or openssl. depend on the error (link-time ssl backend (nss))
poetry run pip uninstall pycurl
poetry run pip install pycurl --no-cache-dir
```

# Running with OCM client
Export `OCM_TOKEN` env variable locally or in test container
```bash
export OCM_TOKEN="production or stage OCM token"
```

# Overwrite global_config execution configuration.
You can overwrite the api server defined in global_config.py by passing the following in command line:
For example:
```bash
poetry run pytest ... --tc=api_server:stage
```
