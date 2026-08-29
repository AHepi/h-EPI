"""Typed failures and stable command-line exit codes."""


class CREIBError(Exception):
    exit_code = 1


class RecordError(CREIBError):
    exit_code = 2


class AuthorityMismatch(CREIBError):
    exit_code = 3


class AnchorMismatch(CREIBError):
    exit_code = 4


class PolicyViolation(CREIBError):
    exit_code = 5


class FormalReplayMismatch(CREIBError):
    exit_code = 6
