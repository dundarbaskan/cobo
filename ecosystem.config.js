module.exports = {
    apps: [
        {
            name: "COBO-API-TEST",
            script: "main.py",
            interpreter: "./venv/Scripts/python.exe",
            interpreter_args: "-X utf8",
            instances: 1,
            autorestart: true,
            watch: false,
            max_memory_restart: '1G',
            // Varsayılan "pm2 start ecosystem.config.js" -> Test Canlı (Release)
            env: {
                PORT: 8001,
                ENVIRONMENT: "test",
                NODE_ENV: "production",
                PYTHONIOENCODING: "utf-8",
                PYTHONUTF8: "1"
            },
            // "pm2 start ecosystem.config.js --env test" -> Gizli Test Modu!
            env_test: {
                PORT: 8001,
                ENVIRONMENT: "test",
                NODE_ENV: "development",
                PYTHONIOENCODING: "utf-8",
                PYTHONUTF8: "1"
            },
            // Log Ayarları
            error_file: "./logs/api-test-error.log",
            out_file: "./logs/api-test-out.log",
            time: true // Loglara tarih ekler
        },
        {
            name: "COBO-MT5-TEST",
            script: "mt5_worker.py",
            interpreter: "./venv/Scripts/python.exe",
            interpreter_args: "-X utf8",
            instances: 1,
            autorestart: true,
            watch: false,
            // Varsayılan
            env: {
                ENVIRONMENT: "test",
                PYTHONIOENCODING: "utf-8",
                PYTHONUTF8: "1"
            },
            // Test
            env_test: {
                ENVIRONMENT: "test",
                PYTHONIOENCODING: "utf-8",
                PYTHONUTF8: "1"
            },
            // Log Ayarları
            error_file: "./logs/mt5-test-error.log",
            out_file: "./logs/mt5-test-out.log",
            time: true
        }
    ]
};
