"""Integrate with `poethepoet` for callback hooks.

## Example

The following `config-ninja`_ settings file configures two local backends connected to three `poethepoet` hooks:
```yaml
.. include:: ../../examples/hooks.yaml
    :end-before: example-0
```
```yaml
  example-0:
.. include:: ../../examples/hooks.yaml
    :start-after: example-0:
    :end-before: example-1
```
```yaml
  example-1:
.. include:: ../../examples/hooks.yaml
    :start-after: example-1:
    :end-before: # define
```
```yaml
# define 'poethepoet' tasks in YAML (instead of TOML)
tool.poe:
  # ref https://poethepoet.natn.io/tasks/index.html
  tasks:
.. include:: ../../examples/hooks.yaml
    :start-after: tasks:
```
.. _config-ninja: https://config-ninja.readthedocs.io/home.html
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

# pyright: reportMissingTypeStubs=false
import poethepoet.context
import poethepoet.exceptions
from poethepoet import exceptions
from poethepoet.config import PoeConfig
from poethepoet.task.base import PoeTask, TaskContext, TaskSpecFactory
from poethepoet.task.graph import TaskExecutionGraph
from poethepoet.ui import PoeUi

__all__ = ['Hook', 'HooksEngine', 'exceptions']

logger = logging.getLogger(__name__)


class Hook:
    """Simple callable to execute the named hook with the given engine."""

    engine: HooksEngine
    """The `HooksEngine` instance contains each of the hooks that can be executed."""

    name: str
    """The name of the `poethepoet` task (`Hook`) to invoke."""

    def __init__(self, engine: HooksEngine, name: str) -> None:
        """Raise a `ValueError` if the engine does not define a hook by the given name."""
        if name not in engine:
            raise ValueError(f'Undefined hook {name!r} (options: {list(engine.tasks)})')

        self.name = name
        self.engine = engine

    def __repr__(self) -> str:
        """The string representation of the `Hook` instance.

        <!-- Perform doctest setup that is excluded from the docs
        >>> engine = ['example-hook']

        -->
        >>> Hook(engine, 'example-hook')
        <Hook: 'example-hook'>
        """
        return f'<{self.__class__.__name__}: {self.name!r}>'

    def __call__(self) -> None:
        """Invoke the `Hook` instance to execute it."""
        self.engine.execute(self.name)


class HooksEngine:
    """Encapsulate configuration for executing `poethepoet` tasks as callback hooks."""

    config: PoeConfig
    """Contains `poethepoet` configuration settings."""

    tasks: dict[str, PoeTask]
    """Name `poethepoet.task.base.PoeTask` objects for execution by name."""

    ui: PoeUi
    """Used to parse configuration for running tasks."""

    def __init__(self, config: PoeConfig, ui: PoeUi, tasks: dict[str, PoeTask]) -> None:
        """Initialize the engine with the given configuration, UI, and tasks."""
        self.config = config
        self.tasks = tasks
        self.ui = ui

    def __contains__(self, item: str) -> bool:
        """Convenience method for checking if a hook is defined in the engine."""
        return item in self.tasks

    def get_hook(self, name: str) -> Hook:
        """Initialize a `Hook` instance for running the `poethepoet.task.base.PoeTask` of the given name."""
        return Hook(self, name)

    def get_run_context(self, multistage: bool = False) -> poethepoet.context.RunContext:
        """Create a `poethepoet.context.RunContext` instance for executing tasks.

        This method is based on `poethepoet.app.PoeThePoet.get_run_context()` (`reference`_).

        .. _reference: https://github.com/nat-n/poethepoet/blob/3c9fd8bcffde8a95c5cd9513923d0f43c1507385/poethepoet/app.py#L210-L225
        """
        return poethepoet.context.RunContext(
            config=self.config,
            ui=self.ui,
            env=os.environ,
            dry=self.ui['dry_run'] or False,
            poe_active=os.environ.get('POE_ACTIVE'),
            multistage=multistage,
            cwd=Path.cwd(),
        )

    def execute(self, hook_name: str) -> None:
        """Execute the `poethepoet.task.base.PoeTask` of the given name."""
        self.ui.parse_args([hook_name])

        task = self.tasks[hook_name]

        if task.has_deps():
            self.run_task_graph(task)
        else:
            self.run_task(task)

    @classmethod
    def load_file(cls, path: Path, default_paths: list[Path]) -> HooksEngine:
        """Instantiate a `poethepoet.config.PoeConfig` object, then populate it with the given file."""
        cfg = PoeConfig(config_name=tuple({str(p.name) for p in default_paths}))

        cfg.load(path)
        logger.debug('parsed hooks from %s: %s', path, list(cfg.task_names))

        ui = PoeUi(
            output=sys.stdout,
            program_name=f'{sys.argv[0]} hook'
            if sys.argv[0].endswith('config-ninja')
            else f'{sys.executable} {sys.argv[0]} hook',
        )

        tasks: dict[str, PoeTask] = {}
        factory = TaskSpecFactory(cfg)

        for task_spec in factory.load_all():
            task_spec.validate(cfg, factory)
            tasks[task_spec.name] = task_spec.create_task(
                invocation=(task_spec.name,),
                ctx=TaskContext(config=cfg, cwd=str(task_spec.source.cwd), specs=factory, ui=ui),
            )

        return cls(cfg, ui, tasks)

    def run_task(self, task: PoeTask, ctx: poethepoet.context.RunContext | None = None) -> None:
        """Reimplement the `poethepoet.app.PoeThePoet.run_task()` method (`reference`_).

        .. _reference: https://github.com/nat-n/poethepoet/blob/3c9fd8bcffde8a95c5cd9513923d0f43c1507385/poethepoet/app.py#L169-L181
        """
        try:
            task.run(context=ctx or self.get_run_context())
        except poethepoet.exceptions.ExecutionError as error:
            logger.exception('error running task %s: %s', task.name, error)
            raise

    def run_task_graph(self, task: PoeTask) -> None:
        """Reimplement the `poethepoet.app.PoeThePoet.run_task_graph()` method (`reference`_).

        .. _reference: https://github.com/nat-n/poethepoet/blob/3c9fd8bcffde8a95c5cd9513923d0f43c1507385/poethepoet/app.py#L183-L208
        """
        ctx = self.get_run_context(multistage=True)
        graph = TaskExecutionGraph(task, ctx)
        plan = graph.get_execution_plan()

        for stage in plan:
            for stage_task in stage:
                if stage_task == task:
                    # The final sink task gets special treatment
                    self.run_task(stage_task, ctx)
                    return

                task_result = stage_task.run(context=ctx)
                if task_result:
                    raise poethepoet.exceptions.ExecutionError(
                        f'Task graph aborted after failed task {stage_task.name!r}'
                    )


logger.debug('successfully imported %s', __name__)
