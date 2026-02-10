"""Base contract for all Report implementations.

Defines the two-phase lifecycle:
1. init_report() - Configure and set up the report
2. run_report(sender) - Execute the report

All reports must inherit from BaseReport and implement both methods.
"""
from abc import ABC, abstractmethod
from typing import Any


class BaseReport(ABC):
    """Abstract base class defining the contract for all reports.

    Reports follow a two-phase lifecycle:
    1. __init__() - Basic initialization, set self.report to None
    2. init_report() - Configure the report (create DQReport, set queries, etc.)
    3. run_report(sender) - Execute the report

    The runner will call init_report() once after instantiation, then call
    run_report(sender) to execute.
    """

    def __init__(self):
        """Initialize the report instance.

        Subclasses should set self.report to None or their specific report type.
        Keep this lightweight - heavy initialization should happen in init_report().
        """
        self.report: Any = None

    @abstractmethod
    def init_report(self) -> None:
        """Initialize and configure the report.

        This method should:
        - Create the report instance (DQReport, KladRapport, etc.)
        - Define queries (result_query, cypher_query, aql_query, etc.)
        - Set all configuration parameters
        - Assign to self.report

        Must be called before run_report().
        Must not perform any I/O, DB calls, or side effects at import time.
        """
        pass

    @abstractmethod
    def run_report(self, sender) -> None:
        """Execute the report.

        This method should call self.report.run_report(sender=sender) or equivalent.

        Args:
            sender: MailSender instance or identifier for report execution context.

        Raises:
            RuntimeError: If init_report() was not called first.
        """
        pass

    def validate_initialized(self) -> None:
        """Validate that init_report() was called before run_report().

        Subclasses can call this in run_report() to enforce the contract.
        """
        if self.report is None:
            raise RuntimeError(
                f"{self.__class__.__name__}.init_report() must be called before run_report()"
            )
