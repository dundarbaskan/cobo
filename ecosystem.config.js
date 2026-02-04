module.exports = {
    apps: [
        {
            name: "COBO-API",
            script: "main.py",
            interpreter: "./venv/Scripts/python.exe",
            interpreter_args: "-X utf8",
            instances: 1,
            autorestart: true,
            watch: false,
            max_memory_restart: '1G',
            env: {
                PORT: 8000,
                NODE_ENV: "production",
                PYTHONIOENCODING: "utf-8",
                PYTHONUTF8: "1"
            },
            // Log Ayarları
            error_file: "./logs/api-error.log",
            out_file: "./logs/api-out.log",
            time: true // Loglara tarih ekler
        },
        {
            name: "COBO-MT5-WORKER",
            script: "mt5_worker.py",
            interpreter: "./venv/Scripts/python.exe",
            interpreter_args: "-X utf8",
            instances: 1,
            autorestart: true,
            watch: false,
            env: {
                PYTHONIOENCODING: "utf-8",
                PYTHONUTF8: "1"
            },
            // Log Ayarları
            error_file: "./logs/mt5-error.log",
            out_file: "./logs/mt5-out.log",
            time: true
        },

    ]
};
