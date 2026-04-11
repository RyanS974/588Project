"""Constants for the test_classifier package."""

# Patterns for feature extraction
MOCK_PATTERNS = [r"mock", r"patch", r"MagicMock", r"Mock"]
ASSERT_PATTERNS = [r"assert", r"assertTrue", r"assertFalse", r"assertEquals", r"assertEqual", r"assertThat"]
EXTERNAL_DEP_PATTERNS = [
    r"requests\.", r"http\.", r"urllib", r"database", r"db\.", r"open\(", r"socket", 
    r"connect", r"FTP", r"SMTP", r"connect_to", r"fetch_from"
]
SETUP_PATTERNS = [r"setUp", r"setup_method", r"setup_class", r"@Before", r"@BeforeClass", r"def setUp"]
TEARDOWN_PATTERNS = [r"tearDown", r"teardown_method", r"teardown_class", r"@After", r"@AfterClass", r"def tearDown"]

# Patterns for quality analysis
FLAKY_PATTERNS = [r"sleep\(", r"time\.sleep", r"random", r"rand", r"wait\("]
COMPLEX_TEST_LINE_THRESHOLD = 50  # A test over 50 lines is considered 'complex'

# Test type classification thresholds and indicators
UNIT_INDICATORS = {"mock", "patch", "stub"}
INTEGRATION_INDICATORS = {"requests", "http", "database", "socket"}
REGRESSION_INDICATORS = {"fix", "bug", "issue", "regression"}