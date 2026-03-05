// app.js - Главный файл в корне проекта

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

console.log('='.repeat(60));
console.log('🍰 ЗАПУСК БОТА И МИНИ-ПРИЛОЖЕНИЯ');
console.log('='.repeat(60));

// Путь к мини-приложению
const miniAppPath = path.join(__dirname, 'telegram-cake-miniapp', 'app.js');

if (!fs.existsSync(miniAppPath)) {
    console.error(`❌ Файл не найден: ${miniAppPath}`);
    console.error('📁 Текущая директория:', __dirname);
    console.error('📁 Содержимое:');
    fs.readdirSync(__dirname).forEach(file => {
        console.error(`   - ${file}`);
    });
    process.exit(1);
}

console.log(`✅ Найден файл мини-приложения: ${miniAppPath}`);

// Запускаем мини-приложение
const miniApp = spawn('node', [miniAppPath], {
    stdio: 'inherit',
    shell: true,
    env: { ...process.env, FORCE_COLOR: 'true' }
});

miniApp.on('error', (err) => {
    console.error(`❌ Ошибка запуска мини-приложения: ${err.message}`);
});

miniApp.on('close', (code) => {
    console.log(`⚠️ Мини-приложение завершилось с кодом ${code}`);
});

// Обработка завершения
process.on('SIGINT', () => {
    console.log('\n🛑 Завершение...');
    miniApp.kill();
    process.exit();
});

process.on('SIGTERM', () => {
    console.log('\n🛑 Завершение...');
    miniApp.kill();
    process.exit();
});

console.log('✅ Главный процесс запущен, ожидание...');
