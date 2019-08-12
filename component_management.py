import argparse
import json
import os
import platform
import re
import requests
import shutil
import subprocess
import sys


# Global variables
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
QUIET = False
DOWNGRADE = False
LOG_LVL = 1
PKG_MGMT_BIN = "yum"
BREW_URL = "http://download.devel.redhat.com"
MBS_URL = "https://mbs.engineering.redhat.com/module-build-service/1/module-builds"
PYTHON_MODULE_LIST = "python2-pyyaml"


# A collection of Python utilities functions
def _log(lvl, msg):
    """Print a message with level 'lvl' to Console"""
    if not QUIET and lvl <= LOG_LVL:
        print(msg)

def _log_debug(msg):
    """Print a message with level DEBUG to Console"""
    msg = "\033[96mDEBUG: " + msg + "\033[00m"
    _log(4, msg)

def _log_info(msg):
    """Print a message with level INFO to Console"""
    msg = "\033[92mINFO: " + msg + "\033[00m"
    _log(3, msg)

def _log_warn(msg):
    """Print a message with level WARN to Console"""
    msg = "\033[93mWARN: " + msg + "\033[00m"
    _log(2, msg)

def _log_error(msg):
    """Print a message with level ERROR to Console"""
    msg = "\033[91mERROR: " + msg + "\033[00m"
    _log(1, msg)

def _system_status_output(cmd):
    """Run a subprocess, returning its exit code and output."""
    sp = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, shell=True)
    stdout, stderr = sp.communicate()
    ## Wait for command to terminate. Get return returncode ##
    status = sp.wait()
    return (status, stdout.decode(), stderr.decode())

def _system(cmd):
    """Run a subprocess, returning its exit code."""
    return _system_status_output(cmd)[0]

def _system_output(cmd):
    """Run a subprocess, returning its output."""
    return _system_status_output(cmd)[1]

def _run_cmd(cmd):
    """
    Run a subprocess, returning its exit code and print stdout/stderr
    to Console.
    """
    if QUIET or LOG_LVL <= 1:
        return _system_status_output(cmd)[0]
    else:
        msg = "\033[1m=> %s\033[0m" % cmd
        _log(LOG_LVL, msg)
        sp = subprocess.Popen(cmd, shell=True)
        return sp.wait()

def _exit(ret):
    """Exit from python according to the giving exit code"""
    if ret != 0:
        _log(LOG_LVL, "Please handle the ERROR(s) and re-run this script")
    sys.exit(ret)

def _exit_on_error(ret, msg):
    """Print the error message and exit from python when last command fails"""
    if ret != 0:
        _log_error(msg)
        _exit(1)

def _warn_on_error(ret, msg):
    """Print the warn message when last command fails"""
    if ret != 0:
        _log_warn(msg)
    
def _has_cmd(cmd):
    """Check whether a program is installed"""
    return _system("command -v %s" % cmd) == 0

def _has_rpm(pkg):
    """Check whether a package is installed"""
    return _system("rpm -q %s" % pkg)

def _has_mod_spec(mod_spec):
    """Check whether a module or module stream could be used"""
    return _system("%s module info %s" % (PKG_MGMT_BIN, mod_spec))

def _chk_mod_enabled(mod_spec):
    """Check whether a module or module stream is enabled"""
    return _system("%s module list --enabled %s" % (PKG_MGMT_BIN, mod_spec))

def _chk_mod_disabled(mod_spec):
    """Check whether a module or module stream is disabled"""
    return _system("%s module list --disabled %s" % (PKG_MGMT_BIN, mod_spec))

def _chk_mod_installed(mod_spec):
    """Check whether a module or module stream is installed"""
    return _system("%s module list --installed %s" % (PKG_MGMT_BIN, mod_spec))

def _parse_brew_pkg(brew_pkg):
    """
    Parse the argument to get information of brew package.
    : return build:  Build name expected to be installed
    : return pkgs:   RPMs list included in the build which are expected to be
                     installed. If None, all the RPMs included in the build
                     will be installed
    : return arches: Architecture specified RPMs will be installed. If None,
                     the default value are the host machine type and noarch
    """
    build = brew_pkg.split('/')[0]
    tag = ''
    pkgs = ''
    arches = platform.machine()
    if build.find("@") >= 0:
        tag = build.split('@')[1]
        build = build.split('@')[0]
        cmd = "brew latest-build %s %s --quiet 2>&1" % (tag, build)
        (ret, out, _) = _system_status_output(cmd)
        _exit_on_error(ret, "Failed to get the latest build of '%s (%s)',"
                       " command output:\n%s" % (build, tag, out))
        build = out.split()[0]
    if brew_pkg.count("/") >= 1:
        pkgs = brew_pkg.split('/')[1]
    if brew_pkg.count("/") == 2:
        arches = brew_pkg.split('/')[2]
    arches += ",noarch"
    return (build, pkgs, arches)

def _get_rpm_list(build, arches):
    """
    Get RPMs list according to build name and specified architechtures.
    """
    rpm_list = []
    (ret, out, _) = _system_status_output("brew buildinfo %s 2>&1" % build)
    _exit_on_error(ret, "Failed to get build infomation of '%s', command"
                   " output:\n%s" % (build, out))
    rpms = re.search(r"RPMs\s*:\s*([^:]*)", out, re.I).group(1)
    for rpm in rpms.splitlines():
        for arch in arches.split(','):
            if rpm.find("%s.rpm" % arch) >= 0:
                rpm_list.append(rpm.replace("/mnt/redhat", BREW_URL))
    return rpm_list

def _get_required_rpm_list(rpm_list, pkgs):
    """
    Get required RPMs from the RPMs list. If no specific RPMs are specified,
    all the RPMs in the list will be expected to be installed.
    """
    req_rpm_list = []
    if not pkgs:
        return rpm_list
    for pkg in pkgs.split(','):
        has_pkg = False
        for rpm in rpm_list:
            if rpm.find('/') >= 0:
                pkg_name = rpm.rsplit('/', 1)[1].rsplit('-', 2)[0]
            else:
                pkg_name = rpm.rsplit('-', 2)[0]
            if pkg_name == pkg:
                has_pkg = True
                req_rpm_list.append(rpm)
        if not has_pkg:
            _log_info("'%s' is not in '%s', skipped" % (pkg, rpm_list))
    return req_rpm_list if req_rpm_list else rpm_list

def _get_mod_info_from_mbs(mod_id):
    """
    Get module information according to the module id from MBS.
    """
    mod_info = {}
    url = MBS_URL + '/' + mod_id
    response = json.loads(requests.get(url).text)
    mod_info['state_name'] = response.get("state_name")
    mod_info['scmurl'] = response.get("scmurl")
    mod_info['koji_tag'] = response.get("koji_tag")
    mod_info['rpms'] = response.get("tasks").get("rpms")
    return mod_info

def _check_module_is_ready(mod_id):
    """
    Check whether the module state is ready. When the state is Failed, module
    should not be used for testing.
    """
    mod_info = _get_mod_info_from_mbs(mod_id)
    if mod_info.get('state_name') == "ready":
        return True
    return False

def _get_mod_id_from_koji_tag(koji_tag):
    """
    Use the koji tag to get all the components included in the module, and then
    compare the module id in each component. The maximum module id should be
    the latest one.
    """
    mod_id = None
    (ret, cpnt_list, _) = _system_status_output("brew list-tagged %s 2>&1" %
                                                 koji_tag)
    _exit_on_error(ret, "Failed to get componenet list '%s', command"
                   " output:\n%s" % (koji_tag, cpnt_list))
    for cpnt in cpnt_list.splitlines():
        search_obj = re.search(r"module\+el[^+]+\+(\d+)\+", cpnt, re.I)
        if not search_obj:
            continue
        if not mod_id or mod_id < search_obj.group(1):
            mod_id = search_obj.group(1)
    return mod_id

def _downgrade_module_version(name, stream, release):
    """
    downgrade module version when there is no available module for current release
    """
    firstVersion = release.split('.')[0]
    secondVersion = int(release.split('.')[1])
    thirdVersion = int(release.split('.')[2])
    if stream == "rhel":
        secondVersion = secondVersion - 1
        return "%s:%s:%s.%s.%s" % (name, stream, firstVersion, secondVersion, thirdVersion)
    if thirdVersion > 0:
        thirdVersion = thirdVersion -1
    else:
        secondVersion = secondVersion -1
        stream = "%s.%s" % (firstVersion, secondVersion)
    return "%s:%s:%s.%s.%s" % (name, stream, firstVersion, secondVersion, thirdVersion)

def _get_mod_id_from_module(mod_name):
    """
    Get koji tag from module name and module stream, then use koji tag to get
    the module id.
    """
    if len(mod_name.split(':')) != 3:
        _exit_on_error(1, "Invalid module name: %s" % mod_name)
    name = mod_name.split(':')[0]
    stream = mod_name.split(':')[1]
    target_release = mod_name.split(':')[2]
    if len(target_release.split('.')) != 3:
        _exit_on_error(1, "Invalid target release: %s" % target_release)
    version = target_release.split('.')[0]
    for i in range(1,3):
        v = target_release.split('.')[i]
        if len(v) == 2:
            version = version + v
        elif len(v) == 1:
            version = version + '0' + v
        else:
            _exit_on_error(1, "Invalid target release: %s" % target_release)
    platform_tag = "module-%s-%s-%s" % (name, stream, version)
    cmd = "brew list-targets | grep %s | sort -r 2>&1" % platform_tag
    (ret, koji_tag_list, _) = _system_status_output(cmd)
    _exit_on_error(ret, "Failed to get koji tag of '%s', command"
                   " output:\n%s" % (platform_tag, koji_tag_list))
    for koji_tag in koji_tag_list.splitlines():
        mod_id = _get_mod_id_from_koji_tag(koji_tag.split()[0])
        if _check_module_is_ready(mod_id):
            return mod_id
    if DOWNGRADE:
        new_mod_name = _downgrade_module_version(name, stream, target_release)
        return _get_mod_id_from_module(new_mod_name)
    return None

def _get_mod_id_from_package(pkg_name):
    """
    Get koji tag from package name. Then get the module id from koji tag.
    Notice that not all the gotten koji tags could be used. Some of them may
    be belonged to a aborted module.
    """
    if pkg_name.startswith("module-virt"):
        tags = pkg_name
    else:
        (ret, out, _) = _system_status_output("brew buildinfo %s 2>&1" %
                                              pkg_name)
        _exit_on_error(ret, "Failed to get build infomation of '%s', command"
                       " output:\n%s" % (pkg_name, out))
        tags = re.search(r"Tags\s*:\s*(.*)", out, re.I).group(1)
    tag_list = tags.split()
    tag_list.reverse()
    for koji_tag in tag_list:
        if koji_tag.endswith("-build"):
            continue
        mod_id = _get_mod_id_from_koji_tag(koji_tag)
        if _check_module_is_ready(mod_id):
            return mod_id
    return None

def _get_mod_id(mod_id):
    """
    Get module id
    """
    if mod_id.isdigit():
        return mod_id
    if mod_id.startswith('virt:'):
        return _get_mod_id_from_module(mod_id)
    return _get_mod_id_from_package(mod_id)

def _get_rpm_list_from_virt_yaml(mod_info):
    """
    Get RPMs list for virt module from the yaml configuration.
    """
    import yaml
    repo_dir = os.path.join(ROOT_DIR, "virt")
    yaml_conf = os.path.join(repo_dir, "virt.yaml")
    repo = mod_info.get("scmurl").split('?#')[0]
    commit_hash = mod_info.get("scmurl").split('?#')[1]
    if os.path.exists(repo_dir):
        shutil.rmtree(repo_dir)
    (ret, _, err) = _system_status_output("git clone %s %s" % (repo, repo_dir))
    _exit_on_error(ret, "Failed to clone repo '%s', Error message:\n%s" %
                   (repo, err))
    _system("git -C %s checkout %s" % (repo_dir, commit_hash))
    virt_info = yaml.load(open(yaml_conf))
    rpms_info = virt_info.get("data").get("components").get("rpms")
    return rpms_info

def _get_cpnt_list_for_qemu(mod_info):
    """
    Get component list for qemu and qemu dependencies.
    """
    cpnt_list = []
    rpms_info = _get_rpm_list_from_virt_yaml(mod_info)
    for rpm in rpms_info.keys():
        if rpms_info.get(rpm).get("rationale").find("qemu-kvm") < 0:
            continue
        if not rpms_info.get(rpm).get("arches"):
            cpnt_list.append(rpm)
            continue
        if platform.machine() in rpms_info.get(rpm).get("arches"):
            cpnt_list.append(rpm)
    cpnt_list.append('qemu-kvm')
    return cpnt_list

def _get_pkg_list_for_qemu(mod_id):
    """
    Get package list for qemu and qemu dependencies.
    """
    pkg_list = []
    mod_info = _get_mod_info_from_mbs(mod_id)
    cpnt_list = _get_cpnt_list_for_qemu(mod_info)
    for cpnt in cpnt_list:
        pkg_list.append(mod_info.get("rpms").get(cpnt).get("nvr"))
    return pkg_list

def _install_pkg_list(pkg_list):
    """
    Install required packages.
    """
    (ret, _, err) = _system_status_output("%s install -y %s" %
                                          (PKG_MGMT_BIN, pkg_list))
    _exit_on_error(ret, "Install packages '%s' failed, error message: %s" %
                   (pkg_list, err))


# A collection of Python basic functions
def enable_mod(mod_spec_list):
    """
    Enable all the module streams in the module spec list and make the stream
    RPMs available in the package set.
    """
    if not mod_spec_list:
        return
    for mod_spec in mod_spec_list.split():
        _exit_on_error(_has_mod_spec(mod_spec),
                       "Module '%s' doesn't exist" % mod_spec)
        if _chk_mod_enabled(mod_spec) == 0:
            continue
        _log_info("Enable Module %s" % mod_spec)
        (ret, _, err) = _system_status_output("%s module enable -y %s"
                                              % (PKG_MGMT_BIN, mod_spec))
        if ret != 0:
            _exit_on_error(_chk_mod_enabled(mod_spec),
                           "Module '%s' wasn't enabled(%s)" % (mod_spec, err))

def disable_mod(mod_spec_list):
    """
    Disable all the module in the module spec list. All related module streams
    will become unavailable.
    """
    if not mod_spec_list:
        return
    for mod_spec in mod_spec_list.split():
        _exit_on_error(_has_mod_spec(mod_spec),
                       "Module '%s' doesn't exist" % mod_spec)
        mod_name = mod_spec.split(":")[0]
        if _chk_mod_disabled(mod_name) == 0:
            continue
        _log_info("Disable Module %s" % mod_name)
        (ret, _, err) = _system_status_output("%s module disable -y %s"
                                              % (PKG_MGMT_BIN, mod_name))
        if ret !=0:
            _exit_on_error(_chk_mod_disabled(mod_name),
                           "Module '%s' wasn't disabled(%s)" %
                           (mod_name, err))

def install_mod(mod_spec_list):
    """
    Install all the module profiles incl. their RPMs in the module spec list.
    In case no profile was provided, all default profiles get installed. Module
    streams get enabled accordingly.
    """
    if not mod_spec_list:
        return
    for mod_spec in mod_spec_list.split():
        _exit_on_error(_has_mod_spec(mod_spec),
                       "Module '%s' doesn't exist" % mod_spec)
        if _chk_mod_installed(mod_spec) == 0:
            continue
        mod_name = mod_spec.split(":")[0]
        if _chk_mod_installed(mod_name) == 0:
            _system("%s module remove -y %s" % (PKG_MGMT_BIN, mod_name))
        _log_info("Install Module %s" % mod_spec)
        out = _system_output("dnf module info %s" % mod_spec)
        search_obj = re.search(r"Default profiles\s+:\s+(\S*)", out, re.I)
        if not search_obj:
            profile = re.search(r"Profiles\s+:\s+(\S*)",
                                out, re.I).group(1).split(',')[0]
            mod_spec = mod_spec + '/' + profile
        (ret, _, err) = _system_status_output("%s module install -y %s" %
                                              (PKG_MGMT_BIN, mod_spec))
        if ret != 0:
            _exit_on_error(_chk_mod_installed(mod_spec.split('/')[0]),
                           "Module '%s' wasn't installed(%s)" %
                           (mod_spec, err))

def install_pkg_from_repo(repo_pkg_list):
    """
    Install all the packages and their dependencies in the package list
    from any enabled repository.
    """
    if not repo_pkg_list:
        return
    for repo_pkg in repo_pkg_list.split():
        if _has_rpm(repo_pkg) == 0:
            if PKG_MGMT_BIN == "dnf":
                (ret, _, err) = _system_status_output("%s distro-sync -y %s" %
                                                      (PKG_MGMT_BIN, repo_pkg))
                _exit_on_error(ret, "Package '%s' wasn't synced(%s)" %
                               (repo_pkg, err))
            continue
        _log_info("Install package %s" % repo_pkg)
        (ret, _, err) = _system_status_output("%s install -y %s" %
                                              (PKG_MGMT_BIN, repo_pkg))
        if ret != 0:
            _exit_on_error(_has_rpm(repo_pkg),
                           "Package '%s' wasn't installed(%s)" %
                           (repo_pkg, err))

def install_pkg_from_brew(brew_pkg_list):
    """
    Install all the packages and their dependencies in the package list
    from brew.
    """
    if not brew_pkg_list:
        return
    for brew_pkg in brew_pkg_list.split():
        (build, pkgs, arches) = _parse_brew_pkg(brew_pkg)
        rpm_list = _get_rpm_list(build, arches)
        install_rpm_list = _get_required_rpm_list(rpm_list, pkgs)
        _log_info("Install package %s" % build)
        (ret, _, err) = _system_status_output("%s install -y %s" %
                                              (PKG_MGMT_BIN,
                                               ' '.join(install_rpm_list)))
        if ret != 0:
            _exit_on_error(_has_rpm(build),
                           "Package '%s' wasn't installed(%s)" %
                           (build, err))

def install_virt_qemu_from_brew(mod_id):
    """
    Install qemu and qemu dependencies included a virt module. Other packages
    like libvirt wouldn't be installed. The argument could module id, qemu
    package, koji tag, and module name with stream.
    """
    if not mod_id:
        return
    mod_id = _get_mod_id(mod_id)
    if not mod_id:
        _exit_on_error(1, "Failt to get module id")
    _log_info("Module id is %s" % mod_id)
    pkg_list = _get_pkg_list_for_qemu(mod_id)
    disable_mod("virt")
    install_pkg_from_brew(' '.join(pkg_list))

def parse_opts():
    """
    Parse arguments.
    """
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument(
        '--enable-module',
        action="store",
        help='''
             Enable module streams in the module list and make the stream RPMs available in the package set.
             Support to enable multiple modules at once, which are separated by space. Example:
             Enable slow train virt module: --enable-module 'virt:rhel'
             Enable fast train virt module: --enable-module 'virt:8.0'
             '''
    )
    parser.add_argument(
        '--disable-module',
        action="store",
        help='''
             Disable a module. All related module streams will become unavailable. Support to disable multiple
             modules at once, which are separated by space. Example:
             Disable virt module: --disable-module 'virt' or --disable-module 'virt:rhel'
             '''
    )
    parser.add_argument(
        '--install-module',
        action="store",
        help='''
             Install module profiles incl. their RPMs. In case no profile was provided, all default profiles get
             installed. Module streams get enabled accordingly. Support to install multiple modules at once, which
             are separated by space. Example:
             Install slow train virt module: --install-module 'virt:rhel'
             Install fast train virt module: --install-module 'virt:8.0'
             '''
    )
    parser.add_argument(
        '--install-repopkg',
        action="store",
        help='''
             Install the package and the dependencies from any enabled repository. Support to install multiple
             packages at once, which are separated by space. Example:
             Install qemu-kvm and qemu-kvm-debuginfo: --install-repopkg 'qemu-kvm qemu-kvm-debuginfo'
             '''
    )
    parser.add_argument(
        '--install-brewpkg',
        action="store",
        help='''
             Install the package and the dependencies from brew. Support to install multiple packages at once,
             which are separated by space. Example:
             Install specified qemu: --install-brewpkg 'qemu-kvm-rhev-2.12.0-21.el7'
             Install the latest package: --install-brewpkg 'qemu-kvm-rhev@rhevh-rhel-7.6-candidate'
             Install the specific RPMs:
             --install-brewpkg 'qemu-kvm-rhev@rhevh-rhel-7.6-candidate/qemu-img-rhev,qemu-kvm-rhev'
             Install the specific RPMs with specific architecture:
             --install-brewpkg 'qemu-kvm-rhev@rhevh-rhel-7.6-candidate/qemu-img-rhev,qemu-kvm-rhev/ppc64le,noarch'
             '''
    )
    parser.add_argument(
        '--install-virtqemu',
        action="store",
        help='''
             Install qemu and qemu dependencies included a virt module. Other packages like libvirt wouldn't be
             installed. The argument could module id, qemu package, koji tag, and module name with stream. Example:
             Module id: --install-virtqemu '3143'
             QEMU package: --install-virtqemu 'qemu-kvm-2.12.0-69.module+el8.1.0+3143+457f984c'
             Koji tag: --install-virtqemu 'module-virt-rhel-8010020190503000142-cdc1202b'
             Module name: --install-virtqemu 'virt:rhel:8.1.0' or --install-virtqemu 'virt:8.0:8.0.1'
             '''
    )
    parser.add_argument(
        '-v', '--verbose',
        action="store_true",
        default=False,
        help='''
             give detailed output
             '''
    )
    parser.add_argument(
        '-q', '--quiet',
        action="store_true",
        default=False,
        help='''
             give less output
             '''
    )
    parser.add_argument(
        '-d', '--downgrade',
        action="store_true",
        default=False,
        help='''
             downgrade module version when there is no available module for current release
             '''
    )
    return vars(parser.parse_args())

if __name__ == "__main__":
    opts = parse_opts()
    if opts.get("verbose"):
        LOG_LVL = 4
    if opts.get("quiet"):
        QUIET = True
    if opts.get("downgrade"):
        DOWNGRADE = True
    if _has_cmd('python3'):
        PYTHON_MODULE_LIST = "python3-pyyaml"
    if _has_cmd('dnf'):
        PKG_MGMT_BIN="dnf"
        _install_pkg_list(PYTHON_MODULE_LIST)
        enable_mod(opts.get("enable_module"))
        disable_mod(opts.get("disable_module"))
        install_mod(opts.get("install_module"))
        install_virt_qemu_from_brew(opts.get("install_virtqemu"))
    install_pkg_from_repo(opts.get("install_repopkg"))
    install_pkg_from_brew(opts.get("install_brewpkg"))
