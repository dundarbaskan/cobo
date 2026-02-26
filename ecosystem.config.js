module.exports = {
    apps: [
        {
            name: "COBO-API",
            script: "main.py",
            interpreter: "./sanallik/Scripts/python.exe",
            interpreter_args: "-X utf8",
            instances: 1,
            autorestart: true,
            watch: false,
            max_memory_restart: '1G',
            // Varsayılan "pm2 start ecosystem.config.js" -> Canlı (Release)
            env: {
                PORT: 8000,
                ENVIRONMENT: "release",
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
            error_file: "./logs/api-error.log",
            out_file: "./logs/api-out.log",
            time: true // Loglara tarih ekler
        },
        {
            name: "COBO-MT5",
            script: "mt5_worker.py",
            interpreter: "./sanallik/Scripts/python.exe",
            interpreter_args: "-X utf8",
            instances: 1,
            autorestart: true,
            watch: false,
            // Varsayılan
            env: {
                ENVIRONMENT: "release",
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
            error_file: "./logs/mt5-error.log",
            out_file: "./logs/mt5-out.log",
            time: true
        }
    ]
};
