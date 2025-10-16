#!/bin/bash

# ============================================================================
# Comprehensive Test Runner for Multi-Agent System
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored message
print_msg() {
    color=$1
    message=$2
    echo -e "${color}${message}${NC}"
}

# Print section header
print_header() {
    echo ""
    echo "========================================="
    print_msg "$BLUE" "$1"
    echo "========================================="
    echo ""
}

# Check if virtual environment is activated
if [[ -z "${VIRTUAL_ENV}" ]]; then
    print_msg "$YELLOW" "⚠️  Virtual environment not activated. Activating..."
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
    else
        print_msg "$RED" "❌ Virtual environment not found. Run: uv venv"
        exit 1
    fi
fi

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    print_msg "$RED" "❌ pytest not found. Installing test dependencies..."
    uv pip install -e ".[test]"
fi

# ============================================================================
# TEST EXECUTION
# ============================================================================

print_header "🧪 STARTING TEST SUITE"

# Clean up previous test artifacts
print_msg "$YELLOW" "🧹 Cleaning up previous test artifacts..."
rm -rf .pytest_cache htmlcov .coverage coverage.xml

# ============================================================================
# PHASE 1: QUICK UNIT TESTS
# ============================================================================

print_header "📦 Phase 1: Running Unit Tests (Fast)"

pytest -m unit -v --tb=short || {
    print_msg "$RED" "❌ Unit tests failed"
    UNIT_FAILED=1
}

if [ -z "$UNIT_FAILED" ]; then
    print_msg "$GREEN" "✅ Unit tests passed"
fi

# ============================================================================
# PHASE 2: INTEGRATION TESTS
# ============================================================================

print_header "🔗 Phase 2: Running Integration Tests"

pytest -m integration -v --tb=short || {
    print_msg "$RED" "❌ Integration tests failed"
    INTEGRATION_FAILED=1
}

if [ -z "$INTEGRATION_FAILED" ]; then
    print_msg "$GREEN" "✅ Integration tests passed"
fi

# ============================================================================
# PHASE 3: API TESTS
# ============================================================================

print_header "🌐 Phase 3: Running API Tests"

pytest -m api -v --tb=short || {
    print_msg "$RED" "❌ API tests failed"
    API_FAILED=1
}

if [ -z "$API_FAILED" ]; then
    print_msg "$GREEN" "✅ API tests passed"
fi

# ============================================================================
# PHASE 4: WEBSOCKET TESTS
# ============================================================================

print_header "🔌 Phase 4: Running WebSocket Tests"

pytest -m websocket -v --tb=short || {
    print_msg "$RED" "❌ WebSocket tests failed"
    WS_FAILED=1
}

if [ -z "$WS_FAILED" ]; then
    print_msg "$GREEN" "✅ WebSocket tests passed"
fi

# ============================================================================
# PHASE 5: AGENT TESTS
# ============================================================================

print_header "🤖 Phase 5: Running Agent Tests"

pytest -m agents -v --tb=short || {
    print_msg "$RED" "❌ Agent tests failed"
    AGENT_FAILED=1
}

if [ -z "$AGENT_FAILED" ]; then
    print_msg "$GREEN" "✅ Agent tests passed"
fi

# ============================================================================
# PHASE 6: ALL TESTS WITH COVERAGE
# ============================================================================

print_header "📊 Phase 6: Running ALL Tests with Coverage"

pytest \
    --cov=app \
    --cov-report=term-missing:skip-covered \
    --cov-report=html:htmlcov \
    --cov-report=xml:coverage.xml \
    --cov-fail-under=70 \
    -v \
    --tb=short || {
    print_msg "$RED" "❌ Coverage tests failed or coverage below 70%"
    COVERAGE_FAILED=1
}

if [ -z "$COVERAGE_FAILED" ]; then
    print_msg "$GREEN" "✅ Coverage requirements met"
fi

# ============================================================================
# PHASE 7: SLOW/E2E TESTS (Optional)
# ============================================================================

if [ "$1" == "--full" ]; then
    print_header "🐌 Phase 7: Running Slow/E2E Tests"
    
    pytest -m slow -v --tb=short || {
        print_msg "$RED" "❌ Slow tests failed"
        SLOW_FAILED=1
    }
    
    if [ -z "$SLOW_FAILED" ]; then
        print_msg "$GREEN" "✅ Slow tests passed"
    fi
fi

# ============================================================================
# FINAL SUMMARY
# ============================================================================

print_header "📋 TEST SUMMARY"

echo "Test Results:"
echo ""

[ -z "$UNIT_FAILED" ] && print_msg "$GREEN" "✅ Unit Tests: PASSED" || print_msg "$RED" "❌ Unit Tests: FAILED"
[ -z "$INTEGRATION_FAILED" ] && print_msg "$GREEN" "✅ Integration Tests: PASSED" || print_msg "$RED" "❌ Integration Tests: FAILED"
[ -z "$API_FAILED" ] && print_msg "$GREEN" "✅ API Tests: PASSED" || print_msg "$RED" "❌ API Tests: FAILED"
[ -z "$WS_FAILED" ] && print_msg "$GREEN" "✅ WebSocket Tests: PASSED" || print_msg "$RED" "❌ WebSocket Tests: FAILED"
[ -z "$AGENT_FAILED" ] && print_msg "$GREEN" "✅ Agent Tests: PASSED" || print_msg "$RED" "❌ Agent Tests: FAILED"
[ -z "$COVERAGE_FAILED" ] && print_msg "$GREEN" "✅ Coverage: PASSED (≥70%)" || print_msg "$RED" "❌ Coverage: FAILED (<70%)"

if [ "$1" == "--full" ]; then
    [ -z "$SLOW_FAILED" ] && print_msg "$GREEN" "✅ Slow/E2E Tests: PASSED" || print_msg "$RED" "❌ Slow/E2E Tests: FAILED"
fi

echo ""
print_msg "$BLUE" "📊 Coverage Report: htmlcov/index.html"
print_msg "$BLUE" "📄 Coverage XML: coverage.xml"
echo ""

# ============================================================================
# EXIT CODE
# ============================================================================

if [ -n "$UNIT_FAILED" ] || [ -n "$INTEGRATION_FAILED" ] || [ -n "$API_FAILED" ] || [ -n "$WS_FAILED" ] || [ -n "$AGENT_FAILED" ] || [ -n "$COVERAGE_FAILED" ]; then
    print_header "❌ TESTS FAILED"
    exit 1
else
    print_header "✅ ALL TESTS PASSED"
    exit 0
fi
