import os.path
import queue
from functools import lru_cache

import modal
import pytest
from modal import Mount

from pytest_modalt.ignoring import find_project_root, get_nonignored_file_paths


def file_filter(path: str):
    include = path[2:] in files_for_inclusion()
    return include


@lru_cache
def files_for_inclusion():
    project_root = find_project_root(".")
    project_root = os.path.abspath(project_root)
    filepaths = get_nonignored_file_paths(project_root)
    return set(filepaths)


def find_requirements_file():
    """use pathspec to find any *requirements*.txt file in the project"""
    filepaths = files_for_inclusion()
    for path in filepaths:
        if "requirements" in path and path.endswith(".txt"):
            return path


image = modal.Image.debian_slim(python_version="3.11").pip_install("pytest", "pathspec")
requirements_filename = find_requirements_file()
if requirements_filename:
    image = image.pip_install_from_requirements(requirements_filename)
local_mount = Mount.from_local_dir(".", remote_path="/root", condition=file_filter)
pkg_mount = Mount.from_local_python_packages("pytest_modalt")

mystub = modal.Stub(
    "modal-t",
    image=image,
    mounts=[local_mount, pkg_mount],
)
mystub.test_report_queue = modal.Queue.new()

send_reports = False


@mystub.function()
def run_specific_test(test_node_id):
    global send_reports
    # print(f"specific test: {test_node_id}")
    cmd = [
        "--modal-subrun",
        "1",
        "-qq",
        "-rN",
        "--no-header",
        "--no-summary",
        "-o",
        "console_output_style=classic",
        test_node_id,
    ]
    # print(f"running {' '.join(cmd)}")
    send_reports = True

    from pytest_modalt import plugin

    exit_code = pytest.main(cmd, plugins=[plugin])
    return exit_code


@mystub.local_entrypoint()
def run_node_ids(node_ids, session):
    report_counter = 0
    def process_reports():
        nonlocal report_counter
        while True:
            try:
                reports = mystub.test_report_queue.get_many(10, timeout=0.5)
            except queue.Empty:
                break
            for report in reports:
                session.config.hook.pytest_runtest_logreport(report=report)
                report_counter += 1
                # print(f"report {report_counter}: {report.nodeid} {report.outcome}")
            if not reports:
                break

    for exit_code in run_specific_test.map(node_ids, order_outputs=False):
        if report_counter >= len(node_ids) * 3:
            break
        process_reports()


    process_reports()


@mystub.local_entrypoint()
def run_pytest():
    exit_code = pytest.main(["-v", "--modal-mainrun", "1"])
