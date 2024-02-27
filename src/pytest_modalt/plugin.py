import pytest

from pytest_modalt import main


def pytest_addoption(parser):
    group = parser.getgroup("modalt")
    group.addoption(
        "--modal-subrun",
        action="store",
        default=None,
        help="",
    )
    group.addoption(
        "--modal-mainrun",
        action="store",
        default=None,
        help="",
    )


#
# @pytest.hookimpl()
# def pytest_collection_modifyitems(config, items):
#     """Only select a subset of tests to run, based on the --subset option."""
#     node_ids = [f.nodeid for f in items]
#     node_ids.sort()


@pytest.hookimpl()
def pytest_runtest_logreport(report):
    if main.send_reports:
        main.mystub.test_report_queue.put(report)


@pytest.hookimpl()
def pytest_runtestloop(session) -> bool:
    if session.testsfailed and not session.config.option.continue_on_collection_errors:
        raise session.Interrupted(
            "%d error%s during collection"
            % (session.testsfailed, "s" if session.testsfailed != 1 else "")
        )

    if session.config.option.collectonly:
        return True
    modal_subrun = session.config.getoption("--modal-subrun")
    modal_mainrun = session.config.getoption("--modal-mainrun")

    if modal_mainrun:
        node_ids = [f.nodeid for f in session.items]
        main.run_node_ids(node_ids, session)
    else:
        # normal pytest run
        for i, item in enumerate(session.items):
            nextitem = session.items[i + 1] if i + 1 < len(session.items) else None
            item.config.hook.pytest_runtest_protocol(item=item, nextitem=nextitem)

            if session.shouldfail:
                raise session.Failed(session.shouldfail)
            if session.shouldstop:
                raise session.Interrupted(session.shouldstop)

    return True


def pytest_report_teststatus(report, config):
    # hide the status outputs
    if config.getoption("--modal-subrun"):
        category, short, verbose = "", "", ""
        return category, short, verbose

    return None
