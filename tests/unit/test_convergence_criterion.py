"""Tests for convergence_function."""

from genai_opt.optimizer_engine.convergence_criterion.convergence_criterion import (
    convergence_function,
)
from genai_opt.optimizer_engine.population import Population


def test_convergence_false_before_limit():
    """convergence_function(10) called at iteration=5 should return False."""
    is_converged = convergence_function(10)
    result = is_converged(Population(), 5)
    assert result is False


def test_convergence_true_at_limit():
    """convergence_function(10) called at iteration=10 should return True."""
    is_converged = convergence_function(10)
    result = is_converged(Population(), 10)
    assert result is True
