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
      max_memory_restart: "1G",
      // Varsayılan (pm2 start ecosystem.config.js)
      env: {
        PORT: 8000,
        ENVIRONMENT: "release",
        NODE_ENV: "production",
        PYTHONIOENCODING: "utf-8",
        PYTHONUTF8: "1",
      },
      // Test Modu (pm2 start ecosystem.config.js --env test)
      env_test: {
        PORT: 8000,
        ENVIRONMENT: "test",
        NODE_ENV: "development",
        PYTHONIOENCODING: "utf-8",
        PYTHONUTF8: "1",
      },
      // Log Ayarları
      error_file: "./logs/api-error.log",
      out_file: "./logs/api-out.log",
      time: true,
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
        PYTHONUTF8: "1",
      },
      // Test
      env_test: {
        ENVIRONMENT: "test",
        PYTHONIOENCODING: "utf-8",
        PYTHONUTF8: "1",
      },
      // Log Ayarları
      error_file: "./logs/mt5-error.log",
      out_file: "./logs/mt5-out.log",
      time: true,
    },

    // ─────────────────────────────────────────────────────────────────────────
    // BAKIM MODU — Normal sistemden tamamen bağımsız.
    // Kullanım:
    //   pm2 start ecosystem.config.js --only COBO-MAINTENANCE
    //
    // Parametreli başlatma (önerilen):
    //   pm2 start maintenance_server.py \
    //     --name COBO-MAINTENANCE \
    //     --interpreter ./sanallik/Scripts/python.exe \
    //     -- --time 17:00 --day 1
    //
    // Açıklamalar:
    //   --time HH:MM  → Türkiye saatinde tahmini açılış saati
    //   --day  N      → Kaç gün sonra açılacağı (0 = bugün, 1 = yarın)
    //
    // Önemli: Bu process çalışırken COBO-API ve COBO-MT5 ÇALIŞMAMALIDIR.
    //         Bakım modunda backend sıfır, sadece HTML serve edilir.
    // ─────────────────────────────────────────────────────────────────────────
    {
      name: "COBO-MAINTENANCE",
      script: "maintenance_server.py",
      interpreter: "./sanallik/Scripts/python.exe",
      interpreter_args: "-X utf8",
      instances: 1,
      autorestart: true,
      watch: false,
      args: "--time 17:00 --day 1",   // Varsayılan: 1 gün sonra saat 17:00
      env: {
        PORT: 8000,
        PYTHONIOENCODING: "utf-8",
        PYTHONUTF8: "1",
      },
      error_file: "./logs/maintenance-error.log",
      out_file:   "./logs/maintenance-out.log",
      time: true,
    },
  ],
};
