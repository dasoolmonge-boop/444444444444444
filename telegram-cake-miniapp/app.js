// Сервер для раздачи статических файлов и прокси к боту
const http = require('http');
const fs = require('fs');
const path = require('path');
const https = require('https');

const PORT = process.env.PORT || 3000;
const BOT_TOKEN = "8714739961:AAG9l-7-G7duRNKuNtarP7rTchfvZQFCMxo";
const ADMIN_ID = 1066867845;

const mimeTypes = {
  '.html': 'text/html',
  '.css': 'text/css',
  '.js': 'text/javascript',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon'
};

const server = http.createServer((req, res) => {
  console.log(`Запрос: ${req.method} ${req.url}`);

  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }

  // API endpoint для отправки заказа админу
  if (req.url === '/api/send-order' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const orderData = JSON.parse(body);
        sendOrderToAdmin(orderData, res);
      } catch (error) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Invalid JSON' }));
      }
    });
    return;
  }

  // API endpoint для получения тортов
  if (req.url === '/api/cakes' && req.method === 'GET') {
    // Здесь должен быть запрос к вашей БД
    // Пока возвращаем тестовые данные
    const cakes = [
      {
        id: 1,
        name: 'Медовик',
        price: 2500,
        weight: 1.5,
        description: 'Классический медовый торт с нежным кремом',
        photo: 'https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=400'
      },
      {
        id: 2,
        name: 'Наполеон',
        price: 2800,
        weight: 1.8,
        description: 'Хрустящие коржи с заварным кремом',
        photo: 'https://images.unsplash.com/photo-1464305795233-6e7c1d10f1d8?w=400'
      },
      {
        id: 3,
        name: 'Красный бархат',
        price: 3200,
        weight: 2.0,
        description: 'Красные коржи с сливочно-сырным кремом',
        photo: 'https://images.unsplash.com/photo-1586788224331-947f68671cf1?w=400'
      },
      {
        id: 4,
        name: 'Птичье молоко',
        price: 2700,
        weight: 1.6,
        description: 'Нежное суфле на тонких коржах',
        photo: 'https://images.unsplash.com/photo-1519915025057-0b45c91fde85?w=400'
      },
      {
        id: 5,
        name: 'Прага',
        price: 2900,
        weight: 1.7,
        description: 'Шоколадный торт с пралине',
        photo: 'https://images.unsplash.com/photo-1588195538326-c5b1e9f80a6a?w=400'
      }
    ];

    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(cakes));
    return;
  }

  // Раздача статических файлов
  let url = req.url;
  if (url === '/' || url === '') {
    url = '/index.html';
  }

  const filePath = path.join(__dirname, 'public', url);
  const extname = path.extname(filePath);
  const contentType = mimeTypes[extname] || 'text/plain';

  fs.readFile(filePath, (error, content) => {
    if (error) {
      if (error.code === 'ENOENT') {
        res.writeHead(404);
        res.end('Файл не найден');
      } else {
        res.writeHead(500);
        res.end(`Ошибка сервера: ${error.code}`);
      }
    } else {
      res.writeHead(200, { 'Content-Type': contentType });
      res.end(content, 'utf-8');
    }
  });
});

function sendOrderToAdmin(orderData, res) {
  const { name, phone, address, deliveryDate, deliveryTime, wish, cart, totalPrice, userId, username } = orderData;

  const cakesList = cart.map(item =>
    `🍰 ${item.name} - ${item.price} ₽ (${item.weight} кг)`
  ).join('\n');

  const message =
    `📩 **НОВЫЙ ЗАКАЗ ИЗ MINI APP**\n\n` +
    `🍰 **Торты:**\n${cakesList}\n` +
    `💰 **Итого:** ${totalPrice} ₽\n\n` +
    `👤 **Имя:** ${name}\n` +
    `🆔 **Username:** ${username ? '@' + username : 'нет'}\n` +
    `📱 **Телефон:** ${phone}\n` +
    `📍 **Адрес:** ${address}\n` +
    `📅 **Дата доставки:** ${deliveryDate}\n` +
    `⏰ **Время доставки:** ${deliveryTime}\n` +
    `📝 **Пожелания:** ${wish || 'Без пожеланий'}\n` +
    `🆔 **User ID:** ${userId}\n` +
    `📅 **Дата заказа:** ${new Date().toLocaleString('ru-RU')}`;

  const postData = JSON.stringify({
    chat_id: ADMIN_ID,
    text: message,
    parse_mode: 'Markdown'
  });

  const options = {
    hostname: 'api.telegram.org',
    path: `/bot${BOT_TOKEN}/sendMessage`,
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(postData)
    }
  };

  const req = https.request(options, (apiRes) => {
    let data = '';
    apiRes.on('data', chunk => data += chunk);
    apiRes.on('end', () => {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: true, message: 'Заказ отправлен администратору' }));
    });
  });

  req.on('error', (error) => {
    console.error('Ошибка отправки:', error);
    res.writeHead(500, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Ошибка отправки заказа' }));
  });

  req.write(postData);
  req.end();
}

server.listen(PORT, '0.0.0.0', () => {
  console.log(`✅ Mini App сервер запущен на порту ${PORT}`);
});