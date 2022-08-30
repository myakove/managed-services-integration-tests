import logging
import os
import shutil

import pytest
import yaml
from pytest_testconfig import config as py_config

import ocp_utilities
from utilities.logger import separator, setup_logging


LOGGER = logging.getLogger(__name__)
BASIC_LOGGER = logging.getLogger("basic")


# pytest fixtures
def pytest_addoption(parser):
    storage_group = parser.getgroup(name="Storage")
    data_collector_group = parser.getgroup(name="DataCollector")
    ocm_group = parser.getgroup(name="OCM")
    upgrade_group = parser.getgroup(name="Upgrade")

    # Storage addoption
    storage_group.addoption("--storage-classes", help="Storage classes to test")

    # Data collector group
    data_collector_group.addoption(
        "--data-collector",
        help="pass YAML file path to enable data collector to capture additional logs and resources",
    )
    data_collector_group.addoption(
        "--pytest-log-file",
        help="Path to pytest log file",
        default="pytest-tests.log",
    )

    # OCM group
    ocm_group.addoption("--cluster-name", help="Cluster name")

    # Upgrade group
    upgrade_group.addoption("--ocp-target-version", help="cluster OCP target version")


def pytest_cmdline_main(config):
    if config.getoption("--storage-classes"):
        py_config["storage_classes"] = config.getoption("--storage-classes").split(",")


def pytest_sessionstart(session):
    if session.config.getoption("log_collector"):
        # set log_collector to True if it is explicitly requested,
        # otherwise use what is set in the global config
        py_config["log_collector"] = True

    if py_config.get("log_collector", False):
        # this could already be set in the global config
        # if it is set then the environment must be configured so that openshift-python-wrapper can use it
        os.environ["TEST_COLLECT_LOGS"] = "1"

    # store the base directory for log collection in the environment so it can be used by utilities
    os.environ["TEST_COLLECT_BASE_DIR"] = session.config.getoption("log_collector_dir")

    data_collector = session.config.getoption("--data-collector")
    if data_collector:
        with open(data_collector, "r") as fd:
            py_config["data_collector"] = yaml.safe_load(fd.read())
            shutil.rmtree(
                py_config["data_collector"]["data_collector_base_directory"],
                ignore_errors=True,
            )

    tests_log_file = session.config.getoption("pytest_log_file")
    if os.path.exists(tests_log_file):
        shutil.rmtree(tests_log_file, ignore_errors=True)

    setup_logging(
        log_file=tests_log_file,
        log_level=logging.INFO,
    )


def pytest_report_teststatus(report, config):
    test_name = report.head_line
    when = report.when
    call_str = "call"
    if report.passed:
        if when == call_str:
            BASIC_LOGGER.info(f"\nTEST: {test_name} STATUS: \033[0;32mPASSED\033[0m")

    elif report.skipped:
        BASIC_LOGGER.info(f"\nTEST: {test_name} STATUS: \033[1;33mSKIPPED\033[0m")

    elif report.failed:
        if when != call_str:
            BASIC_LOGGER.info(
                f"\nTEST: {test_name} STATUS: [{when}] \033[0;31mERROR\033[0m",
            )
        else:
            BASIC_LOGGER.info(f"\nTEST: {test_name} STATUS: \033[0;31mFAILED\033[0m")


def pytest_runtest_setup(item):
    """
    Use incremental
    """
    BASIC_LOGGER.info(f"\n{separator(symbol_='-', val=item.name)}")
    BASIC_LOGGER.info(f"{separator(symbol_='-', val='SETUP')}")

    if item.session.config.getoption("--data-collector"):
        py_config["data_collector"][
            "collector_directory"
        ] = ocp_utilities.data_collector.prepare_test_data_dir(
            item=item, prefix="setup"
        )


def pytest_sessionfinish(session, exitstatus):
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    deselected_str = "deselected"
    deselected = len(reporter.stats.get(deselected_str, []))
    summary = (
        f"{deselected} {deselected_str}, "
        f"{reporter.pass_count} {'passed'}, "
        f"{reporter.skip_count} {'skipped'}, "
        f"{reporter.fail_count} {'failed'}, "
        f"{reporter.error_count} {'error'}, "
        f"{reporter.xfail_count} {'xfail'}, "
        f"{reporter.xpass_count} {'xpass'}, "
        f"exit status {exitstatus} "
    )
    BASIC_LOGGER.info(f"{separator(symbol_='-', val=summary)}")

    # Remove empty directories from data collector directory
    if session.config.getoption("--data-collector"):
        collector_directory = py_config["data_collector"][
            "data_collector_base_directory"
        ]
        for root, dirs, files in os.walk(collector_directory, topdown=False):
            for _dir in dirs:
                dir_path = os.path.join(root, _dir)
                if not os.listdir(dir_path):
                    shutil.rmtree(dir_path, ignore_errors=True)


def pytest_runtest_call(item):
    BASIC_LOGGER.info(f"{separator(symbol_='-', val='CALL')}")
    if item.session.config.getoption("--data-collector"):
        py_config["data_collector"][
            "collector_directory"
        ] = ocp_utilities.data_collector.prepare_test_data_dir(item=item, prefix="call")


def pytest_runtest_teardown(item):
    BASIC_LOGGER.info(f"{separator(symbol_='-', val='TEARDOWN')}")
    if item.session.config.getoption("--data-collector"):
        py_config["data_collector"][
            "collector_directory"
        ] = ocp_utilities.data_collector.prepare_test_data_dir(item=item, prefix="call")


@pytest.fixture(scope="session")
def junitxml_plugin(request, record_testsuite_property):
    return (
        record_testsuite_property
        if request.config.pluginmanager.has_plugin("junitxml")
        else None
    )
