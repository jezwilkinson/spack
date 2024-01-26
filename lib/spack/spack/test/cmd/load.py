# Copyright 2013-2024 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)
import os
import re

import pytest

import spack.spec
import spack.user_environment as uenv
import spack.util.environment
from spack.main import SpackCommand

load = SpackCommand("load")
unload = SpackCommand("unload")
install = SpackCommand("install")
location = SpackCommand("location")

pytestmark = pytest.mark.not_on_windows("does not run on windows")


def test_manpath_trailing_colon(
    install_mockery, mock_fetch, mock_archive, mock_packages, working_env
):
    """Test that the commands generated by load add the MANPATH prefix
    inspections. Also test that Spack correctly preserves the default/existing
    manpath search path via a trailing colon"""
    install("mpileaks")

    sh_out = load("--sh", "mpileaks")
    lines = sh_out.split("\n")
    assert any(re.match(r"export MANPATH=.*:;", ln) for ln in lines)

    os.environ["MANPATH"] = "/tmp/man:"

    sh_out = load("--sh", "mpileaks")
    lines = sh_out.split("\n")
    assert any(re.match(r"export MANPATH=.*:/tmp/man:;", ln) for ln in lines)


def test_load_recursive(install_mockery, mock_fetch, mock_archive, mock_packages, working_env):
    """Test that `spack load` applies prefix inspections of its required runtime deps in
    topo-order"""
    install("mpileaks")
    mpileaks_spec = spack.spec.Spec("mpileaks").concretized()

    # Ensure our reference variable is cleed.
    os.environ["CMAKE_PREFIX_PATH"] = "/hello:/world"

    sh_out = load("--sh", "mpileaks")
    csh_out = load("--csh", "mpileaks")

    def extract_cmake_prefix_path(output, prefix):
        return next(cmd for cmd in output.split(";") if cmd.startswith(prefix))[
            len(prefix) :
        ].split(":")

    # Map a prefix found in CMAKE_PREFIX_PATH back to a package name in mpileaks' DAG.
    prefix_to_pkg = lambda prefix: next(
        s.name for s in mpileaks_spec.traverse() if s.prefix == prefix
    )

    paths_sh = extract_cmake_prefix_path(sh_out, prefix="export CMAKE_PREFIX_PATH=")
    paths_csh = extract_cmake_prefix_path(csh_out, prefix="setenv CMAKE_PREFIX_PATH ")

    # Shouldn't be a difference between loading csh / sh, so check they're the same.
    assert paths_sh == paths_csh

    # We should've prepended new paths, and keep old ones.
    assert paths_sh[-2:] == ["/hello", "/world"]

    # All but the last two paths are added by spack load; lookup what packages they're from.
    pkgs = [prefix_to_pkg(p) for p in paths_sh[:-2]]

    # Do we have all the runtime packages?
    assert set(pkgs) == set(
        s.name for s in mpileaks_spec.traverse(deptype=("link", "run"), root=True)
    )

    # Finally, do we list them in topo order?
    for i, pkg in enumerate(pkgs):
        set(s.name for s in mpileaks_spec[pkg].traverse(direction="parents")) in set(pkgs[:i])

    # Lastly, do we keep track that mpileaks was loaded?
    assert f"export {uenv.spack_loaded_hashes_var}={mpileaks_spec.dag_hash()}" in sh_out
    assert f"setenv {uenv.spack_loaded_hashes_var} {mpileaks_spec.dag_hash()}" in csh_out


def test_load_includes_run_env(install_mockery, mock_fetch, mock_archive, mock_packages):
    """Tests that environment changes from the package's
    `setup_run_environment` method are added to the user environment in
    addition to the prefix inspections"""
    install("mpileaks")

    sh_out = load("--sh", "mpileaks")
    csh_out = load("--csh", "mpileaks")

    assert "export FOOBAR=mpileaks" in sh_out
    assert "setenv FOOBAR mpileaks" in csh_out


def test_load_first(install_mockery, mock_fetch, mock_archive, mock_packages):
    """Test with and without the --first option"""
    install("libelf@0.8.12")
    install("libelf@0.8.13")

    # Now there are two versions of libelf, which should cause an error
    out = load("--sh", "libelf", fail_on_error=False)
    assert "matches multiple packages" in out
    assert "Use a more specific spec" in out

    # Using --first should avoid the error condition
    load("--sh", "--first", "libelf")


def test_load_fails_no_shell(install_mockery, mock_fetch, mock_archive, mock_packages):
    """Test that spack load prints an error message without a shell."""
    install("mpileaks")

    out = load("mpileaks", fail_on_error=False)
    assert "To set up shell support" in out


def test_unload(install_mockery, mock_fetch, mock_archive, mock_packages, working_env):
    """Tests that any variables set in the user environment are undone by the
    unload command"""
    install("mpileaks")
    mpileaks_spec = spack.spec.Spec("mpileaks").concretized()

    # Set so unload has something to do
    os.environ["FOOBAR"] = "mpileaks"
    os.environ[uenv.spack_loaded_hashes_var] = "%s:%s" % (mpileaks_spec.dag_hash(), "garbage")

    sh_out = unload("--sh", "mpileaks")
    csh_out = unload("--csh", "mpileaks")

    assert "unset FOOBAR" in sh_out
    assert "unsetenv FOOBAR" in csh_out

    assert "export %s=garbage" % uenv.spack_loaded_hashes_var in sh_out
    assert "setenv %s garbage" % uenv.spack_loaded_hashes_var in csh_out


def test_unload_fails_no_shell(
    install_mockery, mock_fetch, mock_archive, mock_packages, working_env
):
    """Test that spack unload prints an error message without a shell."""
    install("mpileaks")
    mpileaks_spec = spack.spec.Spec("mpileaks").concretized()
    os.environ[uenv.spack_loaded_hashes_var] = mpileaks_spec.dag_hash()

    out = unload("mpileaks", fail_on_error=False)
    assert "To set up shell support" in out
