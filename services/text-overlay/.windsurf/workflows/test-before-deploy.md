---
description: Run comprehensive tests before deployment
---

# Test Before Deploy Workflow

This workflow ensures your Flask Video Enhancement API is thoroughly tested before deployment.

## Prerequisites

1. Ensure you have Python 3.8+ installed
2. Create a `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```
3. Have Docker installed (optional, for Docker deployment)

## Testing Steps

### 1. Quick System Check
First, run a quick system check to ensure basic components are working:

```bash
python quick_test.py
```

This will verify:
- All required Python packages are installed
- Flask app can be imported
- Video processing modules are available
- File structure is correct
- Environment variables are configured

### 2. Install Testing Dependencies
// turbo
```bash
pip install -r requirements.txt
```

This installs all dependencies including testing frameworks (pytest, coverage, etc.).

### 3. Run Unit Tests
// turbo
```bash
python -m pytest tests/ -m unit -v
```

This runs isolated unit tests for individual components.

### 4. Run API Tests
// turbo
```bash
python -m pytest tests/test_flask_api.py -v
```

This tests all Flask API endpoints with mocked dependencies.

### 5. Run Integration Tests
```bash
python -m pytest tests/ -m integration -v
```

This tests how different components work together.

### 6. Run Full Test Suite with Coverage
```bash
python run_tests.py --coverage
```

This runs all tests and generates coverage reports.

### 7. Check Deployment Readiness
```bash
python deploy_ready.py
```

This comprehensive script:
- Verifies all dependencies are installed
- Checks environment configuration
- Creates necessary directories
- Runs the test suite
- Validates Docker configuration
- Generates a deployment report

## Test Results

After running tests, you'll have:

- **test_report.json** - Machine-readable test results
- **test_report.txt** - Human-readable test summary
- **htmlcov/index.html** - Coverage report (if run with coverage)
- **deployment_report.md** - Deployment readiness assessment

## Deployment Decision

✅ **DEPLOY** if:
- All unit tests pass
- All API tests pass  
- Integration tests pass
- Coverage is acceptable (>80%)
- No critical security issues

❌ **DO NOT DEPLOY** if:
- Any essential tests fail
- Coverage is too low (<60%)
- Security vulnerabilities detected
- Missing required dependencies

## Quick Deploy Commands

### Local Development
```bash
python start_flask_local.py
```

### Docker Deployment
// turbo
```bash
docker-compose up -d
```

### Test Deployment
```bash
curl http://localhost:5000/health
```

## Continuous Integration

For automated testing, add this to your CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
name: Test and Deploy
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python run_tests.py --all
      - name: Check deployment readiness
        run: python deploy_ready.py
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Run `pip install -r requirements.txt`
2. **Missing OpenAI Key**: Create `.env` file with your API key
3. **Docker Issues**: Ensure Docker is running and docker-compose.yml is valid
4. **Test Failures**: Check test logs and fix issues before deploying

### Test Markers

Use pytest markers to run specific test categories:

```bash
# Run only fast tests
python -m pytest -m "not slow"

# Run only API tests
python -m pytest -m api

# Run only unit tests
python -m pytest -m unit

# Run integration tests
python -m pytest -m integration
```

## Best Practices

1. **Always run tests before deployment**
2. **Fix failing tests before proceeding**
3. **Maintain high test coverage (>80%)**
4. **Review security scan results**
5. **Test in environment similar to production**
6. **Keep test data separate from production data**
7. **Monitor test execution time**
8. **Update tests when adding new features**

## Success Criteria

Your deployment is ready when:

- ✅ All core functionality tests pass
- ✅ API endpoints respond correctly
- ✅ Video processing pipeline works
- ✅ Database logging functions properly
- ✅ Docker containers build successfully
- ✅ No critical security vulnerabilities
- ✅ Performance meets requirements
- ✅ All required files are present

Run the full test suite with `python deploy_ready.py` for a complete readiness assessment.
