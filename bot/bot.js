const mineflayer = require('mineflayer');
const { pathfinder, Movements, goals } = require('mineflayer-pathfinder');
const fs   = require('fs');
const path = require('path');
const http = require('http');

// ─── Config ───────────────────────────────────────────────────────────────────
const SERVER_HOST  = 'private-java-smp.aternos.me';
const SERVER_PORT  = 40115;
const STATUS_FILE  = path.join(__dirname, 'status.json');
const SELF_PING_URL = process.env.SELF_URL || null; // set SELF_URL env var for 24/7 keep-alive

// ─── Username Pool ────────────────────────────────────────────────────────────
const ADJECTIVES = [
  'Shadow','Blazing','Crystal','Iron','Diamond','Golden','Cobalt','Emerald',
  'Mystic','Nether','Ender','Storm','Silent','Swift','Bold','Mighty','Frost',
  'Lava','Azure','Crimson','Obsidian','Coral','Lunar','Solar','Astral',
  'Thunder','Ghast','Creeper','Wither','Phantom','Zombie','Piglin','Blaze',
  'Dark','Light','Wild','Brave','Fierce','Epic','Super','Ultra','Mega','Pro'
];
const NOUNS = [
  'Knight','Warrior','Dragon','Miner','Builder','Crafter','Archer','Wizard',
  'Hero','Legend','Titan','Phantom','Ghost','Ranger','Scout','Sentinel',
  'Slayer','Hunter','Guard','Keeper','Wanderer','Pioneer','Raider','Seeker',
  'Overlord','Champion','Pilgrim','Stalker','Warden','Protector','Wolf','Fox',
  'Bear','Eagle','Tiger','Lion','Snake','Hawk','Raven','Panther'
];
const CHAT_MESSAGES = [
  'Mining away!', 'Beautiful server!', 'Anyone online?', 'GG everyone!',
  'Love this SMP!', 'Building something epic', 'Exploring the world!',
  'Diamonds found!', 'This place is amazing', 'Shoutout to SkipScaped!',
  'Greetings fellow miners!', 'What are you all building?', 'Nice spawn!',
  'This server rocks!', 'Happy mining!', 'Adventuring around!',
  'Found a stronghold!', 'Making progress on my base', 'The nether is spicy!',
  'Anyone need help?', 'Great community here!', 'Love the builds!'
];

// ─── State ────────────────────────────────────────────────────────────────────
let usedUsernames   = new Set();
let usernameIndex   = 0;
let reconnectDelay  = 3000;
const MAX_DELAY     = 60000;
let bot             = null;
let messagesSent    = 0;
let chatInterval    = null;
let moveInterval    = null;
let isRunning       = true;

// ─── Username generation ──────────────────────────────────────────────────────
function generateUsername(index) {
  const adj  = ADJECTIVES[index % ADJECTIVES.length];
  const noun = NOUNS[Math.floor(index / ADJECTIVES.length) % NOUNS.length];
  const num  = (index % 999) + 1;
  const templates = [
    `${adj}${noun}`,
    `${adj}${noun}${num}`,
    `${noun}${num}`,
    `${adj}${num}`,
    `${adj}_${noun}`,
    `x${adj}${noun}`,
    `${noun}${adj}`,
    `${adj}${noun}x`
  ];
  return templates[index % templates.length].substring(0, 16);
}

function nextUsername() {
  let name, tries = 0;
  do {
    name = generateUsername(usernameIndex++);
    tries++;
  } while (usedUsernames.has(name) && tries < 300);
  usedUsernames.add(name);
  if (usernameIndex > 8000) { usernameIndex = 0; usedUsernames.clear(); }
  return name;
}

// ─── Status file ──────────────────────────────────────────────────────────────
function writeStatus(data) {
  try {
    fs.writeFileSync(STATUS_FILE, JSON.stringify({
      ...data, updated: new Date().toISOString()
    }, null, 2));
  } catch (_) {}
}

writeStatus({ connected: false, username: null, status: 'starting', messages_sent: 0, position: null });

// ─── Helpers ──────────────────────────────────────────────────────────────────
function getPos() {
  try {
    const p = bot && bot.entity && bot.entity.position;
    return p ? { x: Math.round(p.x), y: Math.round(p.y), z: Math.round(p.z) } : null;
  } catch (_) { return null; }
}

function safechat(msg) {
  if (!bot) return;
  try { bot.chat(msg); messagesSent++; } catch (_) {}
}

function cleanup() {
  if (chatInterval) { clearInterval(chatInterval); chatInterval = null; }
  if (moveInterval)  { clearInterval(moveInterval);  moveInterval  = null; }
  writeStatus({ connected: false, username: bot && bot.username,
    status: 'disconnected', messages_sent: messagesSent, position: null });
  bot = null;
}

function scheduleReconnect(lastUser, immediate = false) {
  const delay = immediate ? 1000 : reconnectDelay;
  console.log(`[BOT] Reconnecting in ${delay / 1000}s...`);
  writeStatus({ connected: false, username: lastUser,
    status: `reconnecting in ${Math.round(delay / 1000)}s`,
    messages_sent: messagesSent, position: null });
  setTimeout(() => { if (isRunning) createBot(); }, delay);
  if (!immediate) reconnectDelay = Math.min(reconnectDelay * 1.5, MAX_DELAY);
}

// ─── Movement ────────────────────────────────────────────────────────────────
function startMovement() {
  if (!bot || moveInterval) return;
  try {
    const mcData    = require('minecraft-data')(bot.version);
    const movements = new Movements(bot);
    movements.allowSprinting = true;
    movements.canDig         = false;
    bot.pathfinder.setMovements(movements);
  } catch (e) {
    console.log('[BOT] Pathfinder setup error:', e.message);
    return;
  }

  moveInterval = setInterval(() => {
    if (!bot || !bot.entity) return;
    try {
      const pos = bot.entity.position;
      const dx  = (Math.random() - 0.5) * 24;
      const dz  = (Math.random() - 0.5) * 24;
      bot.pathfinder.setGoal(new goals.GoalXZ(
        Math.floor(pos.x + dx),
        Math.floor(pos.z + dz)
      ));
    } catch (_) {}
  }, 8000 + Math.random() * 6000);
}

// ─── Chat loop ────────────────────────────────────────────────────────────────
function startChatting() {
  if (!bot || chatInterval) return;
  chatInterval = setInterval(() => {
    if (!bot) return;
    safechat(CHAT_MESSAGES[Math.floor(Math.random() * CHAT_MESSAGES.length)]);
  }, 50000 + Math.random() * 40000);
}

// ─── Create bot ───────────────────────────────────────────────────────────────
function createBot() {
  if (!isRunning) return;
  const username = nextUsername();
  console.log(`[BOT] Connecting as ${username}`);
  writeStatus({ connected: false, username, status: 'connecting',
    messages_sent: messagesSent, position: null });

  // Use version: false so mineflayer auto-detects from server handshake
  // This avoids hardcoded version mismatch entirely
  const opts = {
    host:                   SERVER_HOST,
    port:                   SERVER_PORT,
    username,
    auth:                   'offline',
    version:                false,          // auto-detect server version
    hideErrors:             false,
    checkTimeoutInterval:   30000,
    connectTimeout:         25000,
    closeTimeout:           240
  };

  try {
    bot = mineflayer.createBot(opts);
  } catch (err) {
    console.error('[BOT] createBot error:', err.message);
    scheduleReconnect(username);
    return;
  }

  bot.loadPlugin(pathfinder);

  // ── Spawned ──────────────────────────────────────────────────────────────
  bot.once('spawn', () => {
    reconnectDelay = 3000; // reset backoff on success
    console.log(`[BOT] Spawned as ${username} (${bot.version})`);
    writeStatus({ connected: true, username, status: 'online',
      messages_sent: messagesSent, position: getPos(),
      mc_version: bot.version });
    setTimeout(() => {
      startMovement();
      startChatting();
    }, 4000);
  });

  // ── Chat ─────────────────────────────────────────────────────────────────
  bot.on('chat', (sender, msg) => {
    if (sender === username) return;
    const lc = msg.toLowerCase();
    if (lc.includes('hello') || lc.includes('hi ') || lc.includes('hey')) {
      setTimeout(() => safechat(`Hey ${sender}!`), 1200);
    } else if (lc.includes('bot') || lc.includes(username.toLowerCase())) {
      setTimeout(() => safechat("I'm here!"), 900);
    }
  });

  // ── Kicked ───────────────────────────────────────────────────────────────
  bot.on('kicked', reason => {
    const r = typeof reason === 'string' ? reason : JSON.stringify(reason);
    console.log(`[BOT] Kicked: ${r}`);
    cleanup();
    const isNameBan = r.includes('ban') || r.includes('whitelist') ||
                      r.includes('username') || r.includes('name');
    scheduleReconnect(username, isNameBan); // immediate username swap on name-ban
  });

  // ── Error ─────────────────────────────────────────────────────────────────
  bot.on('error', err => {
    console.error('[BOT] Error:', err.message);
    // If server is offline (Aternos sleeping), wait longer
    const isOffline = err.message.includes('ECONNREFUSED') ||
                      err.message.includes('ETIMEDOUT') ||
                      err.message.includes('ENOTFOUND');
    if (isOffline) reconnectDelay = MAX_DELAY;
    cleanup();
    scheduleReconnect(username);
  });

  // ── End ───────────────────────────────────────────────────────────────────
  bot.on('end', reason => {
    console.log(`[BOT] Disconnected: ${reason}`);
    cleanup();
    scheduleReconnect(username);
  });

  // ── Health ────────────────────────────────────────────────────────────────
  bot.on('health', () => {
    if (bot.health <= 3) {
      const food = bot.inventory.items().find(i =>
        ['bread','apple','cooked','golden','carrot','beef','chicken'].some(f => i.name.includes(f))
      );
      if (food) bot.equip(food, 'hand').catch(() => {});
    }
    writeStatus({ connected: true, username, status: 'online',
      messages_sent: messagesSent, position: getPos(),
      health: Math.round(bot.health), food: Math.round(bot.food),
      mc_version: bot.version });
  });

  // ── Death ─────────────────────────────────────────────────────────────────
  bot.on('death', () => {
    console.log('[BOT] Died, respawning...');
    setTimeout(() => bot && bot.respawn(), 500);
  });
}

// ─── Periodic status ping ────────────────────────────────────────────────────
setInterval(() => {
  if (bot && bot.entity) {
    writeStatus({ connected: true, username: bot.username, status: 'online',
      messages_sent: messagesSent, position: getPos(),
      health: bot.health ? Math.round(bot.health) : null,
      food:   bot.food   ? Math.round(bot.food)   : null,
      mc_version: bot.version });
  }
}, 8000);

// ─── Self-ping keep-alive (ping Flask /ping every 4 min) ─────────────────────
if (SELF_PING_URL) {
  setInterval(() => {
    try {
      const url = new URL(SELF_PING_URL);
      const req = http.request({ host: url.hostname, port: url.port || 80,
        path: '/ping', method: 'GET' }, () => {});
      req.on('error', () => {});
      req.end();
    } catch (_) {}
  }, 4 * 60 * 1000);
  console.log(`[BOT] Keep-alive pinging ${SELF_PING_URL}/ping every 4 min`);
}

// ─── Graceful shutdown ────────────────────────────────────────────────────────
process.on('SIGINT', () => {
  console.log('[BOT] Shutting down...');
  isRunning = false;
  cleanup();
  process.exit(0);
});

process.on('uncaughtException', err => {
  console.error('[BOT] Uncaught exception:', err.message);
  cleanup();
  if (isRunning) scheduleReconnect(null);
});

process.on('unhandledRejection', reason => {
  console.error('[BOT] Unhandled rejection:', reason);
});

// ─── Start ────────────────────────────────────────────────────────────────────
console.log('[BOT] Private Java SMP Bot starting (Node', process.version, ')');
createBot();
