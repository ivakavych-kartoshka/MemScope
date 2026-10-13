"""AOSP integration contract. This module deliberately makes no Android API claims."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any


class AndroidServiceAdapter(ABC):
    """Expected bridge to MemScopeManagerService and system-owned AppSearch."""

    @abstractmethod
    def issue_task_token(self, task: Mapping[str, Any]) -> Mapping[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def query_memory(self, request: Mapping[str, Any]) -> Mapping[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def put_observation(self, request: Mapping[str, Any]) -> Mapping[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def put_derivation(self, request: Mapping[str, Any]) -> Mapping[str, Any]:
        raise NotImplementedError


class UnavailableAndroidAdapter(AndroidServiceAdapter):
    def _fail(self) -> Mapping[str, Any]:
        raise RuntimeError(
            "Android adapter unavailable: manually provision the named AOSP branch, "
            "MemScope service patch, AppSearch module, and device build"
        )

    def issue_task_token(self, task: Mapping[str, Any]) -> Mapping[str, Any]:
        return self._fail()

    def query_memory(self, request: Mapping[str, Any]) -> Mapping[str, Any]:
        return self._fail()

    def put_observation(self, request: Mapping[str, Any]) -> Mapping[str, Any]:
        return self._fail()

    def put_derivation(self, request: Mapping[str, Any]) -> Mapping[str, Any]:
        return self._fail()
