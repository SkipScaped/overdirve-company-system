const mineflayer = require('mineflayer');
const { pathfinder, Movements, goals } = require('mineflayer-pathfinder');
const fs = require('fs');
const path = require('path');

// ─── Config ───────────────────────────────────────────────────────────────────
const SERVER_HOST = 'private-java-smp.aternos.me';
const SERVER_PORT = 40115;
const MC_VERSION  = '1.21.5';
const STATUS_FILE = path.join(__dirname, 'status.json');

// ─── Username Pool (algorithmic generation) ───────────────────────────────────
const ADJECTIVES = [
  'Shadow','Blazing','Crystal','Iron','Diamond','Golden','Cobalt','Emerald',
  'Mystic','Nether','Ender','Storm','Silent','Swift','Bold','Mighty','Frost',
  'Lava','Azure','Crimson','Obsidian','Coral','Lunar','Solar','Astral',
  'Thunder','Ghast','Creeper','Wither','Phantom','Zombie','Piglin','Blaze'
];
const NOUNS = [
  'Knight','Warrior','Dragon','Miner','Builder','Crafter','Archer','Wizard',
  'Hero','Legend','Titan','Phantom','Ghost','Ranger','Scout','Sentinel',
  'Slayer','Hunter','Guard','Keeper','Wanderer','Pioneer','Raider','Seeker',
  'Overlord','Champion','Pilgrim','Stalker','Warden','Protector','Seeker'
];
const CHAT_MESSAGES = [
  'Mining away!', 'Beautiful server!', 'Anyone online?', 'GG everyone!',
  'Love this SMP!', 'Building something epic', 'Exploring the world!',
  'Diamonds found!', 'This place is amazing', 'Shoutout to SkipScaped!',
  'Greetings fellow miners!', 'What are you all building?', 'Nice spawn!',
  'This server rocks!', 'Happy mining everyone!', 'Adventuring around!',
  'Found a stronghold!', 'Making progress on my base', 'The nether is spicy!'
];

let usedUsernames = new Set();
let currentUsernameIndex = 0;
let reconnectDelay = 3000;
const MAX_RECONNECT_DELAY = 60000;

function generateUsername(index) {
  const adj  = ADJECTIVES[index % ADJECTIVES.length];
  const noun = NOUNS[Math.floor(index / ADJECTIVES.length) % NOUNS.length];
  const num  = (index % 999) + 1;
  const variants = [
    `${adj}${noun}`,
    `${adj}${noun}${num}`,
    `${noun}${num}`,
    `${adj}${num}`,
    `${adj}_${noun}`,
    `${noun}_${adj}`,
    `_${adj}${noun}_`,
    `${adj}${noun}XD`
  ];
  return variants[index % variants.length].substring(0, 16);
}

function getNextUsername() {
  let name;
  let tries = 0;
  do {
    name = generateUsername(currentUsernameIndex++);
    tries++;
  } while (usedUsernames.has(name) && tries < 200);
  usedUsernames.add(name);
  // Reset pool after 5000 attempts
  if (currentUsernameIndex > 5000) {
    currentUsernameIndex = 0;
    usedUsernames.clear();
  }
  return name;
}

// ─── Status file ──────────────────────────────────────────────────────────────
function writeStatus(data) {
  try {
    fs.writeFileSync(STATUS_FILE, JSON.stringify({ ...data, updated: new Date().toISOString() }, null, 2));
  } catch (_) {}
}

writeStatus({ connected: false, username: null, status: 'starting', messages_sent: 0, position: null });

// ─── Bot logic ────────────────────────────────────────────────────────────────
let bot = null;
let messagesSent = 0;
let chatInterval = null;
let moveInterval = null;
let isRunning = true;

function createBot() {
  if (!isRunning) return;

  const username = getNextUsername();
  console.log(`[BOT] Connecting as ${username} to ${SERVER_HOST}:${SERVER_PORT}`);

  writeStatus({ connected: false, username, status: 'connecting', messages_sent: messagesSent, position: null });

  try {
    bot = mineflayer.createBot({
      host: SERVER_HOST,
      port: SERVER_PORT,
      username,
      version: MC_VERSION,
      auth: 'offline',
      hideErrors: false,
      checkTimeoutInterval: 30000,
      connectTimeout: 20000
    });
  } catch (err) {
    console.error('[BOT] Failed to create bot:', err.message);
    scheduleReconnect(username);
    return;
  }

  bot.loadPlugin(pathfinder);

  // ── Spawned ──────────────────────────────────────────────────────────────
  bot.once('spawn', () => {
    reconnectDelay = 3000;
    console.log(`[BOT] Spawned as ${username}`);
    writeStatus({ connected: true, username, status: 'online', messages_sent: messagesSent, position: getPos() });

    // Give server 3 seconds to settle before starting activity
    setTimeout(() => {
      startMovement();
      startChatting();
    }, 3000);
  });

  // ── Chat received ─────────────────────────────────────────────────────────
  bot.on('chat', (sender, msg) => {
    if (sender === username) return;
    // Respond to greetings
    const lower = msg.toLowerCase();
    if (lower.includes('hello') || lower.includes('hi') || lower.includes('hey')) {
      setTimeout(() => safechat(`Hey ${sender}!`), 1500);
    } else if (lower.includes('bot') || lower.includes(username.toLowerCase())) {
      setTimeout(() => safechat('Yep, I\'m here!'), 1000);
    }
  });

  // ── Kicked ────────────────────────────────────────────────────────────────
  bot.on('kicked', (reason) => {
    console.log(`[BOT] Kicked: ${reason}`);
    cleanup();
    // If kicked for auth/name reasons, skip this username and try a new one immediately
    if (reason && (reason.includes('banned') || reason.includes('whitelist') ||
        reason.includes('name') || reason.includes('username'))) {
      console.log('[BOT] Username rejected, switching immediately...');
      reconnectDelay = 1000;
    }
    scheduleReconnect(username);
  });

  // ── Error ─────────────────────────────────────────────────────────────────
  bot.on('error', (err) => {
    console.error('[BOT] Error:', err.message);
    cleanup();
    scheduleReconnect(username);
  });

  // ── End ───────────────────────────────────────────────────────────────────
  bot.on('end', (reason) => {
    console.log(`[BOT] Disconnected: ${reason}`);
    cleanup();
    scheduleReconnect(username);
  });

  // ── Health monitor ────────────────────────────────────────────────────────
  bot.on('health', () => {
    if (bot.health <= 2) {
      console.log('[BOT] Low health, eating or retreating...');
      const food = bot.inventory.items().find(i => i.name.includes('bread') ||
        i.name.includes('apple') || i.name.includes('cooked') || i.name.includes('golden'));
      if (food) bot.equip(food, 'hand').catch(() => {});
    }
    writeStatus({ connected: true, username, status: 'online', messages_sent: messagesSent,
      position: getPos(), health: bot.health, food: bot.food });
  });

  // ── Death ─────────────────────────────────────────────────────────────────
  bot.on('death', () => {
    console.log('[BOT] Died, respawning...');
    bot.respawn();
  });
}

// ─── Movement ─────────────────────────────────────────────────────────────────
function startMovement() {
  if (!bot || moveInterval) return;
  const mcData = require('minecraft-data')(bot.version);
  const movements = new Movements(bot, mcData);
  movements.allowSprinting = true;
  movements.canDig = false;
  bot.pathfinder.setMovements(movements);

  moveInterval = setInterval(() => {
    if (!bot || !bot.entity) return;
    try {
      const pos = bot.entity.position;
      const dx = (Math.random() - 0.5) * 20;
      const dz = (Math.random() - 0.5) * 20;
      const target = new goals.GoalXZ(Math.floor(pos.x + dx), Math.floor(pos.z + dz));
      bot.pathfinder.setGoal(target);
    } catch (_) {}
  }, 8000 + Math.random() * 5000);
}

// ─── Chatting ─────────────────────────────────────────────────────────────────
function startChatting() {
  if (!bot || chatInterval) return;
  chatInterval = setInterval(() => {
    if (!bot) return;
    const msg = CHAT_MESSAGES[Math.floor(Math.random() * CHAT_MESSAGES.length)];
    safechat(msg);
  }, 45000 + Math.random() * 30000);
}

function safechat(msg) {
  if (!bot) return;
  try {
    bot.chat(msg);
    messagesSent++;
  } catch (_) {}
}

function getPos() {
  try {
    const p = bot && bot.entity && bot.entity.position;
    if (!p) return null;
    return { x: Math.floor(p.x), y: Math.floor(p.y), z: Math.floor(p.z) };
  } catch (_) { return null; }
}

// ─── Cleanup ──────────────────────────────────────────────────────────────────
function cleanup() {
  if (chatInterval) { clearInterval(chatInterval); chatInterval = null; }
  if (moveInterval) { clearInterval(moveInterval); moveInterval = null; }
  writeStatus({ connected: false, username: bot && bot.username, status: 'disconnected',
    messages_sent: messagesSent, position: null });
  bot = null;
}

// ─── Reconnect ────────────────────────────────────────────────────────────────
function scheduleReconnect(lastUsername) {
  console.log(`[BOT] Reconnecting in ${reconnectDelay / 1000}s...`);
  writeStatus({ connected: false, username: lastUsername, status: `reconnecting in ${reconnectDelay / 1000}s`,
    messages_sent: messagesSent, position: null });

  setTimeout(() => {
    if (isRunning) createBot();
  }, reconnectDelay);

  reconnectDelay = Math.min(reconnectDelay * 1.5, MAX_RECONNECT_DELAY);
}

// ─── Keep-alive status ping ───────────────────────────────────────────────────
setInterval(() => {
  if (bot && bot.entity) {
    writeStatus({ connected: true, username: bot.username, status: 'online',
      messages_sent: messagesSent, position: getPos(),
      health: bot.health, food: bot.food });
  }
}, 10000);

// ─── Graceful shutdown ────────────────────────────────────────────────────────
process.on('SIGINT', () => {
  console.log('[BOT] Shutting down...');
  isRunning = false;
  cleanup();
  process.exit(0);
});

process.on('uncaughtException', (err) => {
  console.error('[BOT] Uncaught exception:', err.message);
  cleanup();
  if (isRunning) scheduleReconnect(null);
});

process.on('unhandledRejection', (reason) => {
  console.error('[BOT] Unhandled rejection:', reason);
});

// ─── Start ────────────────────────────────────────────────────────────────────
console.log('[BOT] Private Java SMP Bot starting...');
createBot();
