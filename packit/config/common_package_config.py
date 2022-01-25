# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

"""
Common package config attributes so they can be imported both in PackageConfig and JobConfig
"""
from os import getenv
from os.path import basename
from typing import Dict, List, Optional, Union

from packit.actions import ActionName
from packit.config.notifications import (
    NotificationsConfig,
    PullRequestNotificationsConfig,
)
from packit.config.sources import SourcesItem
from packit.constants import PROD_DISTGIT_URL, DISTGIT_NAMESPACE
from packit.sync import SyncFilesItem, iter_srcs


class CommonPackageConfig:
    """
    We want JobConfig to hold all the attributes from PackageConfig so we don't need to
    pass both PackageConfig and JobConfig to handlers in p-s. We also want people
    to be able to override global PackageConfig attributes per job.

                        CommonPackageConfig
                              /      \
                   PackageConfig   JobConfig
                          //
              contains [JobConfig]
    """

    def __init__(
        self,
        config_file_path: Optional[str] = None,
        specfile_path: Optional[str] = None,
        synced_files: Optional[List[SyncFilesItem]] = None,
        dist_git_namespace: str = None,
        upstream_project_url: str = None,  # can be URL or path
        upstream_package_name: str = None,
        downstream_project_url: str = None,
        downstream_package_name: str = None,
        dist_git_base_url: str = None,
        actions: Dict[ActionName, Union[str, List[str]]] = None,
        upstream_ref: Optional[str] = None,
        allowed_gpg_keys: Optional[List[str]] = None,
        create_pr: bool = True,
        sync_changelog: bool = False,
        create_sync_note: bool = True,
        spec_source_id: str = "Source0",
        upstream_tag_template: str = "{version}",
        archive_root_dir_template: str = "{upstream_pkg_name}-{version}",
        patch_generation_ignore_paths: List[str] = None,
        patch_generation_patch_id_digits: int = 4,
        notifications: Optional[NotificationsConfig] = None,
        copy_upstream_release_description: bool = False,
        sources: Optional[List[SourcesItem]] = None,
        merge_pr_in_ci: bool = True,
    ):
        self.config_file_path: Optional[str] = config_file_path
        self.specfile_path: Optional[str] = specfile_path
        self.synced_files: List[SyncFilesItem] = synced_files or []
        self.patch_generation_ignore_paths = patch_generation_ignore_paths or []
        self.patch_generation_patch_id_digits = patch_generation_patch_id_digits
        self.upstream_project_url: Optional[str] = upstream_project_url
        self.upstream_package_name: Optional[str] = upstream_package_name
        # this is generated by us
        self.downstream_package_name: Optional[str] = downstream_package_name
        self._downstream_project_url: str = downstream_project_url
        self.dist_git_base_url: str = dist_git_base_url or getenv(
            "DISTGIT_URL", PROD_DISTGIT_URL
        )
        self.dist_git_namespace: str = dist_git_namespace or getenv(
            "DISTGIT_NAMESPACE", DISTGIT_NAMESPACE
        )
        # path to a local git clone of the dist-git repo; None means to clone in a tmpdir
        self.dist_git_clone_path: Optional[str] = None
        self.actions = actions or {}
        self.upstream_ref: Optional[str] = upstream_ref
        self.allowed_gpg_keys = allowed_gpg_keys
        self.create_pr: bool = create_pr
        self.sync_changelog: bool = sync_changelog
        self.create_sync_note: bool = create_sync_note
        self.spec_source_id: str = spec_source_id
        self.notifications = notifications or NotificationsConfig(
            pull_request=PullRequestNotificationsConfig()
        )

        # template to create an upstream tag name (upstream may use different tagging scheme)
        self.upstream_tag_template = upstream_tag_template
        self.archive_root_dir_template = archive_root_dir_template
        self.copy_upstream_release_description = copy_upstream_release_description
        self.sources = sources or []
        self.merge_pr_in_ci = merge_pr_in_ci

    def __repr__(self):
        return (
            "CommonPackageConfig("
            f"specfile_path='{self.specfile_path}', "
            f"synced_files='{self.synced_files}', "
            f"dist_git_namespace='{self.dist_git_namespace}', "
            f"upstream_project_url='{self.upstream_project_url}', "
            f"upstream_package_name='{self.upstream_package_name}', "
            f"downstream_project_url='{self.downstream_project_url}', "
            f"downstream_package_name='{self.downstream_package_name}', "
            f"dist_git_base_url='{self.dist_git_base_url}', "
            f"actions='{self.actions}', "
            f"upstream_ref='{self.upstream_ref}', "
            f"allowed_gpg_keys='{self.allowed_gpg_keys}', "
            f"create_pr='{self.create_pr}', "
            f"synced_files='{self.synced_files}', "
            f"create_sync_note='{self.create_sync_note}', "
            f"spec_source_id='{self.spec_source_id}', "
            f"upstream_tag_template='{self.upstream_tag_template}', "
            f"patch_generation_ignore_paths='{self.patch_generation_ignore_paths}',"
            f"patch_generation_patch_id_digits='{self.patch_generation_patch_id_digits}',"
            f"copy_upstream_release_description='{self.copy_upstream_release_description}',"
            f"sources='{self.sources}', "
            f"merge_pr_in_ci={self.merge_pr_in_ci})"
        )

    @property
    def downstream_project_url(self) -> str:
        if not self._downstream_project_url:
            self._downstream_project_url = self.dist_git_package_url
        return self._downstream_project_url

    @property
    def dist_git_package_url(self):
        return (
            f"{self.dist_git_base_url}{self.dist_git_namespace}/"
            f"{self.downstream_package_name}.git"
        )

    def get_specfile_sync_files_item(self, from_downstream: bool = False):
        """
        Get SyncFilesItem object for the specfile.
        :param from_downstream: True when syncing from downstream
        :return: SyncFilesItem
        """
        upstream_specfile_path = self.specfile_path
        downstream_specfile_path = (
            f"{self.downstream_package_name}.spec"
            if self.downstream_package_name
            else basename(upstream_specfile_path)
        )
        return SyncFilesItem(
            src=[
                downstream_specfile_path if from_downstream else upstream_specfile_path
            ],
            dest=upstream_specfile_path
            if from_downstream
            else downstream_specfile_path,
        )

    def get_all_files_to_sync(self):
        """
        Adds the default files (config file, spec file) to synced files
        when doing propose-downstream.
        :return: Files to be synced
        """
        files = self.synced_files

        if self.specfile_path not in iter_srcs(files):
            files.append(self.get_specfile_sync_files_item())

        if self.config_file_path and self.config_file_path not in iter_srcs(files):
            # this relative because of glob: "Non-relative patterns are unsupported"
            files.append(
                SyncFilesItem(src=[self.config_file_path], dest=self.config_file_path)
            )

        return files
