# coding: utf-8

import json
import os
import re

from .base import BaseCreator
from ..core.constants import NODE_RUNTIME_RECOMMENDED, NODE_RUNTIME_VERSIONS, locks_dir
from ..core.exceptions import ProjectImportError
from ..core.json_store import file_lock


NODEJS_ROOT = "/www/server/nodejs"
NODEJS_MANAGER_MAIN = "/www/server/panel/plugin/nodejs/nodejs_main.py"
NODE_PACKAGE_MANAGERS = ("npm", "yarn", "pnpm")


def get_installed_nodejs_versions(nodejs_root=None, manager_main=None, default_node=None):
    """Return Node.js runtimes offered by the import wizard.

    The manager's online version list is intentionally not used here because
    reading the import form must not refresh remote metadata or install
    anything. A version is reported as installed only when its bin/node
    exists. Whitelist versions that are not installed yet are still offered
    as options with ``installed=False`` so the wizard can auto-install them
    later. Optional arguments and environment variables make the filesystem
    scan testable without changing production paths.
    """
    nodejs_root = nodejs_root or os.environ.get("AAPANEL_NODEJS_ROOT", NODEJS_ROOT)
    manager_main = manager_main or os.environ.get(
        "AAPANEL_NODEJS_MANAGER_MAIN",
        NODEJS_MANAGER_MAIN,
    )
    default_node = default_node or os.environ.get("AAPANEL_DEFAULT_NODE", "/usr/bin/node")
    manager_installed = os.path.isfile(manager_main)
    options = []

    if manager_installed and os.path.isdir(nodejs_root):
        default_realpath = _existing_realpath(default_node)
        for version in os.listdir(nodejs_root):
            version_root = os.path.join(nodejs_root, version)
            node_bin = os.path.join(version_root, "bin", "node")
            if not os.path.isdir(version_root) or not os.path.isfile(node_bin):
                continue
            options.append({
                "label": "Node.js {}".format(version.lstrip("v")),
                "value": version,
                "installed": True,
            })

    installed_values = [item["value"] for item in options]
    for version in NODE_RUNTIME_VERSIONS:
        if version in installed_values:
            continue
        options.append({
            "label": "Node.js {}".format(version.lstrip("v")),
            "value": version,
            # "is_default": False,
            "installed": False,
        })

    options.sort(key=lambda item: _node_version_sort_key(item["value"]), reverse=True)

    return {
        "manager_installed": manager_installed,
        "versions": [item["value"] for item in options if item.get("installed")],
        "options": options,
        "recommended_version": NODE_RUNTIME_RECOMMENDED,
        "auto_install": True,
    }


def _existing_realpath(path):
    if not path or not (os.path.exists(path) or os.path.islink(path)):
        return ""
    return os.path.realpath(path)


def _same_path(left, right):
    return os.path.normcase(os.path.abspath(left)) == os.path.normcase(os.path.abspath(right))


def _node_version_sort_key(version):
    numbers = [int(item) for item in re.findall(r"\d+", str(version))[:4]]
    numbers.extend([0] * (4 - len(numbers)))
    return tuple(numbers) + (str(version),)


def _normalize_node_version(value):
    version = str(value or "").strip()
    if version and not version.startswith("v"):
        version = "v" + version
    return version


def prepare_node_config(config, project_root, install_runtime=True, progress=None):
    """Validate Node.js settings and optionally verify the selected runtime."""
    requested = _normalize_node_version(
        config.get("runtime_version", config.get("nodejs_version", ""))
    )
    if not requested:
        raise ProjectImportError(
            "Node.js runtime version is required",
            "NODE_RUNTIME_REQUIRED",
        )

    inventory = get_installed_nodejs_versions()
    if requested not in NODE_RUNTIME_VERSIONS and requested not in inventory["versions"]:
        raise ProjectImportError(
            "Unsupported Node.js runtime '{}'".format(requested),
            "NODE_RUNTIME_UNSUPPORTED",
        )

    package_manager = str(config.get("package_manager", "npm") or "npm").strip().lower()
    if package_manager not in NODE_PACKAGE_MANAGERS:
        raise ProjectImportError(
            "Unsupported Node.js package manager: {}".format(package_manager),
            "NODE_PACKAGE_MANAGER_UNSUPPORTED",
        )

    package_file = os.path.join(project_root, "package.json")
    if not os.path.isfile(package_file):
        raise ProjectImportError("package.json was not found", "NODE_PACKAGE_JSON_REQUIRED")
    try:
        with open(package_file, "r", encoding="utf-8-sig") as handle:
            package_info = json.load(handle)
    except (OSError, ValueError) as exc:
        raise ProjectImportError(
            "Invalid package.json: {}".format(exc),
            "NODE_PACKAGE_JSON_INVALID",
        )
    scripts = package_info.get("scripts", {}) if isinstance(package_info, dict) else {}
    project_script = str(config.get("project_script", config.get("start_script", "start"))).strip()
    if not isinstance(scripts, dict) or project_script not in scripts:
        raise ProjectImportError(
            "The startup script does not exist in package.json: {}".format(project_script),
            "NODE_SCRIPT_NOT_FOUND",
        )

    config["runtime_version"] = requested
    config["nodejs_version"] = requested
    config["package_manager"] = package_manager
    config["project_script"] = project_script
    if install_runtime:
        prepare_node_runtime(config, progress=progress)
    return config


def prepare_node_runtime(config, progress=None):
    """Install the selected Node.js runtime and package manager when missing."""
    import public

    version = _normalize_node_version(
        config.get("runtime_version", config.get("nodejs_version", ""))
    )
    package_manager = str(config.get("package_manager", "npm") or "npm").strip().lower()
    if not version:
        raise ProjectImportError(
            "Node.js runtime version is required",
            "NODE_RUNTIME_REQUIRED",
        )
    if package_manager not in NODE_PACKAGE_MANAGERS:
        raise ProjectImportError(
            "Unsupported Node.js package manager: {}".format(package_manager),
            "NODE_PACKAGE_MANAGER_UNSUPPORTED",
        )
    inventory = get_installed_nodejs_versions()
    if version not in NODE_RUNTIME_VERSIONS and version not in inventory["versions"]:
        raise ProjectImportError(
            "Unsupported Node.js runtime '{}'".format(version),
            "NODE_RUNTIME_UNSUPPORTED",
        )

    # Serialize concurrent imports so the same version is not installed twice.
    with file_lock(os.path.join(locks_dir(), "node_runtime.install.lock")):
        _report_runtime(progress, 0.05, "Checking Node.js Manager")
        manager = _load_node_manager(public, progress)
        from projectModelV2.nodejsModel import main as NodeModel

        project_model = NodeModel()

        node_bin = os.path.join(manager._nodejs_path, version, "bin", "node")
        if not os.path.isfile(node_bin):
            _report_runtime(progress, 0.25, "Installing Node.js {}".format(version))
            try:
                result = manager.install_nodejs(public.to_dict_obj({"version": version}))
            except Exception as exc:
                raise ProjectImportError(
                    "Failed to install Node.js {}: {}".format(version, exc),
                    "NODE_RUNTIME_INSTALL_FAILED",
                )
            if not _manager_result_ok(result, ("already installed",)):
                raise ProjectImportError(
                    BaseCreator.error_message(
                        result,
                        "Failed to install Node.js {}".format(version),
                    ),
                    "NODE_RUNTIME_INSTALL_FAILED",
                )
        if not os.path.isfile(node_bin):
            raise ProjectImportError(
                "Node.js {} installation completed without a usable node binary".format(version),
                "NODE_RUNTIME_INSTALL_INCOMPLETE",
            )

        getter = {
            "npm": project_model.get_npm_bin,
            "pnpm": project_model.get_pnpm_bin,
            "yarn": project_model.get_yarn_bin,
        }[package_manager]
        if not getter(version):
            #  系统/NVM 版本：缺失的包管理器无法经面板插件下载，回退 npm
            if package_manager != "npm" and "-" in version:
                _report_runtime(
                    progress,
                    0.75,
                    "{} is not available for Node.js {} (system Node), fallback to npm".format(
                        package_manager, version),
                )
                package_manager = "npm"
                getter = project_model.get_npm_bin
                config["package_manager"] = "npm"
            if package_manager == "npm":
                raise ProjectImportError(
                    "npm is not available for Node.js {}".format(version),
                    "NODE_PACKAGE_MANAGER_NOT_FOUND",
                )
            _report_runtime(
                progress,
                0.75,
                "Installing {} for Node.js {}".format(package_manager, version),
            )
            try:
                result = manager.install_module(public.to_dict_obj({
                    "version": version,
                    "module": package_manager,
                }))
            except Exception as exc:
                raise ProjectImportError(
                    "Failed to install {} for Node.js {}: {}".format(
                        package_manager,
                        version,
                        exc,
                    ),
                    "NODE_PACKAGE_MANAGER_INSTALL_FAILED",
                )
            if not _manager_result_ok(result, ("has been installed", "already installed")):
                raise ProjectImportError(
                    BaseCreator.error_message(
                        result,
                        "Failed to install {} for Node.js {}".format(package_manager, version),
                    ),
                    "NODE_PACKAGE_MANAGER_INSTALL_FAILED",
                )
        if not getter(version):
            raise ProjectImportError(
                "Package manager '{}' is not available for Node.js {}".format(
                    package_manager,
                    version,
                ),
                "NODE_PACKAGE_MANAGER_NOT_FOUND",
            )

        _report_runtime(progress, 1, "Node.js runtime is ready")
        return version


def _load_node_manager(public, progress=None):
    import importlib

    plugin_path = public.get_plugin_path("nodejs")
    plugin_main = os.path.join(plugin_path, "nodejs_main.py")
    if not os.path.isfile(plugin_main):
        _report_runtime(progress, 0.1, "Installing Node.js Manager")
        _install_node_manager(public)
        importlib.invalidate_caches()
    try:
        from plugin.nodejs.nodejs_main import nodejs_main
        return nodejs_main()
    except Exception as exc:
        raise ProjectImportError(
            "Failed to load Node.js Manager: {}".format(exc),
            "NODE_MANAGER_LOAD_FAILED",
        )


def _install_node_manager(public):
    """Install the Node.js Manager package using the setup-wizard package flow."""
    try:
        from panel_guide_page import GuidePage
        from panel_plugin_v2 import panelPlugin

        guide = GuidePage()
        plugin_name = "nodejs"
        plugin_version = _node_manager_install_version(public)
        temporary_path = os.path.join(public.get_panel_path(), "temp", "nodejs")
        os.makedirs(temporary_path, mode=0o700, exist_ok=True)
        archive_path = guide._download_plugin_zip(
            plugin_name,
            plugin_version,
            temporary_path,
        )
        if not archive_path or not os.path.isfile(archive_path):
            raise ProjectImportError(
                str(archive_path or "Failed to download Node.js Manager"),
                "NODE_MANAGER_DOWNLOAD_FAILED",
            )
        public.extract_archive_to_target(archive_path, temporary_path)
        nested_archive = os.path.join(temporary_path, plugin_name + ".zip")
        if os.path.isfile(nested_archive):
            os.remove(nested_archive)
        result = panelPlugin().input_zip(public.to_dict_obj({
            "plugin_name": plugin_name,
            "tmp_path": temporary_path,
        }))
        if not isinstance(result, dict) or result.get("status") != 0:
            raise ProjectImportError(
                BaseCreator.error_message(result, "Failed to install Node.js Manager"),
                "NODE_MANAGER_INSTALL_FAILED",
            )
    except ProjectImportError:
        raise
    except Exception as exc:
        raise ProjectImportError(
            "Failed to install Node.js Manager: {}".format(exc),
            "NODE_MANAGER_INSTALL_FAILED",
        )


def _node_manager_install_version(public, default="2.3"):
    """Return the plugin version to download, preferring a deployed info.json.
    """
    try:
        info_file = os.path.join(public.get_plugin_path("nodejs"), "info.json")
        if os.path.isfile(info_file):
            with open(info_file, "r", encoding="utf-8") as handle:
                info = json.load(handle)
            version = str(info.get("versions", "")).strip()
            if version:
                return version
    except (OSError, ValueError):
        pass
    return default


def _manager_result_ok(result, allowed_messages=()):
    if isinstance(result, dict) and result.get("status") is True:
        return True
    message = BaseCreator.error_message(result, "").lower()
    return any(item in message for item in allowed_messages)


def _report_runtime(progress, ratio, message):
    if progress:
        progress(ratio, message)




class NodeCreator(BaseCreator):
    def create(self):
        import public
        from projectModelV2.nodejsModel import main as NodeModel

        domains = self.domains()
        config = self.config
        args = public.to_dict_obj({
            "project_cwd": self.project_path,
            "project_name": str(config.get("project_name", "imported_node")),
            "project_script": str(config.get("project_script", config.get("start_script", "start"))),
            "port": str(config.get("port", 3000)),
            "run_user": str(config.get("run_user", "www")),
            "nodejs_version": str(config.get("runtime_version", config.get("nodejs_version", ""))),
            "project_ps": str(config.get("project_note", "Imported project")),
            "project_env": str(config.get("project_env", "")),
            "bind_extranet": 1 if domains else 0,
            "domains": [item if ":" in item else item + ":80" for item in domains],
            "is_power_on": int(config.get("is_power_on", 1)),
            "max_memory_limit": int(config.get("max_memory_limit", 0)),
            "pkg_manager": str(config.get("package_manager", "npm")),
            "package_manager": str(config.get("package_manager", "npm")),
        })
        model = NodeModel()
        result = model.create_project(args)
        payload = self.ensure_success(result)
        project_id = public.M("sites").where("name=?", (args.project_name,)).getField("id") or 0
        # 依赖安装与启动由 nodejsModel.create_project 内部完成
        # （见 nodejsModel.py 的 install_packages/start_project 调用），这里不再重复执行
        return {
            "site_id": int(project_id),
            "project_name": args.project_name,
            "domain": domains[0] if domains else "",
            "project_type": "node",
            "path": self.project_path,
            "port": int(args.port),
            "runtime_version": args.nodejs_version,
            "warnings": [],
            "raw": payload if isinstance(payload, dict) else {},
        }
