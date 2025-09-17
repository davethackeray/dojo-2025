<?php
// InvestingDojo Configuration File

// Database Configuration
define('DB_HOST', 'localhost');
define('DB_NAME', 'u219832816_investing_dojo');
define('DB_USER', 'u219832816_davethackeray');
define('DB_PASS', 'ToTheM00n!');
define('DB_CHARSET', 'utf8mb4');

// Site Configuration
define('SITE_URL', 'https://InvestingDojo.co');
define('SITE_NAME', 'Investing Dojo');
define('DEBUG_MODE', false); // Set to true for development

// Security
define('SECURE_KEY', 'your-unique-secure-key-here');

// Error Reporting (for development only)
if (DEBUG_MODE) {
    error_reporting(E_ALL);
    ini_set('display_errors', 1);
} else {
    error_reporting(0);
    ini_set('display_errors', 0);
}

/**
 * Get database connection with proper error handling
 */
function getDBConnection() {
    static $pdo = null;
    
    if ($pdo === null) {
        try {
            $dsn = "mysql:host=" . DB_HOST . ";dbname=" . DB_NAME . ";charset=" . DB_CHARSET;
            $options = [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                PDO::ATTR_EMULATE_PREPARES => false,
                PDO::MYSQL_ATTR_INIT_COMMAND => "SET NAMES " . DB_CHARSET . " COLLATE " . DB_CHARSET . "_unicode_ci"
            ];
            $pdo = new PDO($dsn, DB_USER, DB_PASS, $options);
        } catch (PDOException $e) {
            if (DEBUG_MODE) {
                die("Database connection failed: " . $e->getMessage());
            } else {
                die("Website temporarily unavailable. Please try again later.");
            }
        }
    }
    
    return $pdo;
}

/**
 * Safe output function to prevent XSS
 */
function safe_output($string) {
    return htmlspecialchars($string, ENT_QUOTES, 'UTF-8');
}

/**
 * Generate CSRF token
 */
function generate_csrf_token() {
    if (!isset($_SESSION['csrf_token'])) {
        $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
    }
    return $_SESSION['csrf_token'];
}

// Start session securely
if (session_status() === PHP_SESSION_NONE) {
    session_start([
        'cookie_httponly' => true,
        'cookie_secure' => isset($_SERVER['HTTPS']),
        'cookie_samesite' => 'Strict'
    ]);
}
?>
